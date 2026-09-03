import streamlit as st

from pathlib import Path

from datetime import datetime

import folium

from streamlit_folium import st_folium

from streamlit_geolocation import (
    streamlit_geolocation
)


from ai.classifier import (
    CivicIssueClassifier
)

from ai.duplicate_detector import (
    find_duplicate_reports
)

from ai.priority_engine import (
    calculate_priority
)

from ai.spam_detector import (
    calculate_spam_score
)

from ai.resolution_verifier import (
    verify_resolution
)

from utils.report import (
    create_report,
    save_report,
    load_reports
)

from utils.authority import (
    assign_authority
)

from components.report_form import (
    render_report_form
)

from components.dashboard import (
    render_dashboard
)

from components.chatbot import (
    civic_chatbot
)

from components.admin_dashboard import (
    render_admin_dashboard
)


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(

    page_title="CivicSense",

    page_icon="🏙️",

    layout="wide"
)


# ============================================================
# DIRECTORIES
# ============================================================

UPLOADS_DIR = Path(
    "uploads"
)

UPLOADS_DIR.mkdir(
    exist_ok=True
)


# ============================================================
# TITLE
# ============================================================

st.title(
    "🏙️ CivicSense"
)

st.caption(
    "Smart Civic Issue Reporting & Resolution Platform"
)


# ============================================================
# INITIALIZE CLASSIFIER
# ============================================================

@st.cache_resource
def get_classifier():

    return CivicIssueClassifier()


classifier = get_classifier()


# ============================================================
# NAVIGATION
# ============================================================

page = st.radio(

    "Navigation",

    [

        "📝 Report Issue",

        "📊 Civic Dashboard",

        "🤖 Civic Assistant",

        "🏛️ Authority Panel"

    ],

    horizontal=True
)


# ============================================================
# DASHBOARD
# ============================================================

if page == "📊 Civic Dashboard":

    reports = load_reports()

    render_dashboard(
        reports
    )

    st.stop()


# ============================================================
# CHATBOT
# ============================================================

if page == "🤖 Civic Assistant":

    civic_chatbot()

    st.stop()


# ============================================================
# AUTHORITY PANEL
# ============================================================

if page == "🏛️ Authority Panel":

    reports = load_reports()

    render_admin_dashboard(
        reports
    )

    st.stop()


# ============================================================
# REPORT PAGE
# ============================================================

st.subheader(
    "📷 Upload Civic Issue Image"
)


uploaded_image = st.file_uploader(

    "Upload an image",

    type=[
        "jpg",
        "jpeg",
        "png"
    ]
)


ai_result = None


# ============================================================
# AI ANALYSIS
# ============================================================

if uploaded_image is not None:

    st.image(

        uploaded_image,

        caption="Uploaded Image",

        use_container_width=True
    )

    if st.button(
        "🤖 Analyse Image",
        use_container_width=True
    ):

        with st.spinner(
            "Analysing civic issue..."
        ):

            ai_result = classifier.predict(
                uploaded_image
            )

        st.success(
            "AI analysis completed."
        )

        detections = (
            ai_result.get(
                "detections",
                []
            )
        )

        if detections:

            st.subheader(
                "🔍 AI Detection Results"
            )

            for detection in detections:

                st.write(

                    f"**{detection['issue_type']}** "
                    f"— "
                    f"{detection['confidence'] * 100:.1f}%"

                )

        else:

            st.warning(
                "No civic issue was detected."
            )


# ============================================================
# REPORT FORM
# ============================================================

if uploaded_image is None:

    st.info(
        "Upload an image to continue."
    )

    st.stop()


form_data = render_report_form(
    ai_result
)


# ============================================================
# LOCATION
# ============================================================

st.markdown("---")

st.subheader(
    "📍 Report Location"
)


location = streamlit_geolocation()


latitude = location.get(
    "latitude"
)

longitude = location.get(
    "longitude"
)


if (
    latitude is not None
    and
    longitude is not None
):

    st.success(

        f"📍 Location captured: "
        f"{latitude:.6f}, "
        f"{longitude:.6f}"

    )

    report_map = folium.Map(

        location=[
            latitude,
            longitude
        ],

        zoom_start=16
    )

    folium.Marker(

        [
            latitude,
            longitude
        ],

        popup=
            "Your reported issue",

        tooltip=
            "📍 Report Location",

        icon=folium.Icon(
            color="red",
            icon="warning-sign"
        )

    ).add_to(
        report_map
    )

    st_folium(

        report_map,

        width=700,

        height=400
    )

else:

    st.warning(
        "📍 Please click the "
        "location button and allow "
        "browser location access."
    )


# ============================================================
# FORM SUBMISSION
# ============================================================

if form_data is None:

    st.stop()


# ============================================================
# CREATE IMAGE FILE
# ============================================================

image_filename = (
    uploaded_image.name
)

image_path = (
    UPLOADS_DIR /
    image_filename
)


with open(
    image_path,
    "wb"
) as file:

    file.write(
        uploaded_image.getbuffer()
    )


# ============================================================
# CREATE REPORT
# ============================================================

confirmed_category = (
    form_data.get(
        "confirmed_category",
        "Other"
    )
)

description = (
    form_data.get(
        "description",
        ""
    )
)


report = create_report(

    issue_type=
        confirmed_category,

    ai_result=
        ai_result or {},

    confirmed_category=
        confirmed_category,

    description=
        description,

    image_filename=
        image_filename,

    image_path=
        str(image_path),

    latitude=
        latitude,

    longitude=
        longitude
)


# ============================================================
# STATUS
# ============================================================

report["status"] = (
    "Reported"
)

report["status_history"] = [

    {

        "status":
            "Reported",

        "timestamp":
            report["created_at"]

    }

]


# ============================================================
# EXISTING REPORTS
# ============================================================

existing_reports = load_reports()


# ============================================================
# DUPLICATE DETECTION
# ============================================================

duplicate_matches = (
    find_duplicate_reports(

        report,

        existing_reports

    )
)


report["duplicates"] = {

    "is_duplicate":
        len(
            duplicate_matches
        ) > 0,

    "matches":
        duplicate_matches
}


# ============================================================
# SPAM DETECTION
# ============================================================

spam_result = (
    calculate_spam_score(

        report,

        existing_reports

    )
)


report["spam"] = (
    spam_result
)


# ============================================================
# PRIORITY
# ============================================================

priority = (
    calculate_priority(

        report,

        duplicate_count=
            len(
                duplicate_matches
            )

    )
)


report["priority"] = (
    priority
)


# ============================================================
# AUTHORITY ASSIGNMENT
# ============================================================

authority = (
    assign_authority(
        report
    )
)


report["assignment"] = (
    authority
)


# ============================================================
# SAVE REPORT
# ============================================================

save_report(
    report
)


# ============================================================
# REPORT SUMMARY
# ============================================================

st.markdown("---")

st.subheader(
    "📋 Report Summary"
)


col1, col2 = (
    st.columns(2)
)


with col1:

    st.write(
        "**Issue:**",
        confirmed_category
    )

    st.write(
        "**Priority:**",
        report[
            "priority"
        ][
            "level"
        ]
    )

    st.write(
        "**Priority Score:**",
        report[
            "priority"
        ][
            "score"
        ]
    )

    st.write(
        "**Status:**",
        report[
            "status"
        ]
    )


with col2:

    st.write(
        "**Department:**",
        report[
            "assignment"
        ][
            "department"
        ]
    )

    st.write(
        "**Authority:**",
        report[
            "assignment"
        ][
            "authority_name"
        ]
    )

    st.write(
        "**Spam Score:**",
        report[
            "spam"
        ][
            "score"
        ]
    )

    st.write(
        "**Duplicate:**",
        "Yes"
        if report[
            "duplicates"
        ][
            "is_duplicate"
        ]
        else "No"
    )


# ============================================================
# RESOLUTION VERIFICATION
# ============================================================

st.markdown("---")

st.subheader(
    "🔍 Resolution Verification"
)

st.info(
    "Once the civic authority repairs "
    "the issue, upload an after-repair "
    "image for verification."
)


after_image = st.file_uploader(

    "📷 Upload After-Repair Image",

    type=[
        "jpg",
        "jpeg",
        "png"
    ],

    key="after_repair_image"
)


if after_image is not None:

    st.image(

        after_image,

        caption=
            "After-Repair Image",

        use_container_width=True
    )

    if st.button(
        "🤖 Verify Resolution",
        use_container_width=True
    ):

        with st.spinner(
            "Comparing before and "
            "after images..."
        ):

            after_path = (

                UPLOADS_DIR /

                (
                    f"after_"
                    f"{report['id']}_"
                    f"{after_image.name}"
                )

            )

            with open(
                after_path,
                "wb"
            ) as file:

                file.write(
                    after_image.getbuffer()
                )

            verification = (
                verify_resolution(

                    report[
                        "image"
                    ][
                        "path"
                    ],

                    str(
                        after_path
                    )

                )
            )


            report[
                "resolution"
            ] = {

                "after_image":
                    str(
                        after_path
                    ),

                "image_similarity":
                    verification[
                        "similarity"
                    ],

                "ai_verified":
                    verification[
                        "verified"
                    ],

                "citizen_confirmed":
                    None

            }


            # Update existing saved report
            reports = load_reports()

            for index, saved_report in enumerate(
                reports
            ):

                if (
                    saved_report.get(
                        "id"
                    )
                    == report.get(
                        "id"
                    )
                ):

                    reports[index] = report

            with open(
                "data/reports.json",
                "w",
                encoding="utf-8"
            ) as file:

                import json

                json.dump(
                    reports,
                    file,
                    indent=4
                )


            if verification[
                "verified"
            ]:

                st.success(
                    "🤖 AI suggests that "
                    "the issue has been resolved."
                )

                st.write(

                    "Image similarity: "
                    f"{verification['similarity'] * 100:.1f}%"

                )

            else:

                st.warning(
                    "⚠️ AI could not confidently "
                    "verify the resolution."
                )


# ============================================================
# CITIZEN CONFIRMATION
# ============================================================

if (
    report
    .get(
        "resolution",
        {}
    )
    .get(
        "ai_verified"
    )
    is True
):

    st.markdown("---")

    st.subheader(
        "Is the issue actually resolved?"
    )

    col1, col2 = (
        st.columns(2)
    )


    with col1:

        if st.button(
            "✅ Confirm Resolution",
            use_container_width=True
        ):

            report[
                "resolution"
            ][
                "citizen_confirmed"
            ] = True

            report[
                "status"
            ] = "Closed"

            report[
                "status_history"
            ].append({

                "status":
                    "Closed",

                "timestamp":
                    datetime.now().isoformat()

            })


            reports = load_reports()

            for index, saved_report in enumerate(
                reports
            ):

                if (
                    saved_report.get(
                        "id"
                    )
                    == report.get(
                        "id"
                    )
                ):

                    reports[index] = report


            import json

            with open(
                "data/reports.json",
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    reports,
                    file,
                    indent=4
                )


            st.success(
                "✅ Issue successfully closed!"
            )


    with col2:

        if st.button(
            "❌ Issue Not Resolved",
            use_container_width=True
        ):

            report[
                "resolution"
            ][
                "citizen_confirmed"
            ] = False

            report[
                "status"
            ] = "In Progress"

            report[
                "status_history"
            ].append({

                "status":
                    "In Progress",

                "timestamp":
                    datetime.now().isoformat()

            })


            reports = load_reports()

            for index, saved_report in enumerate(
                reports
            ):

                if (
                    saved_report.get(
                        "id"
                    )
                    == report.get(
                        "id"
                    )
                ):

                    reports[index] = report


            import json

            with open(
                "data/reports.json",
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    reports,
                    file,
                    indent=4
                )


            st.warning(
                "⚠️ Issue reopened and "
                "returned to the authority."
            )


# ============================================================
# RAW REPORT
# ============================================================

st.markdown("---")

with st.expander(
    "🔧 Developer: View full report JSON"
):

    st.json(
        report
    )