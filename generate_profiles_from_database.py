#!/usr/bin/env python3
"""Generate profiles.csv from a CSV database and a folder profile list."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


DATABASE_REQUIRED_COLUMNS = {"profile_name", "name", "linkedin_url"}
FOLDER_REQUIRED_COLUMNS = {"profile_name"}
OUTPUT_COLUMNS = ["profile_name", "url", "original_connections_number"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate profiles.csv from profiles_database.csv and folder_profiles.csv."
    )
    parser.add_argument("--database", default="profiles_database.csv", help="CSV database path.")
    parser.add_argument("--folder", default="folder_profiles.csv", help="Folder profile list CSV path.")
    parser.add_argument("--out", default="profiles.csv", help="Generated profiles.csv path.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if folder contains a profile_name that is missing from the database.",
    )
    return parser.parse_args()


def read_csv_rows(path: Path, required_columns: set[str]) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    with path.open("r", newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        if not reader.fieldnames:
            return []

        missing_columns = required_columns - set(reader.fieldnames)
        if missing_columns:
            joined_columns = ", ".join(sorted(missing_columns))
            raise ValueError(f"{path} missing required column(s): {joined_columns}")

        return [{key: (value or "").strip() for key, value in row.items()} for row in reader]


def write_profiles(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def build_profiles(
    database_rows: list[dict[str, str]],
    folder_rows: list[dict[str, str]],
    strict: bool,
) -> tuple[list[dict[str, str]], list[str]]:
    database_by_profile_name = {
        row["profile_name"]: row
        for row in database_rows
        if row.get("profile_name")
    }

    output_rows: list[dict[str, str]] = []
    missing_profile_names: list[str] = []
    seen_profile_names: set[str] = set()

    for folder_row in folder_rows:
        profile_name = folder_row.get("profile_name", "")
        if not profile_name or profile_name in seen_profile_names:
            continue
        seen_profile_names.add(profile_name)

        database_row = database_by_profile_name.get(profile_name)
        if not database_row:
            missing_profile_names.append(profile_name)
            if strict:
                continue
            continue

        linkedin_url = database_row.get("linkedin_url", "")
        if not linkedin_url:
            missing_profile_names.append(profile_name)
            if strict:
                continue
            continue

        output_rows.append(
            {
                "profile_name": profile_name,
                "url": linkedin_url,
                "original_connections_number": database_row.get("last_connections_number", ""),
            }
        )

    return output_rows, missing_profile_names


def main() -> int:
    args = parse_args()
    database_path = Path(args.database)
    folder_path = Path(args.folder)
    out_path = Path(args.out)

    database_rows = read_csv_rows(database_path, DATABASE_REQUIRED_COLUMNS)
    folder_rows = read_csv_rows(folder_path, FOLDER_REQUIRED_COLUMNS)
    output_rows, missing_profile_names = build_profiles(database_rows, folder_rows, args.strict)

    if args.strict and missing_profile_names:
        print("Missing profile_name values:")
        for profile_name in missing_profile_names:
            print(f"  {profile_name}")
        return 1

    write_profiles(out_path, output_rows)
    print(f"Generated {len(output_rows)} profiles: {out_path}")

    if missing_profile_names:
        print("Skipped missing database rows:")
        for profile_name in missing_profile_names:
            print(f"  {profile_name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
