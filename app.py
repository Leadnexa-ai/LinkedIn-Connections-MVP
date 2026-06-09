#!/usr/bin/env python3
"""Minimal internal API for the LinkedIn connections workflow."""

from __future__ import annotations

import csv
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent
RUNS_DIR = BASE_DIR / "run_artifacts"
ENV_FILE = BASE_DIR / ".env"
PYTHON_BIN = BASE_DIR / ".venv" / "bin" / "python3"

app = FastAPI(title="LinkedIn Connections Internal API", version="1.0.0")


class RunRequest(BaseModel):
    start_index: int = Field(default=1, ge=1)
    limit: int | None = Field(default=None, ge=1)
    page_timeout: int = Field(default=10, ge=1)
    connections_timeout: int = Field(default=3, ge=1)
    page_load_timeout: int = Field(default=15, ge=1)
    delay: float = Field(default=1.5, ge=0)


def require_api_key(x_api_key: str | None) -> None:
    expected_key = os.getenv("LOCAL_API_KEY", "").strip()
    if not expected_key:
        return
    if x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key.")


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
        value = (row.get("recent_connections_number") or "").strip()
        if value:
            summary["success_count"] += 1
        else:
            summary["not_found_count"] += 1
    return summary


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/run")
def run_workflow(payload: RunRequest, x_api_key: str | None = Header(default=None)) -> dict[str, Any]:
    require_api_key(x_api_key)

    if not PYTHON_BIN.exists():
        raise HTTPException(status_code=500, detail="Virtual environment Python not found at .venv/bin/python3.")
    if not ENV_FILE.exists():
        raise HTTPException(status_code=500, detail="Missing .env file.")

    RUNS_DIR.mkdir(exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    generated_profiles_path = run_dir / "profiles.generated.csv"
    profiles_path = run_dir / "profiles.csv"
    results_path = run_dir / "linkedin_connections.csv"
    xlsx_path = run_dir / "linkedin_connections.xlsx"

    generate_step = run_command(
        [
            str(PYTHON_BIN),
            "generate_profiles_from_supabase.py",
            "--env-file",
            str(ENV_FILE),
            "--out",
            str(generated_profiles_path),
        ]
    )
    if generate_step["returncode"] != 0:
        raise HTTPException(status_code=500, detail={"step": "generate_profiles", **generate_step})

    generated_rows = load_profiles(generated_profiles_path)
    selected_rows = generated_rows[payload.start_index - 1 :]
    if payload.limit is not None:
        selected_rows = selected_rows[: payload.limit]
    if not selected_rows:
        raise HTTPException(status_code=400, detail="No profiles selected for this run.")
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
            str(payload.page_timeout),
            "--connections-timeout",
            str(payload.connections_timeout),
            "--page-load-timeout",
            str(payload.page_load_timeout),
            "--delay",
            str(payload.delay),
        ]
    )
    if capture_step["returncode"] != 0:
        raise HTTPException(status_code=500, detail={"step": "capture", **capture_step})

    update_step = run_command(
        [
            str(PYTHON_BIN),
            "update_supabase_from_results.py",
            "--env-file",
            str(ENV_FILE),
            "--results",
            str(results_path),
        ]
    )
    if update_step["returncode"] != 0:
        raise HTTPException(status_code=500, detail={"step": "update_supabase", **update_step})

    result_rows = read_results(results_path)
    summary = summarize_results(result_rows)
    summary["selected_count"] = len(selected_rows)

    return {
        "status": "success",
        "run_id": run_id,
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
    }
