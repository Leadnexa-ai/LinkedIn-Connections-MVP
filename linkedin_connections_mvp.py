#!/usr/bin/env python3
"""
LinkedIn connection counter helper.

Flow:
1. Selenium opens Chrome with a reusable local profile.
2. You log in manually when the browser appears.
3. The script opens each URL and reads visible "connection" text only.
4. The output CSV is refreshed for the current input list.
5. If original_connections_number is blank, the previous recent value is reused.
"""

from __future__ import annotations

import argparse
import csv
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


INPUT_COLUMNS = [
    "profile_name",
    "url",
    "original_connections_number",
]

CONNECTION_PATTERNS = [
    re.compile(r"(?<!\w)(?:\d{1,3}(?:[,\s]\d{3})+|\d+)\+?\s+connections?\b", re.IGNORECASE),
    re.compile(r"(?<!\w)(?:\d{1,3}(?:[,\s]\d{3})+|\d+)\+?\s*位联系人\b", re.IGNORECASE),
    re.compile(r"(?<!\w)(?:\d{1,3}(?:[,\s]\d{3})+|\d+)\+?\s*个联系人\b", re.IGNORECASE),
    re.compile(r"(?<!\w)(?:\d{1,3}(?:[,\s]\d{3})+|\d+)\+?\s*名联系人\b", re.IGNORECASE),
]

CSV_COLUMNS = [
    "profile_name",
    "name",
    "url",
    "original_connections_number",
    "recent_connections_number",
]

PROFILE_KEY_COLUMNS = ["profile_name", "url"]


@dataclass
class ProfileInput:
    profile_name: str
    url: str
    original_connections_number: str = ""


@dataclass
class CaptureResult:
    profile_name: str
    name: str
    url: str
    original_connections_number: str
    recent_connections_number: str
    status: str
    source: str
    connection_text: str
    page_title: str
    captured_at: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Selenium helper for recording LinkedIn connection counts."
    )
    parser.add_argument(
        "--input",
        default="profiles.csv",
        help="CSV input with profile_name,url,original_connections_number columns.",
    )
    parser.add_argument("--out", default="linkedin_connections.csv", help="CSV output path.")
    parser.add_argument("--xlsx", default="", help="Optional XLSX export path.")
    parser.add_argument(
        "--profile-dir",
        default=".selenium-profile",
        help="Chrome user data directory for keeping login state.",
    )
    parser.add_argument("--start-index", type=int, default=1, help="1-based URL index to start from.")
    parser.add_argument("--page-timeout", type=int, default=12, help="Visible page/body wait timeout seconds.")
    parser.add_argument(
        "--connections-timeout",
        type=int,
        default=5,
        help="Wait timeout for visible connections text seconds.",
    )
    parser.add_argument(
        "--page-load-timeout",
        type=int,
        default=20,
        help="Browser page load timeout seconds.",
    )
    parser.add_argument("--delay", type=float, default=1.5, help="Delay between pages in seconds.")
    parser.add_argument(
        "--driver-path",
        default="",
        help="Optional chromedriver path. Usually not needed with recent Selenium versions.",
    )
    return parser.parse_args()


def clean_url(url: str) -> str:
    value = url.strip()
    if value.startswith("www."):
        return f"https://{value}"
    return value


def load_profiles_from_csv(path: Path) -> list[ProfileInput]:
    if not path.exists():
        return []

    with path.open("r", newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        if not reader.fieldnames:
            return []

        missing_columns = {"profile_name", "url"} - set(reader.fieldnames)
        if missing_columns:
            joined_columns = ", ".join(sorted(missing_columns))
            raise ValueError(f"Input CSV missing required column(s): {joined_columns}")

        profiles = []
        for row in reader:
            url = clean_url(row.get("url", ""))
            if not url:
                continue
            profiles.append(
                ProfileInput(
                    profile_name=(row.get("profile_name") or "").strip(),
                    url=url,
                    original_connections_number=(row.get("original_connections_number") or "").strip(),
                )
            )
        return profiles
def load_profile_inputs(input_path: Path) -> list[ProfileInput]:
    profiles = load_profiles_from_csv(input_path)
    if profiles:
        return profiles
    raise FileNotFoundError(f"Input CSV not found or empty: {input_path}")


def profile_key(profile_name: str, url: str) -> tuple[str, str]:
    return profile_name.strip(), clean_url(url).rstrip("/")


def load_previous_recent_counts(path: Path) -> dict[tuple[str, str], str]:
    if not path.exists() or path.stat().st_size == 0:
        return {}

    previous_counts: dict[tuple[str, str], str] = {}
    with path.open("r", newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        if not reader.fieldnames:
            return previous_counts

        for row in reader:
            url = row.get("url", "")
            if not url:
                continue

            profile_name = row.get("profile_name", "")
            recent_count = row.get("recent_connections_number") or row.get("connection_count") or ""
            recent_count = recent_count.strip()
            if not recent_count:
                continue

            previous_counts[profile_key(profile_name, url)] = recent_count
            previous_counts[profile_key("", url)] = recent_count

    return previous_counts


def fill_original_counts(
    profiles: list[ProfileInput],
    previous_counts: dict[tuple[str, str], str],
) -> list[ProfileInput]:
    filled_profiles: list[ProfileInput] = []
    for profile in profiles:
        original_count = profile.original_connections_number
        if not original_count:
            original_count = previous_counts.get(profile_key(profile.profile_name, profile.url), "")
        if not original_count:
            original_count = previous_counts.get(profile_key("", profile.url), "")

        filled_profiles.append(
            ProfileInput(
                profile_name=profile.profile_name,
                url=profile.url,
                original_connections_number=original_count,
            )
        )
    return filled_profiles


def build_driver(profile_dir: Path, driver_path: str, page_load_timeout: int) -> webdriver.Chrome:
    options = Options()
    options.add_argument(f"--user-data-dir={profile_dir.resolve()}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    if driver_path:
        driver = webdriver.Chrome(service=Service(driver_path), options=options)
    else:
        driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(page_load_timeout)
    return driver


def wait_for_page(driver: webdriver.Chrome, timeout: int) -> None:
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except TimeoutException:
        print("  页面加载等待超时，但会继续尝试读取当前可见文本。")


def wait_for_profile_text(driver: webdriver.Chrome, timeout: int) -> None:
    try:
        WebDriverWait(driver, timeout).until(
            lambda current_driver: any(
                keyword in visible_body_text(current_driver).lower()
                for keyword in ("connections", "位联系人", "个联系人", "名联系人")
            )
        )
    except TimeoutException:
        print("  等待 connections 文本超时，将读取当前页面文本。")


def visible_body_text(driver: webdriver.Chrome) -> str:
    try:
        return driver.find_element(By.TAG_NAME, "body").text
    except WebDriverException:
        return ""


def normalized_text_variants(body_text: str) -> list[str]:
    lines = []
    seen = set()
    normalized_body = " ".join(body_text.split())
    if normalized_body:
        lines.append(normalized_body)
        seen.add(normalized_body)

    for raw_line in body_text.splitlines():
        line = " ".join(raw_line.split())
        if len(line) < 3 or line in seen:
            continue
        seen.add(line)
        lines.append(line)
    return lines


def find_connection_text(text_variants: list[str]) -> str:
    candidates: list[str] = []
    seen = set()
    for text in text_variants:
        for pattern in CONNECTION_PATTERNS:
            for match in pattern.findall(text):
                candidate = " ".join(match.split())
                if candidate not in seen:
                    seen.add(candidate)
                    candidates.append(candidate)

    if not candidates:
        return ""

    if len(candidates) > 1:
        print(f"  找到 {len(candidates)} 个 connection 候选，自动使用第 1 个：{candidates[0]}")
    else:
        print(f"  找到 connection：{candidates[0]}")
    return candidates[0]


def normalize_count(text: str) -> str:
    match = re.search(r"\d[\d,.\s]*\+?", text)
    if not match:
        return ""
    return re.sub(r"\s+", "", match.group(0))


def find_profile_name(driver: webdriver.Chrome, page_title: str) -> str:
    try:
        heading = driver.find_element(By.TAG_NAME, "h1").text.strip()
        if heading:
            return " ".join(heading.split())
    except WebDriverException:
        pass

    title_name = page_title.split("|", 1)[0].strip()
    if title_name and title_name.lower() not in {"linkedin", "sign up", "sign in"}:
        return title_name
    return ""


def reset_csv(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS)
        writer.writeheader()


def append_csv(path: Path, result: CaptureResult) -> None:
    with path.open("a", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS)
        writer.writerow({column: getattr(result, column) for column in CSV_COLUMNS})


def export_xlsx(csv_path: Path, xlsx_path: Path) -> None:
    try:
        from openpyxl import Workbook
    except ImportError:
        print("未安装 openpyxl，跳过 XLSX 导出。可以运行：pip install openpyxl")
        return

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "connections"

    with csv_path.open("r", newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            sheet.append(row)

    for column_cells in sheet.columns:
        max_length = max(len(str(cell.value or "")) for cell in column_cells)
        sheet.column_dimensions[column_cells[0].column_letter].width = min(max_length + 2, 80)

    workbook.save(xlsx_path)


def capture_one(
    driver: webdriver.Chrome,
    profile: ProfileInput,
    page_timeout: int,
    connections_timeout: int,
) -> CaptureResult:
    try:
        driver.get(profile.url)
    except Exception as error:
        try:
            driver.execute_script("window.stop();")
        except Exception:
            pass
        raise RuntimeError(f"打开页面失败：{error}") from error

    wait_for_page(driver, page_timeout)
    wait_for_profile_text(driver, connections_timeout)
    time.sleep(0.5)

    page_title = driver.title or ""
    name = find_profile_name(driver, page_title)
    body_text = visible_body_text(driver)
    text_variants = normalized_text_variants(body_text)
    connection_text = find_connection_text(text_variants)
    status = "ok" if connection_text else "not_found"
    source = "auto_visible_text" if connection_text else "no_connection_text"

    if not connection_text:
        print("  当前页面没有找到 connections 文本，已记录为 not_found。")

    return CaptureResult(
        profile_name=profile.profile_name,
        name=name,
        url=profile.url,
        original_connections_number=profile.original_connections_number,
        recent_connections_number=normalize_count(connection_text),
        status=status,
        source=source,
        connection_text=connection_text,
        page_title=page_title,
        captured_at=datetime.now(timezone.utc).isoformat(),
    )


def login_checkpoint(driver: webdriver.Chrome, first_url: str, page_timeout: int) -> None:
    print("正在打开第一个 LinkedIn URL。请在浏览器里手动完成 Google/LinkedIn 登录。")
    driver.get(first_url)
    wait_for_page(driver, page_timeout)
    input("登录完成并且页面可见后，回到终端按回车继续：")


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    out_path = Path(args.out)
    profile_dir = Path(args.profile_dir)

    try:
        profiles = load_profile_inputs(input_path)
    except (FileNotFoundError, ValueError) as error:
        print(error)
        return 1

    if not profiles:
        print(f"输入为空：{input_path}")
        return 1

    previous_counts = load_previous_recent_counts(out_path)
    profiles = fill_original_counts(profiles, previous_counts)
    start_index = max(args.start_index, 1)
    profiles_to_process = profiles[start_index - 1 :]
    reset_csv(out_path)

    print(f"读取到 {len(profiles)} 个 profile，将从第 {start_index} 个开始。")
    print(f"CSV 会按本次输入刷新写入：{out_path}")

    driver = build_driver(profile_dir, args.driver_path, args.page_load_timeout)
    try:
        login_checkpoint(driver, profiles_to_process[0].url, args.page_timeout)

        for offset, profile in enumerate(profiles_to_process, start=start_index):
            print("")
            label = f"{profile.profile_name} / " if profile.profile_name else ""
            print(f"[{offset}/{len(profiles)}] 打开：{label}{profile.url}")
            try:
                result = capture_one(driver, profile, args.page_timeout, args.connections_timeout)
            except KeyboardInterrupt:
                print("收到退出指令，停止处理。")
                break
            except WebDriverException as error:
                print(f"  Selenium 错误：{error}")
                result = CaptureResult(
                    profile_name=profile.profile_name,
                    name="",
                    url=profile.url,
                    original_connections_number=profile.original_connections_number,
                    recent_connections_number="",
                    status="error",
                    source="selenium_error",
                    connection_text="",
                    page_title="",
                    captured_at=datetime.now(timezone.utc).isoformat(),
                )
            except Exception as error:
                print(f"  页面处理失败：{error}")
                result = CaptureResult(
                    profile_name=profile.profile_name,
                    name="",
                    url=profile.url,
                    original_connections_number=profile.original_connections_number,
                    recent_connections_number="",
                    status="error",
                    source="page_error",
                    connection_text="",
                    page_title="",
                    captured_at=datetime.now(timezone.utc).isoformat(),
                )

            append_csv(out_path, result)
            print(f"  已写入：{result.status} / {result.name or '无姓名'} / {result.recent_connections_number or '无'}")
            time.sleep(args.delay)
    finally:
        driver.quit()

    if args.xlsx:
        export_xlsx(out_path, Path(args.xlsx))
        print(f"XLSX 导出完成：{args.xlsx}")

    print("完成。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n已停止。")
        raise SystemExit(130)
