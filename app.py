"""
CivicAI — Smart Civic Issue Reporting & Resolution Platform

Streamlit entry-point.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import folium
import streamlit as st
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation

# ────────────────────────────────────────────────────────────
# Ensure project root is on sys.path
# ────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ────────────────────────────────────────────────────────────
# Project Imports
# ────────────────────────────────────────────────────────────

from ai.classifier import CivicIssueClassifier
from ai.duplicate_detector import find_duplicate_reports
from ai.priority_engine import calculate_priority
from ai.resolution_verifier import verify_resolution
from components.dashboard import render_dashboard

from components.upload import render_upload_section
from components.report_form import render_report_form

from config.constants import ISSUE_TYPES, UPLOADS_DIR

from utils.authority import assign_authority

from utils.report import (
    create_report,
    save_report,
    load_reports,
)


# ────────────────────────────────────────────────────────────
# Page Configuration
# ────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="CivicAI — Smart Civic Issue Reporting",
    page_icon="🏙️",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ────────────────────────────────────────────────────────────
# Initialise Session State
# ────────────────────────────────────────────────────────────

if "classifier" not in st.session_state:
    st.session_state.classifier = CivicIssueClassifier()

if "ai_result" not in st.session_state:
    st.session_state.ai_result = None

if "submitted_report" not in st.session_state:
    st.session_state.submitted_report = None

if "last_uploaded_file" not in st.session_state:
    st.session_state.last_uploaded_file = None


# ────────────────────────────────────────────────────────────
# Header
# ────────────────────────────────────────────────────────────

st.title("🏙️ CivicAI")

st.caption(
    "Smart Civic Issue Reporting & Resolution Platform"
)

st.markdown("---")
page = st.radio(
    "Navigation",
    [
        "📝 Report Issue",
        "📊 Civic Dashboard"
    ],
    horizontal=True
)
if page == "📊 Civic Dashboard":

    reports = load_reports()

    render_dashboard(reports)

    st.stop()


# ────────────────────────────────────────────────────────────
# Step 1 — Upload Image
# ────────────────────────────────────────────────────────────

image, uploaded_file = render_upload_section()


# Reset analysis when a new image is uploaded
if (
    uploaded_file is not None
    and uploaded_file.name
    != st.session_state.last_uploaded_file
):

    st.session_state.last_uploaded_file = uploaded_file.name

    st.session_state.ai_result = None

    st.session_state.submitted_report = None


# Stop if no image
if image is None:
    st.stop()


# ────────────────────────────────────────────────────────────
# Step 2 — AI Analysis
# ────────────────────────────────────────────────────────────

st.markdown("---")

st.subheader("🤖 AI Analysis")


classifier: CivicIssueClassifier = (
    st.session_state.classifier
)


if st.button(
    "Analyse Image",
    type="secondary",
    use_container_width=True,
):

    with st.spinner("Analysing image..."):

        ai_result = classifier.predict(image)

        st.session_state.ai_result = ai_result


ai_result = st.session_state.ai_result


if ai_result is None:

    st.info(
        "Click **Analyse Image** to run the "
        "AI classifier on your uploaded photo."
    )

    st.stop()


# ────────────────────────────────────────────────────────────
# Step 3 — Report Form
# ────────────────────────────────────────────────────────────

st.markdown("---")

form_data = render_report_form(ai_result)


# ────────────────────────────────────────────────────────────
# PHASE 2 — LOCATION
# ────────────────────────────────────────────────────────────

st.markdown("---")

st.subheader("📍 Report Location")


location = streamlit_geolocation()


latitude = location.get("latitude")
longitude = location.get("longitude")


if (
    latitude is not None
    and longitude is not None
):

    st.success(
        f"📍 Location captured: "
        f"{latitude:.6f}, {longitude:.6f}"
    )


    # ────────────────────────────────────────────────
    # Show Map
    # ────────────────────────────────────────────────

    report_map = folium.Map(
        location=[
            latitude,
            longitude,
        ],
        zoom_start=16,
    )


    folium.Marker(
        [
            latitude,
            longitude,
        ],
        popup="Your reported issue",
        tooltip="📍 Report Location",
        icon=folium.Icon(
            color="red",
            icon="warning-sign",
        ),
    ).add_to(report_map)


    st_folium(
        report_map,
        width=700,
        height=400,
    )


else:

    st.warning(
        "📍 Please allow browser location access "
        "to capture your report location."
    )


# Stop until report form is submitted
if form_data is None:
    st.stop()


# ────────────────────────────────────────────────────────────
# Step 4 — Prepare Report
# ────────────────────────────────────────────────────────────

confirmed_category = form_data[
    "confirmed_category"
]

description = form_data[
    "description"
]


# ────────────────────────────────────────────────────────────
# Save Uploaded Image
# ────────────────────────────────────────────────────────────

image_filename = (
    uploaded_file.name
    if uploaded_file
    else None
)

image_path = None


if uploaded_file is not None:

    uploads_dir = Path(UPLOADS_DIR)

    uploads_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    image_path = str(
        uploads_dir / uploaded_file.name
    )


    with open(
        image_path,
        "wb"
    ) as f:

        uploaded_file.seek(0)

        f.write(
            uploaded_file.read()
        )


# ────────────────────────────────────────────────────────────
# Create Report
# ────────────────────────────────────────────────────────────

report = create_report(

    issue_type=confirmed_category,

    ai_result=ai_result,

    confirmed_category=confirmed_category,

    description=description,

    image_filename=image_filename,

    image_path=image_path,

    latitude=latitude,

    longitude=longitude,
)


# ============================================================
# PHASE 5 — REPORT STATUS
# ============================================================

report["status"] = "Reported"

report["status_history"] = [

    {
        "status": "Reported",

        "timestamp": report["created_at"],
    }

]


# ============================================================
# PHASE 3 — DUPLICATE DETECTION
# ============================================================

existing_reports = load_reports()


duplicate_matches = find_duplicate_reports(

    report,

    existing_reports,
)


report["duplicates"] = {

    "is_duplicate":
        len(duplicate_matches) > 0,

    "matches":
        duplicate_matches,
}


# ────────────────────────────────────────────────────────────
# Display Duplicate Results
# ────────────────────────────────────────────────────────────

st.markdown("---")

st.subheader("🔍 Duplicate Detection")


if duplicate_matches:

    st.warning(

        f"⚠️ {len(duplicate_matches)} "
        "similar report(s) found nearby."
    )


    for match in duplicate_matches[:5]:

        st.write(

            f"**{match['report_id']}** — "

            f"{match['distance_m']} m away — "

            f"Similarity: "

            f"{match['duplicate_score'] * 100:.0f}%"

        )

else:

    st.success(
        "✅ No likely duplicate reports found."
    )


# ============================================================
# PHASE 4 — PRIORITY ENGINE
# ============================================================

priority = calculate_priority(

    report,

    duplicate_count=len(
        duplicate_matches
    ),

)


report["priority"] = priority


# ────────────────────────────────────────────────────────────
# Display Priority
# ────────────────────────────────────────────────────────────

st.markdown("---")

st.subheader("🧠 Intelligent Priority")


score = priority["score"]

level = priority["level"]


if level == "CRITICAL":

    st.error(
        f"🔴 CRITICAL — {score}/100"
    )

elif level == "HIGH":

    st.warning(
        f"🟠 HIGH — {score}/100"
    )

elif level == "MEDIUM":

    st.info(
        f"🟡 MEDIUM — {score}/100"
    )

else:

    st.success(
        f"🟢 LOW — {score}/100"
    )


with st.expander(
    "View priority factors"
):

    st.json(
        priority["factors"]
    )


# ============================================================
# PHASE 5 — AUTHORITY ASSIGNMENT
# ============================================================

authority = assign_authority(
    report
)


report["assignment"] = authority


# ────────────────────────────────────────────────────────────
# Display Authority Assignment
# ────────────────────────────────────────────────────────────

st.markdown("---")

st.subheader("🏛️ Authority Assignment")


col1, col2 = st.columns(2)


with col1:

    st.write(
        f"**Department:** "
        f"{authority['department']}"
    )

    st.write(
        f"**Authority ID:** "
        f"{authority['authority_id']}"
    )


with col2:

    st.write(
        f"**Authority:** "
        f"{authority['authority_name']}"
    )

    st.write(
        f"**Status:** "
        f"{report['status']}"
    )


st.info(
    "📋 Your report has been assigned "
    "to the appropriate civic department."
)


# ============================================================
# SAVE FINAL REPORT
# ============================================================

save_report(report)


st.session_state.submitted_report = report


# ────────────────────────────────────────────────────────────
# Step 5 — Success & Report Summary
# ────────────────────────────────────────────────────────────

st.markdown("---")

st.success(
    f"✅ Report submitted successfully! "
    f"**{report['id']}**"
)


st.subheader("📄 Report Summary")


col1, col2 = st.columns(2)


# ────────────────────────────────────────────────────────────
# Column 1
# ────────────────────────────────────────────────────────────

with col1:

    st.metric(
        "Report ID",
        report["id"]
    )

    st.metric(
        "Issue Type",
        report["issue"]["type"]
    )

    st.metric(
        "Status",
        report["status"]
        .replace("_", " ")
        .title()
    )

    st.metric(
        "Priority",
        f"{report['priority']['level']} "
        f"({report['priority']['score']}/100)"
    )


# ────────────────────────────────────────────────────────────
# Column 2
# ────────────────────────────────────────────────────────────

with col2:

    st.metric(
        "AI Available",
        "Yes"
        if report["ai"]["available"]
        else "No"
    )


    if report["ai"]["available"]:

        st.metric(
            "AI Category",
            report["ai"]["category"]
            or "—"
        )


        st.metric(
            "AI Confidence",
            f"{report['ai']['confidence'] * 100:.0f}%"
        )


    st.metric(
        "Confirmed Category",
        report["user"]["confirmed_category"]
    )


# ────────────────────────────────────────────────────────────
# Description
# ────────────────────────────────────────────────────────────

if description:

    st.markdown(
        f"**Description:** {description}"
    )


# ────────────────────────────────────────────────────────────
# Location
# ────────────────────────────────────────────────────────────

if (
    latitude is not None
    and longitude is not None
):

    st.markdown(
        f"**📍 Location:** "
        f"{latitude:.6f}, "
        f"{longitude:.6f}"
    )


# ────────────────────────────────────────────────────────────
# Authority
# ────────────────────────────────────────────────────────────

st.markdown(
    f"**🏛️ Department:** "
    f"{authority['department']}"
)


st.markdown(
    f"**👤 Assigned Authority:** "
    f"{authority['authority_name']}"
)


# ────────────────────────────────────────────────────────────
# Created Time
# ────────────────────────────────────────────────────────────

st.markdown(
    f"**Created at:** "
    f"{report['created_at']}"
)


# ────────────────────────────────────────────────────────────
# Full JSON
# ────────────────────────────────────────────────────────────

with st.expander(
    "View full report JSON"
):

    st.json(report)

with st.expander(
    "View full report JSON"
):

    st.json(report)


# ============================================================
# PHASE 6 — RESOLUTION VERIFICATION
# ============================================================

st.markdown("---")

st.subheader("🔍 Resolution Verification")

st.info(
    "Once the civic authority repairs the issue, "
    "upload an after-repair image for verification."
)

after_image = st.file_uploader(
    "📷 Upload After-Repair Image",
    type=["jpg", "jpeg", "png"],
    key="after_repair_image"
)

if after_image is not None:

    st.image(
        after_image,
        caption="After-Repair Image",
        use_container_width=True
    )

    if st.button(
        "🤖 Verify Resolution",
        use_container_width=True
    ):

        with st.spinner(
            "Comparing before and after images..."
        ):

            after_path = (
                Path(UPLOADS_DIR)
                / f"after_{report['id']}_{after_image.name}"
            )

            with open(
                after_path,
                "wb"
            ) as f:

                f.write(
                    after_image.getbuffer()
                )

            verification = verify_resolution(
                report["image"]["path"],
                str(after_path)
            )

            report["resolution"] = {
                "after_image": str(after_path),
                "image_similarity": verification["similarity"],
                "ai_verified": verification["verified"],
                "citizen_confirmed": None
            }

            save_report(report)

            st.session_state.submitted_report = report

            if verification["verified"]:

                st.success(
                    "🤖 AI suggests that the issue "
                    "has been resolved."
                )

                st.write(
                    f"Image similarity: "
                    f"{verification['similarity'] * 100:.1f}%"
                )

            else:

                st.warning(
                    "⚠️ AI could not confidently verify "
                    "the resolution."
                )


# ============================================================
# CITIZEN CONFIRMATION
# ============================================================

if (
    report.get("resolution", {})
    .get("ai_verified") is True
):

    st.markdown("### Is the issue actually resolved?")

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "✅ Confirm Resolution",
            use_container_width=True
        ):

            report["resolution"][
                "citizen_confirmed"
            ] = True

            report["status"] = "Closed"

            report["status_history"].append({
                "status": "Closed",
                "timestamp": __import__(
                    "datetime"
                ).datetime.now().isoformat()
            })

            save_report(report)

            st.session_state.submitted_report = report

            st.success(
                "✅ Issue successfully closed!"
            )

    with col2:

        if st.button(
            "❌ Issue Not Resolved",
            use_container_width=True
        ):

            report["resolution"][
                "citizen_confirmed"
            ] = False

            report["status"] = "In Progress"

            report["status_history"].append({
                "status": "In Progress",
                "timestamp": __import__(
                    "datetime"
                ).datetime.now().isoformat()
            })

            save_report(report)

            st.session_state.submitted_report = report

            st.warning(
                "⚠️ Issue reopened and returned "
                "to the authority."
            )


# ────────────────────────────────────────────────────────────
# Footer
# ────────────────────────────────────────────────────────────

st.markdown("---")

st.caption(
    "CivicAI — Smart Civic Issue Reporting "
    "& Resolution Platform"
)    


# ────────────────────────────────────────────────────────────
# Footer
# ────────────────────────────────────────────────────────────

st.markdown("---")

st.caption(
    "CivicAI — Smart Civic Issue Reporting "
    "& Resolution Platform"
)