from datetime import datetime


STATUSES = [
    "Reported",
    "Under Review",
    "Assigned",
    "In Progress",
    "Resolved",
    "Closed"
]


def update_status(report, status):

    if status not in STATUSES:
        return report

    report["status"] = status

    report["status_history"].append({
        "status": status,
        "timestamp": datetime.now().isoformat()
    })

    return report
    report["status"] = "Reported"

report["status_history"] = [{
    "status": "Reported",
    "timestamp": report["created_at"]
}]