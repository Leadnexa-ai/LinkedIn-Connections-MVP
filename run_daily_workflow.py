#!/usr/bin/env python3
"""Run the full Supabase -> LinkedIn -> Supabase workflow for cron jobs."""

from __future__ import annotations

import argparse
import csv
import fcntl
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
RUNS_DIR = BASE_DIR / "run_artifacts"
ENV_FILE = BASE_DIR / ".env"
PYTHON_BIN = BASE_DIR / ".venv" / "bin" / "python3"
LOCK_FILE = BASE_DIR / ".daily_workflow.lock"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the daily LinkedIn connections workflow without interactive prompts."
    )
    parser.add_argument("--start-index", type=int, default=1, help="1-based row index to start from.")
    parser.add_argument("--limit", type=int, default=0, help="Optional max profile count. Use 0 for all rows.")
    parser.add_argument("--page-timeout", type=int, default=10, help="Visible page/body wait timeout seconds.")
    parser.add_argument(
        "--connections-timeout",
        type=int,
        default=3,
        help="Wait timeout for visible connections text seconds.",
    )
    parser.add_argument(
        "--page-load-timeout",
        type=int,
        default=15,
        help="Browser page load timeout seconds.",
    )
    parser.add_argument("--delay", type=float, default=1.5, help="Delay between pages in seconds.")
    parser.add_argument("--env-file", default=str(ENV_FILE), help="Local .env file path.")
    parser.add_argument(
        "--run-id",
        default="",
        help="Optional run id override. Defaults to the current UTC timestamp.",
    )
    return parser.parse_args()


def run_command(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def load_profiles(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as csv_file:
        return list(csv.DictReader(csv_file))


def write_profiles(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = ["profile_name", "url", "original_connections_number"]
    with path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_results(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as csv_file:
        return list(csv.DictReader(csv_file))


def summarize_results(rows: list[dict[str, str]]) -> dict[str, int]:
    summary = {
        "processed": len(rows),
        "success_count": 0,
        "not_found_count": 0,
        "error_count": 0,
    }
    for row in rows:
        recent_value = (row.get("recent_connections_number") or "").strip()
        status = (row.get("status") or "").strip().lower()
        if recent_value:
            summary["success_count"] += 1
        elif status == "error":
            summary["error_count"] += 1
        else:
            summary["not_found_count"] += 1
    return summary


def build_run_id(run_id: str) -> str:
    return run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def main() -> int:
    args = parse_args()

    if not PYTHON_BIN.exists():
        print("Virtual environment Python not found at .venv/bin/python3.", file=sys.stderr)
        return 1

    env_file = Path(args.env_file)
    if not env_file.exists():
        print(f"Missing .env file: {env_file}", file=sys.stderr)
        return 1

    RUNS_DIR.mkdir(exist_ok=True)
    run_id = build_run_id(args.run_id)
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    generated_profiles_path = run_dir / "profiles.generated.csv"
    profiles_path = run_dir / "profiles.csv"
    results_path = run_dir / "linkedin_connections.csv"
    xlsx_path = run_dir / "linkedin_connections.xlsx"
    summary_path = run_dir / "summary.json"

    with LOCK_FILE.open("w", encoding="utf-8") as lock_handle:
        try:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("Another daily workflow run is already in progress.", file=sys.stderr)
            return 1

        generate_step = run_command(
            [
                str(PYTHON_BIN),
                "generate_profiles_from_supabase.py",
                "--env-file",
                str(env_file),
                "--out",
                str(generated_profiles_path),
            ]
        )
        if generate_step["returncode"] != 0:
            print(generate_step["stdout"], end="")
            print(generate_step["stderr"], end="", file=sys.stderr)
            return 1

        generated_rows = load_profiles(generated_profiles_path)
        selected_rows = generated_rows[max(args.start_index - 1, 0) :]
        if args.limit > 0:
            selected_rows = selected_rows[: args.limit]

        if not selected_rows:
            print("No profiles selected for this run.", file=sys.stderr)
            return 1

        write_profiles(profiles_path, selected_rows)

        capture_step = run_command(
            [
                str(PYTHON_BIN),
                "linkedin_connections_mvp.py",
                "--input",
                str(profiles_path),
                "--out",
                str(results_path),
                "--xlsx",
                str(xlsx_path),
                "--page-timeout",
                str(args.page_timeout),
                "--connections-timeout",
                str(args.connections_timeout),
                "--page-load-timeout",
                str(args.page_load_timeout),
                "--delay",
                str(args.delay),
                "--skip-login-prompt",
            ]
        )
        if capture_step["returncode"] != 0:
            print(capture_step["stdout"], end="")
            print(capture_step["stderr"], end="", file=sys.stderr)
            return 1

        update_step = run_command(
            [
                str(PYTHON_BIN),
                "update_supabase_from_results.py",
                "--env-file",
                str(env_file),
                "--results",
                str(results_path),
            ]
        )
        if update_step["returncode"] != 0:
            print(update_step["stdout"], end="")
            print(update_step["stderr"], end="", file=sys.stderr)
            return 1

        result_rows = read_results(results_path)
        summary = summarize_results(result_rows)
        summary["selected_count"] = len(selected_rows)
        summary["run_id"] = run_id

        summary_path.write_text(
            json.dumps(
                {
                    "summary": summary,
                    "files": {
                        "profiles": str(profiles_path),
                        "results_csv": str(results_path),
                        "results_xlsx": str(xlsx_path),
                    },
                    "steps": {
                        "generate_profiles": generate_step,
                        "capture": capture_step,
                        "update_supabase": update_step,
                    },
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        print(json.dumps(summary, ensure_ascii=False))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
