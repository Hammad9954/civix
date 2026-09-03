from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image
import imagehash

from utils.location import haversine_distance


def calculate_image_hash(image_path: str | Path):
    """
    Generate perceptual hash for an image.
    """

    image = Image.open(image_path)

    return imagehash.phash(image)


def image_similarity(
    image1_path: str | Path,
    image2_path: str | Path,
) -> float:
    """
    Compare two images using perceptual hashing.

    Returns:
        Similarity from 0.0 to 1.0.
    """

    try:
        hash1 = calculate_image_hash(image1_path)
        hash2 = calculate_image_hash(image2_path)

        distance = hash1 - hash2

        max_distance = len(hash1.hash) ** 2

        similarity = 1 - (distance / max_distance)

        return max(0.0, min(1.0, similarity))

    except Exception:
        return 0.0


def find_duplicate_reports(
    new_report: dict[str, Any],
    existing_reports: list[dict[str, Any]],
    location_radius_m: float = 100.0,
    similarity_threshold: float = 0.65,
) -> list[dict[str, Any]]:

    matches = []

    new_location = new_report.get("location", {})

    new_lat = new_location.get("latitude")
    new_lon = new_location.get("longitude")

    new_issue = (
        new_report
        .get("issue", {})
        .get("type")
    )

    new_image = (
        new_report
        .get("image", {})
        .get("path")
    )

    if new_lat is None or new_lon is None:
        return []

    for report in existing_reports:

        # Don't compare against itself
        if report.get("id") == new_report.get("id"):
            continue

        # Compare issue category
        existing_issue = (
            report
            .get("issue", {})
            .get("type")
        )

        if existing_issue != new_issue:
            continue

        location = report.get("location", {})

        old_lat = location.get("latitude")
        old_lon = location.get("longitude")

        if old_lat is None or old_lon is None:
            continue

        distance = haversine_distance(
            float(new_lat),
            float(new_lon),
            float(old_lat),
            float(old_lon),
        )

        if distance > location_radius_m:
            continue

        old_image = (
            report
            .get("image", {})
            .get("path")
        )

        similarity = 0.0

        if new_image and old_image:
            if Path(new_image).exists() and Path(old_image).exists():
                similarity = image_similarity(
                    new_image,
                    old_image,
                )

        # Combined duplicate score
        location_score = max(
            0.0,
            1.0 - (distance / location_radius_m),
        )

        duplicate_score = (
            0.6 * similarity
            + 0.4 * location_score
        )

        if duplicate_score >= similarity_threshold:

            matches.append(
                {
                    "report_id": report.get("id"),
                    "distance_m": round(distance, 1),
                    "image_similarity": round(
                        similarity,
                        3,
                    ),
                    "duplicate_score": round(
                        duplicate_score,
                        3,
                    ),
                }
            )

    matches.sort(
        key=lambda x: x["duplicate_score"],
        reverse=True,
    )

    return matches
    