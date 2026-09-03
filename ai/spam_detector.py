def calculate_spam_score(
    report,
    existing_reports
):

    score = 0
    reasons = []

    location = report.get(
        "location",
        {}
    )

    if (
        location.get("latitude") is None
        or
        location.get("longitude") is None
    ):

        score += 20

        reasons.append(
            "Missing GPS location"
        )

    description = (
        report.get(
            "description",
            ""
        ).strip()
    )

    if len(description) < 5:

        score += 10

        reasons.append(
            "Very short description"
        )

    duplicates = report.get(
        "duplicates",
        {}
    )

    if duplicates.get(
        "is_duplicate"
    ):

        score += 30

        reasons.append(
            "Potential duplicate report"
        )

    image_path = (
        report.get("image", {})
        .get("path")
    )

    if image_path:

        same_image_count = sum(
            1
            for r in existing_reports
            if (
                r.get("image", {})
                .get("path")
                == image_path
            )
        )

        if same_image_count > 0:

            score += 40

            reasons.append(
                "Previously used image"
            )

    score = min(
        score,
        100
    )

    flagged = score >= 50

    return {
        "score": score,
        "flagged": flagged,
        "reasons": reasons
    }