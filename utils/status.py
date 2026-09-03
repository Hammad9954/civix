from datetime import datetime


STATUSES = [
    "Reported",
    "Under Review",
    "Assigned",
    "In Progress",
    "Resolved",
    "Closed"
]


def update_status(
    report,
    status
):

    if status not in STATUSES:

        return report

    report["status"] = status

    if "status_history" not in report:

        report["status_history"] = []

    report["status_history"].append({

        "status": status,

        "timestamp":
            datetime.now().isoformat()

    })

    return report