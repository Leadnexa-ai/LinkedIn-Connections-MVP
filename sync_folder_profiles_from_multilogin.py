#!/usr/bin/env python3
"""Fetch Multilogin profiles and write folder profile names to CSV."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from multilogin_env import getenv, load_dotenv, md5_hex, post_json


MULTILOGIN_BASE_URL = "https://api.multilogin.com"
OUTPUT_COLUMNS = ["profile_name"]
FOLDER_ID_KEYS = {
    "folder",
    "folder_id",
    "folderId",
    "group",
    "group_id",
    "groupId",
}
PROFILE_NAME_KEYS = ("name", "profile_name", "profileName", "title")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync folder_profiles.csv from a Multilogin folder."
    )
    parser.add_argument("--env-file", default=".env", help="Path to local .env file.")
    parser.add_argument("--folder-id", default="", help="Override folder id instead of using .env.")
    parser.add_argument("--out", default="folder_profiles.csv", help="Output CSV path.")
    parser.add_argument("--page-size", type=int, default=100, help="Profiles fetched per page.")
    return parser.parse_args()


def signin() -> str:
    api_token = getenv("MULTILOGIN_API_TOKEN")
    if api_token:
        return api_token

    email = getenv("MULTILOGIN_EMAIL")
    password = getenv("MULTILOGIN_PASSWORD")
    if not email or not password:
        raise RuntimeError(
            "Missing Multilogin credentials. Set MULTILOGIN_API_TOKEN or MULTILOGIN_EMAIL and MULTILOGIN_PASSWORD."
        )

    response = post_json(
        f"{MULTILOGIN_BASE_URL}/user/signin",
        {"email": email, "password": md5_hex(password)},
    )
    token = (((response.get("data") or {}).get("token")) or "").strip()
    if not token:
        raise RuntimeError("Multilogin signin succeeded but no token was returned.")
    return token


def profile_search(token: str, limit: int, offset: int) -> dict[str, Any]:
    return post_json(
        f"{MULTILOGIN_BASE_URL}/profile/search",
        {
            "is_removed": False,
            "limit": limit,
            "offset": offset,
            "search_text": "",
            "storage_type": "all",
            "order_by": "created_at",
            "sort": "asc",
        },
        headers={"Authorization": f"Bearer {token}"},
    )


def find_profile_name(profile: dict[str, Any]) -> str:
    for key in PROFILE_NAME_KEYS:
        value = profile.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def object_contains_folder_id(value: Any, folder_id: str) -> bool:
    if isinstance(value, dict):
        for key, nested_value in value.items():
            if key in FOLDER_ID_KEYS and str(nested_value).strip() == folder_id:
                return True
            if object_contains_folder_id(nested_value, folder_id):
                return True
        return False
    if isinstance(value, list):
        return any(object_contains_folder_id(item, folder_id) for item in value)
    return False


def fetch_profiles_in_folder(token: str, folder_id: str, page_size: int) -> list[dict[str, Any]]:
    matched_profiles: list[dict[str, Any]] = []
    offset = 0

    while True:
        response = profile_search(token, page_size, offset)
        data = response.get("data") or {}
        profiles = data.get("profiles") or []
        if not profiles:
            break

        for profile in profiles:
            if isinstance(profile, dict) and object_contains_folder_id(profile, folder_id):
                matched_profiles.append(profile)

        if len(profiles) < page_size:
            break
        offset += page_size

    return matched_profiles


def write_folder_profiles(path: Path, profiles: list[dict[str, Any]]) -> int:
    rows: list[dict[str, str]] = []
    seen_names: set[str] = set()

    for profile in profiles:
        profile_name = find_profile_name(profile)
        if not profile_name or profile_name in seen_names:
            continue
        seen_names.add(profile_name)
        rows.append({"profile_name": profile_name})

    with path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


def main() -> int:
    args = parse_args()
    load_dotenv(Path(args.env_file))
    folder_id = args.folder_id.strip() or getenv("MULTILOGIN_FOLDER_ID")
    if not folder_id:
        raise SystemExit("Missing folder id. Set MULTILOGIN_FOLDER_ID or pass --folder-id.")

    token = signin()
    profiles = fetch_profiles_in_folder(token, folder_id, args.page_size)
    count = write_folder_profiles(Path(args.out), profiles)
    print(f"Wrote {count} folder profiles to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
