#!/usr/bin/env python3
"""Helpers for reading and writing the Supabase database."""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


REQUIRED_PROFILE_HEADERS = [
    "profile_name",
    "name",
    "linkedin_url",
    "active",
]

OPTIONAL_PROFILE_HEADERS = [
    "last_connections_number",
    "last_checked_at",
]


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def get_supabase_settings(
    env_file: Path | None = None,
    url: str = "",
    key: str = "",
    table: str = "",
) -> tuple[str, str, str]:
    if env_file:
        load_env_file(env_file)

    supabase_url = (url or os.getenv("SUPABASE_URL", "")).strip().rstrip("/")
    supabase_key = (key or os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY") or "").strip()
    supabase_table = (table or os.getenv("SUPABASE_TABLE", "profiles")).strip()

    if not supabase_url:
        raise ValueError("Missing SUPABASE_URL.")
    if not supabase_key:
        raise ValueError("Missing SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY.")
    if not supabase_table:
        raise ValueError("Missing SUPABASE_TABLE.")

    return supabase_url, supabase_key, supabase_table


def active_value_is_true(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized in {"true", "1", "yes", "y", "active"}


def ensure_profile_headers(row: dict[str, Any]) -> None:
    missing_headers = [header for header in REQUIRED_PROFILE_HEADERS if header not in row]
    if missing_headers:
        raise ValueError(f"Supabase table missing required columns: {', '.join(missing_headers)}")


def build_rest_url(base_url: str, table: str, params: dict[str, str] | None = None) -> str:
    encoded_table = urllib.parse.quote(table, safe="")
    url = f"{base_url}/rest/v1/{encoded_table}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    return url


def request_json(
    method: str,
    url: str,
    key: str,
    payload: Any | None = None,
    prefer: str = "",
) -> Any:
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    }
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    if prefer:
        headers["Prefer"] = prefer

    request = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            if not body:
                return None
            return json.loads(body)
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {error.code} for {url}: {body}") from error


def fetch_profile_rows(base_url: str, key: str, table: str) -> list[dict[str, str]]:
    rows = request_json(
        "GET",
        build_rest_url(base_url, table, {"select": "*", "order": "profile_name.asc"}),
        key,
    )
    cleaned_rows: list[dict[str, str]] = []
    for row in rows or []:
        ensure_profile_headers(row)
        cleaned_rows.append({str(header).strip(): str(value or "").strip() for header, value in row.items()})
    return cleaned_rows


def update_profile_row(
    base_url: str,
    key: str,
    table: str,
    profile_name: str,
    payload: dict[str, Any],
) -> None:
    request_json(
        "PATCH",
        build_rest_url(base_url, table, {"profile_name": f"eq.{profile_name}"}),
        key,
        payload=payload,
        prefer="return=minimal",
    )


def insert_profile_row(
    base_url: str,
    key: str,
    table: str,
    payload: dict[str, Any],
) -> None:
    request_json(
        "POST",
        build_rest_url(base_url, table),
        key,
        payload=payload,
        prefer="return=minimal",
    )
