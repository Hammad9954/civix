"""
CivicAI — Smart Civic Issue Reporting & Resolution Platform (V1)

Entry-point for the Streamlit application.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import streamlit as st
import folium

from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation

from ai.duplicate_detector import find_duplicate_reports
from ai.priority_engine import calculate_priority
from utils.report import load_reports

# ── Ensure project root is on sys.path ──────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.classifier import CivicIssueClassifier
from components.upload import render_upload_section
from components.report_form import render_report_form
from config.constants import ISSUE_TYPES, UPLOADS_DIR
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


# ────────────────────────────────────────────────────────────
# Header
# ────────────────────────────────────────────────────────────
st.title("🏙️ CivicAI")
st.caption("Smart Civic Issue Reporting & Resolution Platform  •  V1")
st.markdown("---")

# ────────────────────────────────────────────────────────────
# Step 1 — Upload Image
# ────────────────────────────────────────────────────────────
image, uploaded_file = render_upload_section()

if "last_uploaded_file" not in st.session_state:
    st.session_state.last_uploaded_file = None

if uploaded_file is not None and uploaded_file.name != st.session_state.last_uploaded_file:
    st.session_state.last_uploaded_file = uploaded_file.name
    st.session_state.ai_result = None
    st.session_state.submitted_report = None

if image is None:
    st.stop()

# ────────────────────────────────────────────────────────────
# Step 2 — AI Analysis
# ────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("🤖 AI Analysis")

classifier: CivicIssueClassifier = st.session_state.classifier

if st.button("Analyse Image", type="secondary", use_container_width=True):
    with st.spinner("Analysing image…"):
        ai_result = classifier.predict(image)
        st.session_state.ai_result = ai_result

ai_result = st.session_state.ai_result

if ai_result is None:
    st.info("Click **Analyse Image** to run the AI classifier on your uploaded photo.")
    st.stop()

# ────────────────────────────────────────────────────────────
# Step 3 — Report Form (category confirmation + description)
# ────────────────────────────────────────────────────────────
st.markdown("---")
form_data = render_report_form(ai_result)
# ============================================================
# PHASE 2 — LOCATION
# ============================================================

st.markdown("---")
st.subheader("📍 Report Location")

location = streamlit_geolocation()

latitude = location.get("latitude")
longitude = location.get("longitude")

if latitude is not None and longitude is not None:

    st.success(
        f"📍 Location captured: "
        f"{latitude:.6f}, {longitude:.6f}"
    )

    # Show map
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
        "📍 Please click the location button "
        "and allow browser location access."
    )

if form_data is None:
    st.stop()

# ────────────────────────────────────────────────────────────
# Step 4 — Create & Save Report
# ────────────────────────────────────────────────────────────
confirmed_category = form_data["confirmed_category"]
description = form_data["description"]

# Optionally save the uploaded image to disk
image_filename = uploaded_file.name if uploaded_file else None
image_path = None
if uploaded_file is not None:
    uploads_dir = Path(UPLOADS_DIR)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    image_path = str(uploads_dir / uploaded_file.name)
    with open(image_path, "wb") as f:
        uploaded_file.seek(0)
        f.write(uploaded_file.read())
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
# PHASE 3 — DUPLICATE DETECTION
# ============================================================

existing_reports = load_reports()

duplicate_matches = find_duplicate_reports(
    report,
    existing_reports,
)

report["duplicates"] = {
    "is_duplicate": len(duplicate_matches) > 0,
    "matches": duplicate_matches,
}

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
    duplicate_count=len(duplicate_matches),
)

report["priority"] = priority

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

with st.expander("View priority factors"):

    st.json(
        priority["factors"]
    )
    save_report(report)

save_report(report)
st.session_state.submitted_report = report

# ────────────────────────────────────────────────────────────
# Step 5 — Success & Report Summary
# ────────────────────────────────────────────────────────────
st.markdown("---")
st.success(f"✅ Report submitted successfully!  **{report['id']}**")

st.subheader("📄 Report Summary")

col1, col2 = st.columns(2)
with col1:
    st.metric("Report ID", report["id"])
    st.metric("Issue Type", report["issue"]["type"])
    st.metric("Status", report["status"].replace("_", " ").title())
with col2:
    st.metric("AI Available", "Yes" if report["ai"]["available"] else "No")
    if report["ai"]["available"]:
        st.metric("AI Category", report["ai"]["category"] or "—")
        st.metric("AI Confidence", f"{report['ai']['confidence'] * 100:.0f}%")
    st.metric("Confirmed Category", report["user"]["confirmed_category"])

if description:
    st.markdown(f"**Description:** {description}")

st.markdown(f"**Created at:** {report['created_at']}")

with st.expander("View full report JSON"):
    st.json(report)

st.markdown("---")
st.caption(
    "CivicAI V1 — Built for IGNITE IT 8.0  •  "
    "FSD 2: Smart Civic Issue Reporting & Resolution Platform"
)
