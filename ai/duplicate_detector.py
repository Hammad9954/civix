import imagehash
from PIL import Image

from utils.location import haversine_distance


DUPLICATE_RADIUS_METERS = 100
DUPLICATE_THRESHOLD = 0.65


def image_similarity(image1_path, image2_path):

    try:

        image1 = Image.open(image1_path)
        image2 = Image.open(image2_path)

        hash1 = imagehash.phash(image1)
        hash2 = imagehash.phash(image2)

        distance = hash1 - hash2

        max_distance = len(hash1.hash) ** 2

        similarity = 1 - (
            distance / max_distance
        )

        return max(
            0,
            min(1, similarity)
        )

    except Exception:

        return 0.0


def find_duplicate_reports(report, existing_reports):

    matches = []

    location = report.get(
        "location",
        {}
    )

    lat = location.get("latitude")
    lon = location.get("longitude")

    if lat is None or lon is None:
        return matches

    issue_type = (
        report.get("issue", {})
        .get("type")
    )

    image_path = (
        report.get("image", {})
        .get("path")
    )

    if not image_path:
        return matches

    for existing in existing_reports:

        existing_issue = (
            existing.get("issue", {})
            .get("type")
        )

        if existing_issue != issue_type:
            continue

        existing_location = existing.get(
            "location",
            {}
        )

        existing_lat = existing_location.get(
            "latitude"
        )

        existing_lon = existing_location.get(
            "longitude"
        )

        if existing_lat is None or existing_lon is None:
            continue

        distance = haversine_distance(
            lat,
            lon,
            existing_lat,
            existing_lon
        )

        if distance > DUPLICATE_RADIUS_METERS:
            continue

        existing_image = (
            existing.get("image", {})
            .get("path")
        )

        if not existing_image:
            continue

        similarity = image_similarity(
            image_path,
            existing_image
        )

        location_score = max(
            0,
            1 - (
                distance /
                DUPLICATE_RADIUS_METERS
            )
        )

        combined_score = (
            similarity * 0.60
            + location_score * 0.40
        )

        if combined_score >= DUPLICATE_THRESHOLD:

            matches.append({
                "report_id": existing.get("id"),
                "distance_meters": round(
                    distance,
                    2
                ),
                "image_similarity": round(
                    similarity,
                    3
                ),
                "match_score": round(
                    combined_score,
                    3
                )
            })

    return matches