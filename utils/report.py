import json
from datetime import datetime
from pathlib import Path
import uuid


DATA_DIR = Path("data")
REPORTS_FILE = DATA_DIR / "reports.json"

DATA_DIR.mkdir(
    exist_ok=True
)


def create_report(
    issue_type,
    ai_result,
    confirmed_category,
    description,
    image_filename=None,
    image_path=None,
    latitude=None,
    longitude=None
):

    return {

        "id":
            f"CS-{uuid.uuid4().hex[:8].upper()}",

        "created_at":
            datetime.now().isoformat(),

        "issue": {

            "type": issue_type,

            "confirmed_category":
                confirmed_category,

            "ai_prediction":
                ai_result
        },

        "description":
            description,

        "image": {

            "filename":
                image_filename,

            "path":
                image_path
        },

        "location": {

            "latitude":
                latitude,

            "longitude":
                longitude,

            "address":
                None
        },

        "priority": {

            "score":
                None,

            "level":
                None,

            "factors":
                {}
        },

        "duplicates": {

            "is_duplicate":
                None,

            "matches":
                []
        },

        "spam": {

            "score":
                None,

            "flagged":
                None,

            "reasons":
                []
        },

        "resolution": {

            "after_image":
                None,

            "image_similarity":
                None,

            "ai_verified":
                None,

            "citizen_confirmed":
                None
        },

        "assignment": {

            "authority_id":
                None,

            "authority_name":
                None,

            "department":
                None,

            "assigned_at":
                None
        },

        "status":
            "Reported",

        "status_history": [

            {

                "status":
                    "Reported",

                "timestamp":
                    datetime.now().isoformat()
            }

        ]
    }


def save_report(report):

    reports = load_reports()

    reports.append(report)

    with open(
        REPORTS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            reports,
            file,
            indent=4
        )


def load_reports():

    if not REPORTS_FILE.exists():

        return []

    try:

        with open(
            REPORTS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except (
        json.JSONDecodeError,
        FileNotFoundError
    ):

        return []