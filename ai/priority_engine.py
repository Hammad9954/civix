def calculate_priority(
    report,
    duplicate_count=0,
    near_school=False,
    near_hospital=False,
    high_traffic=False
):

    issue_type = (
        report.get("issue", {})
        .get("type", "Other")
    )

    severity = {
        "Pothole": 70,
        "Road Damage": 65,
        "Overflowing Garbage": 55,
        "Damaged Streetlight": 60,
        "Water Leakage": 75,
        "Other": 40
    }.get(
        issue_type,
        40
    )

    duplicate_score = min(
        duplicate_count * 3,
        15
    )

    location_score = 0

    if near_school:
        location_score += 10

    if near_hospital:
        location_score += 10

    if high_traffic:
        location_score += 10

    score = round(
        severity * 0.55
        + duplicate_score
        + location_score
    )

    score = min(
        100,
        max(0, score)
    )

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
            "severity": severity,
            "duplicate_reports": duplicate_count,
            "near_school": near_school,
            "near_hospital": near_hospital,
            "high_traffic": high_traffic
        }
    }