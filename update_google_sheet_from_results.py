#!/usr/bin/env python3
"""Update the Google Sheet database from linkedin_connections.csv results."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

from google_sheets_sync import PROFILE_HEADERS, ensure_headers, open_worksheet, read_sheet_rows, update_sheet_rows


RESULT_REQUIRED_COLUMNS = {"profile_name", "name", "url", "recent_connections_number"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update a Google Sheet database from linkedin_connections.csv."
    )
    parser.add_argument("--credentials", default="google_service_account.json", help="Service account JSON path.")
    parser.add_argument("--sheet", required=True, help="Google Sheet URL or spreadsheet id.")
    parser.add_argument("--worksheet", default="Sheet1", help="Worksheet/tab title.")
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


def build_updates(
    sheet_rows: list[dict[str, str]],
    result_rows: list[dict[str, str]],
    checked_at: str,
) -> list[dict[str, str]]:
    by_profile_name = {
        row.get("profile_name", "").strip(): row
        for row in sheet_rows
        if row.get("profile_name", "").strip()
    }

    updates: list[dict[str, str]] = []
    for result_row in result_rows:
        profile_name = result_row.get("profile_name", "").strip()
        recent_connections_number = result_row.get("recent_connections_number", "").strip()
        if not profile_name or not recent_connections_number:
            continue

        current_row = by_profile_name.get(profile_name, {})
        updates.append(
            {
                "profile_name": profile_name,
                "name": result_row.get("name", "").strip() or current_row.get("name", "").strip(),
                "linkedin_url": result_row.get("url", "").strip() or current_row.get("linkedin_url", "").strip(),
                "last_connections_number": recent_connections_number,
                "last_checked_at": checked_at,
                "active": current_row.get("active", "").strip(),
            }
        )

    return updates


def main() -> int:
    args = parse_args()
    worksheet = open_worksheet(Path(args.credentials), args.sheet, args.worksheet)
    ensure_headers(worksheet, PROFILE_HEADERS)
    sheet_rows = read_sheet_rows(worksheet)
    result_rows = read_results(Path(args.results))

    checked_at = datetime.now(timezone.utc).isoformat()
    updates = build_updates(sheet_rows, result_rows, checked_at)
    updated_count = update_sheet_rows(worksheet, updates)
    print(f"Updated {updated_count} Google Sheet rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
