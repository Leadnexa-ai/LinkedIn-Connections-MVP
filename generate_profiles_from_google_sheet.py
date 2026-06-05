#!/usr/bin/env python3
"""Generate profiles.csv from a Google Sheet database."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from google_sheets_sync import (
    PROFILE_HEADERS,
    active_value_is_true,
    ensure_headers,
    open_worksheet,
    read_sheet_rows,
)


OUTPUT_COLUMNS = ["profile_name", "url", "original_connections_number"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate profiles.csv from a Google Sheet database."
    )
    parser.add_argument("--credentials", default="google_service_account.json", help="Service account JSON path.")
    parser.add_argument("--sheet", required=True, help="Google Sheet URL or spreadsheet id.")
    parser.add_argument("--worksheet", default="Sheet1", help="Worksheet/tab title.")
    parser.add_argument("--out", default="profiles.csv", help="Generated profiles.csv path.")
    return parser.parse_args()


def write_profiles(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    worksheet = open_worksheet(Path(args.credentials), args.sheet, args.worksheet)
    ensure_headers(worksheet, PROFILE_HEADERS)
    rows = read_sheet_rows(worksheet)

    output_rows: list[dict[str, str]] = []
    total_rows = 0
    active_rows = 0
    skipped_rows = 0

    for row in rows:
        profile_name = row.get("profile_name", "").strip()
        linkedin_url = row.get("linkedin_url", "").strip()
        if not profile_name:
            continue
        total_rows += 1

        active_value = row.get("active", "").strip()
        if active_value and not active_value_is_true(active_value):
            skipped_rows += 1
            continue

        if not linkedin_url:
            skipped_rows += 1
            continue

        active_rows += 1
        output_rows.append(
            {
                "profile_name": profile_name,
                "url": linkedin_url,
                "original_connections_number": row.get("last_connections_number", "").strip(),
            }
        )

    write_profiles(Path(args.out), output_rows)
    print(f"Sheet rows: {total_rows}")
    print(f"Active rows written: {active_rows}")
    print(f"Skipped rows: {skipped_rows}")
    print(f"Output rows: {len(output_rows)} ({args.out})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
