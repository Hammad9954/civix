from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def calculate_priority(
    report: dict[str, Any],
    duplicate_count: int = 0,
    near_school: bool = False,
    near_hospital: bool = False,
    high_traffic: bool = False,
) -> dict[str, Any]:

    issue_type = (
        report
        .get("issue", {})
        .get("type", "Other")
    )

    # ------------------------------------------------
    # Base severity
    # ------------------------------------------------

    severity_map = {
        "Pothole": 70,
        "Road Damage": 65,
        "Overflowing Garbage": 55,
        "Damaged Streetlight": 60,
        "Water Leakage": 75,
        "Other": 40,
    }

    severity = severity_map.get(
        issue_type,
        40,
    )

    # ------------------------------------------------
    # Duplicate reports
    # ------------------------------------------------

    duplicate_score = min(
        duplicate_count * 3,
        15,
    )

    # ------------------------------------------------
    # Age
    # ------------------------------------------------

    age_score = 0

    created_at = report.get("created_at")

    if created_at:

        try:

            created = datetime.fromisoformat(
                created_at.replace(
                    "Z",
                    "+00:00",
                )
            )

            now = datetime.now(timezone.utc)

            age_days = (
                now - created
            ).total_seconds() / 86400

            age_score = min(
                int(age_days * 2),
                10,
            )

        except Exception:
            age_score = 0

    # ------------------------------------------------
    # Important locations
    # ------------------------------------------------

    school_score = 10 if near_school else 0

    hospital_score = 10 if near_hospital else 0

    traffic_score = 10 if high_traffic else 0

    # ------------------------------------------------
    # Final score
    # ------------------------------------------------

    raw_score = (
        severity * 0.45
        + duplicate_score
        + age_score
        + school_score
        + hospital_score
        + traffic_score
    )

    score = max(
        0,
        min(
            100,
            round(raw_score),
        ),
    )

    # ------------------------------------------------
    # Priority level
    # ------------------------------------------------

    if score >= 75:
        level = "CRITICAL"

    elif score >= 50:
        level = "HIGH"

    elif score >= 25:
        level = "MEDIUM"

    else:
        level = "LOW"

    return {
        "score": score,
        "level": level,
        "factors": {
            "base_severity": severity,
            "duplicate_reports": duplicate_count,
            "duplicate_score": duplicate_score,
            "age_score": age_score,
            "near_school": near_school,
            "near_hospital": near_hospital,
            "high_traffic": high_traffic,
        },
    }