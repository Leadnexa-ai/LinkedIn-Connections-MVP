#!/usr/bin/env python3
"""Update the CSV database with recent LinkedIn connection counts."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path


DATABASE_REQUIRED_COLUMNS = {"profile_name", "name", "linkedin_url"}
RESULT_REQUIRED_COLUMNS = {"profile_name", "url", "recent_connections_number"}
UPDATE_COLUMNS = ["last_connections_number", "last_checked_at"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update profiles_database.csv from linkedin_connections.csv."
    )
    parser.add_argument("--database", default="profiles_database.csv", help="CSV database path.")
    parser.add_argument("--results", default="linkedin_connections.csv", help="Scrape results CSV path.")
    return parser.parse_args()


def read_csv(path: Path, required_columns: set[str]) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    with path.open("r", newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = reader.fieldnames or []
        missing_columns = required_columns - set(fieldnames)
        if missing_columns:
            joined_columns = ", ".join(sorted(missing_columns))
            raise ValueError(f"{path} missing required column(s): {joined_columns}")
        rows = [{key: (value or "").strip() for key, value in row.items()} for row in reader]
    return fieldnames, rows


def write_database(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_result_index(result_rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {
        row["profile_name"]: row
        for row in result_rows
        if row.get("profile_name") and row.get("recent_connections_number")
    }


def dedupe_database_rows(
    database_rows: list[dict[str, str]],
    result_index: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    deduped_rows: list[dict[str, str]] = []
    seen_profile_names: set[str] = set()

    for row in database_rows:
        profile_name = row.get("profile_name", "")
        if not profile_name or profile_name in seen_profile_names:
            continue
        seen_profile_names.add(profile_name)
        deduped_rows.append(row)

    for profile_name, result_row in result_index.items():
        if profile_name in seen_profile_names:
            continue
        deduped_rows.append(
            {
                "profile_name": profile_name,
                "name": (result_row.get("name") or "").strip(),
                "linkedin_url": (result_row.get("url") or "").strip(),
                "last_connections_number": "",
                "last_checked_at": "",
            }
        )
        seen_profile_names.add(profile_name)

    return deduped_rows


def update_rows(
    database_rows: list[dict[str, str]],
    result_index: dict[str, dict[str, str]],
    checked_at: str,
) -> int:
    updated_count = 0
    for database_row in database_rows:
        profile_name = database_row.get("profile_name", "")
        result_row = result_index.get(profile_name)
        if not result_row:
            continue

        result_name = (result_row.get("name") or "").strip()
        result_url = (result_row.get("url") or "").strip()
        if result_name:
            database_row["name"] = result_name
        if result_url:
            database_row["linkedin_url"] = result_url
        database_row["last_connections_number"] = result_row["recent_connections_number"]
        database_row["last_checked_at"] = checked_at
        updated_count += 1

    return updated_count


def main() -> int:
    args = parse_args()
    database_path = Path(args.database)
    results_path = Path(args.results)

    database_fieldnames, database_rows = read_csv(database_path, DATABASE_REQUIRED_COLUMNS)
    _, result_rows = read_csv(results_path, RESULT_REQUIRED_COLUMNS)

    for column in UPDATE_COLUMNS:
        if column not in database_fieldnames:
            database_fieldnames.append(column)
            for row in database_rows:
                row[column] = ""

    result_index = build_result_index(result_rows)
    database_rows = dedupe_database_rows(database_rows, result_index)
    checked_at = datetime.now(timezone.utc).isoformat()
    updated_count = update_rows(database_rows, result_index, checked_at)
    write_database(database_path, database_fieldnames, database_rows)

    print(f"Updated {updated_count} database rows: {database_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
