#!/usr/bin/env python3
"""Generate profiles.csv from a Supabase database table."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from supabase_sync import active_value_is_true, fetch_profile_rows, get_supabase_settings


OUTPUT_COLUMNS = ["profile_name", "url", "original_connections_number"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate profiles.csv from a Supabase database table."
    )
    parser.add_argument("--env-file", default=".env", help="Optional .env file path.")
    parser.add_argument("--url", default="", help="Supabase project URL override.")
    parser.add_argument("--key", default="", help="Supabase API key override.")
    parser.add_argument("--table", default="", help="Supabase table name override.")
    parser.add_argument("--out", default="profiles.csv", help="Generated profiles.csv path.")
    return parser.parse_args()


def write_profiles(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    base_url, key, table = get_supabase_settings(
        env_file=Path(args.env_file),
        url=args.url,
        key=args.key,
        table=args.table,
    )
    rows = fetch_profile_rows(base_url, key, table)

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
    print(f"Supabase rows: {total_rows}")
    print(f"Active rows written: {active_rows}")
    print(f"Skipped rows: {skipped_rows}")
    print(f"Output rows: {len(output_rows)} ({args.out})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
