from datetime import datetime


AUTHORITY_MAP = {
    "Pothole": {
        "department": "Roads Department",
        "authority_id": "ROAD-001",
        "authority_name": "Municipal Roads Authority"
    },

    "Road Damage": {
        "department": "Roads Department",
        "authority_id": "ROAD-001",
        "authority_name": "Municipal Roads Authority"
    },

    "Damaged Streetlight": {
        "department": "Electrical Department",
        "authority_id": "ELEC-001",
        "authority_name": "Municipal Electrical Authority"
    },

    "Overflowing Garbage": {
        "department": "Sanitation Department",
        "authority_id": "SAN-001",
        "authority_name": "Municipal Sanitation Authority"
    },

    "Water Leakage": {
        "department": "Water Department",
        "authority_id": "WATER-001",
        "authority_name": "Municipal Water Authority"
    },

    "Other": {
        "department": "General Civic Department",
        "authority_id": "CIVIC-001",
        "authority_name": "Municipal Civic Authority"
    }
}


def assign_authority(report):
    issue_type = report.get(
        "issue", {}
    ).get("type", "Other")

    authority = AUTHORITY_MAP.get(
        issue_type,
        AUTHORITY_MAP["Other"]
    )

    return {
        "authority_id": authority["authority_id"],
        "authority_name": authority["authority_name"],
        "department": authority["department"],
        "assigned_at": datetime.now().isoformat()
    }