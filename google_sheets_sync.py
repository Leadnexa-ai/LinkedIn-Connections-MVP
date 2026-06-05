#!/usr/bin/env python3
"""Helpers for reading and writing the Google Sheet database."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import gspread
from google.oauth2.service_account import Credentials


SHEETS_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

PROFILE_HEADERS = [
    "profile_name",
    "name",
    "linkedin_url",
    "last_connections_number",
    "last_checked_at",
    "active",
]


def extract_spreadsheet_id(sheet_url_or_id: str) -> str:
    value = sheet_url_or_id.strip()
    if "/spreadsheets/d/" not in value:
        return value
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", value)
    if not match:
        raise ValueError("Could not extract spreadsheet id from URL.")
    return match.group(1)


def load_gspread_client(credentials_path: Path) -> gspread.Client:
    credentials = Credentials.from_service_account_file(str(credentials_path), scopes=SHEETS_SCOPES)
    return gspread.authorize(credentials)


def open_worksheet(
    credentials_path: Path,
    spreadsheet_id_or_url: str,
    worksheet_title: str,
) -> gspread.Worksheet:
    client = load_gspread_client(credentials_path)
    spreadsheet_id = extract_spreadsheet_id(spreadsheet_id_or_url)
    spreadsheet = client.open_by_key(spreadsheet_id)
    return spreadsheet.worksheet(worksheet_title)


def read_sheet_rows(worksheet: gspread.Worksheet) -> list[dict[str, str]]:
    rows = worksheet.get_all_records(default_blank="", head=1)
    cleaned_rows: list[dict[str, str]] = []
    for row in rows:
        cleaned_rows.append({str(key).strip(): str(value).strip() for key, value in row.items()})
    return cleaned_rows


def ensure_headers(worksheet: gspread.Worksheet, required_headers: list[str]) -> None:
    headers = worksheet.row_values(1)
    if not headers:
        worksheet.update("A1", [required_headers])
        return

    missing_headers = [header for header in required_headers if header not in headers]
    if missing_headers:
        raise ValueError(f"Worksheet missing required columns: {', '.join(missing_headers)}")


def active_value_is_true(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized in {"true", "1", "yes", "y", "active"}


def update_sheet_rows(
    worksheet: gspread.Worksheet,
    rows: list[dict[str, Any]],
    match_key: str = "profile_name",
) -> int:
    ensure_headers(worksheet, PROFILE_HEADERS)
    existing_values = worksheet.get_all_values()
    headers = existing_values[0]
    row_index_by_profile_name: dict[str, int] = {}

    for row_index, row_values in enumerate(existing_values[1:], start=2):
        if not row_values:
            continue
        value_map = {
            headers[column_index]: row_values[column_index] if column_index < len(row_values) else ""
            for column_index in range(len(headers))
        }
        profile_name = value_map.get(match_key, "").strip()
        if profile_name:
            row_index_by_profile_name[profile_name] = row_index

    updated_count = 0
    append_rows: list[list[str]] = []

    for row in rows:
        profile_name = str(row.get(match_key, "")).strip()
        if not profile_name:
            continue

        output_values = [str(row.get(header, "")).strip() for header in headers]
        if profile_name in row_index_by_profile_name:
            worksheet.update(f"A{row_index_by_profile_name[profile_name]}", [output_values])
            updated_count += 1
        else:
            append_rows.append(output_values)
            updated_count += 1

    if append_rows:
        worksheet.append_rows(append_rows, value_input_option="USER_ENTERED")

    return updated_count
