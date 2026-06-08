#!/usr/bin/env python3
"""Update a Supabase database table from linkedin_connections.csv results."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

from supabase_sync import fetch_profile_rows, get_supabase_settings, insert_profile_row, update_profile_row


RESULT_REQUIRED_COLUMNS = {"profile_name", "name", "url", "recent_connections_number"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update a Supabase table from linkedin_connections.csv."
    )
    parser.add_argument("--env-file", default=".env", help="Optional .env file path.")
    parser.add_argument("--url", default="", help="Supabase project URL override.")
    parser.add_argument("--key", default="", help="Supabase API key override.")
    parser.add_argument("--table", default="", help="Supabase table name override.")
    parser.add_argument("--results", default="linkedin_connections.csv", help="Scrape results CSV path.")
    return parser.parse_args()


def read_results(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    with path.open("r", newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = reader.fieldnames or []
        missing_columns = RESULT_REQUIRED_COLUMNS - set(fieldnames)
        if missing_columns:
            joined_columns = ", ".join(sorted(missing_columns))
            raise ValueError(f"{path} missing required column(s): {joined_columns}")
        return [{key: (value or "").strip() for key, value in row.items()} for row in reader]


def build_payload(
    result_row: dict[str, str],
    current_row: dict[str, str],
    checked_at: str,
) -> dict[str, str]:
    payload: dict[str, str] = {
        "profile_name": result_row.get("profile_name", "").strip(),
        "name": result_row.get("name", "").strip() or current_row.get("name", "").strip(),
        "linkedin_url": result_row.get("url", "").strip() or current_row.get("linkedin_url", "").strip(),
    }
    active_value = current_row.get("active", "").strip()
    if active_value:
        payload["active"] = active_value
    if "last_connections_number" in current_row:
        payload["last_connections_number"] = result_row.get("recent_connections_number", "").strip()
    if "last_checked_at" in current_row:
        payload["last_checked_at"] = checked_at
    return payload


def main() -> int:
    args = parse_args()
    base_url, key, table = get_supabase_settings(
        env_file=Path(args.env_file),
        url=args.url,
        key=args.key,
        table=args.table,
    )
    result_rows = read_results(Path(args.results))
    current_rows = fetch_profile_rows(base_url, key, table)
    current_rows_by_profile_name = {
        row.get("profile_name", "").strip(): row
        for row in current_rows
        if row.get("profile_name", "").strip()
    }

    checked_at = datetime.now(timezone.utc).isoformat()
    updated_count = 0
    inserted_count = 0

    for result_row in result_rows:
        profile_name = result_row.get("profile_name", "").strip()
        recent_connections_number = result_row.get("recent_connections_number", "").strip()
        if not profile_name or not recent_connections_number:
            continue

        current_row = current_rows_by_profile_name.get(profile_name, {})
        payload = build_payload(result_row, current_row, checked_at)
        if current_row:
            update_profile_row(base_url, key, table, profile_name, payload)
            updated_count += 1
        else:
            insert_profile_row(base_url, key, table, payload)
            inserted_count += 1

    print(f"Updated {updated_count} Supabase rows.")
    print(f"Inserted {inserted_count} Supabase rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
