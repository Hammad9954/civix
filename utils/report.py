
"""
CivicAI — Report Creation & Persistence

Creates a structured civic-issue report and saves/loads reports to/from
the local JSON store (``data/reports.json``).

The report schema intentionally includes *placeholder* fields for every
FSD 2 capability (location, priority, duplicates, spam, resolution,
assignment).  V1 only populates the core fields; later versions fill in
the rest without changing the schema.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.constants import REPORTS_FILE, REPORT_ID_PREFIX


# ────────────────────────────────────────────────────────────
# Report Creation
# ────────────────────────────────────────────────────────────
def create_report(
    issue_type: str,
    ai_result: dict,
    confirmed_category: str,
    description: str,
    image_filename: str | None = None,
    image_path: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict:
    """Build a complete civic-issue report dict.

    Parameters
    ----------
    issue_type:
        Top-level issue type (from ``ISSUE_TYPES``).
    ai_result:
        Structured prediction dict from ``CivicIssueClassifier.predict()``.
    confirmed_category:
        The category the citizen actually confirmed.
    description:
        Free-text description entered by the citizen.
    image_filename:
        Original filename of the uploaded image.
    image_path:
        Path where the image was saved on disk (if applicable).

    Returns
    -------
    dict
        The full report structure.
    """
    now = datetime.now(timezone.utc).isoformat()
    report_id = _next_report_id()

    report: dict[str, Any] = {
        "id": report_id,

        # ── Core issue info ──────────────────────────────────
        "issue": {
            "type": issue_type,
            "subcategory": ai_result.get("subcategory") or ai_result.get("category"),
        },

        # ── Image ────────────────────────────────────────────
        "image": {
            "filename": image_filename,
            "path": image_path,
        },

        # ── AI analysis ──────────────────────────────────────
        "ai": {
            "available": ai_result.get("available", False),
            "model": ai_result.get("model"),
            "category": ai_result.get("category"),
            "subcategory": ai_result.get("subcategory"),
            "confidence": ai_result.get("confidence", 0.0),
            "probabilities": ai_result.get("probabilities", {}),
        },

        # ── Citizen input ────────────────────────────────────
        "user": {
            "confirmed_category": confirmed_category,
            "description": description,
        },

        # ── Location (V2+) ──────────────────────────────────
        "location": {
            "latitude": latitude,
            "longitude": longitude,
            "address": None,
        },

        # ── Status ───────────────────────────────────────────
        "status": "reported",

        # ── Priority engine (V2+) ───────────────────────────
        "priority": {
            "score": None,
            "level": None,
            "factors": {},
        },

        # ── Duplicate detection (V2+) ───────────────────────
        "duplicates": {
            "is_duplicate": None,
            "matches": [],
        },

        # ── Spam / trust scoring (V2+) ──────────────────────
        "spam": {
            "score": None,
            "flagged": None,
            "reasons": [],
        },

        # ── Resolution verification (V2+) ───────────────────
        "resolution": {
            "after_image": None,
            "image_similarity": None,
            "ai_verified": None,
            "citizen_confirmed": None,
        },

        # ── Authority assignment (V2+) ──────────────────────
        "assignment": {
            "authority_id": None,
            "department": None,
            "assigned_at": None,
        },

        # ── Timestamps ──────────────────────────────────────
        "created_at": now,
        "updated_at": now,
    }

    return report


# ────────────────────────────────────────────────────────────
# Persistence Helpers
# ────────────────────────────────────────────────────────────

def save_report(report: dict) -> None:
    """Append a report to the local JSON file."""
    reports = load_reports()
    reports.append(report)
    _write_reports(reports)


def load_reports() -> list[dict]:
    """Load all reports from the local JSON file."""
    path = Path(REPORTS_FILE)
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, OSError):
        return []


# ────────────────────────────────────────────────────────────
# Internal Helpers
# ────────────────────────────────────────────────────────────

def _write_reports(reports: list[dict]) -> None:
    """Overwrite the JSON file with the given reports list."""
    path = Path(REPORTS_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(reports, f, indent=2, ensure_ascii=False)


def _next_report_id() -> str:
    """Generate the next sequential report ID (e.g. ``RPT-000042``)."""
    reports = load_reports()
    next_num = len(reports) + 1
    return f"{REPORT_ID_PREFIX}-{next_num:06d}"
