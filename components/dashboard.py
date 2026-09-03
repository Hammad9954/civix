import streamlit as st
from collections import Counter
import pandas as pd
import folium
from streamlit_folium import st_folium


def issue_statistics(reports):
    issues = []

    for report in reports:
        issue = report.get("issue", {}).get("type")

        if issue:
            issues.append(issue)

    return Counter(issues)


def render_issue_map(reports):
    valid_reports = []

    for report in reports:
        location = report.get("location", {})

        lat = location.get("latitude")
        lon = location.get("longitude")

        if lat is not None and lon is not None:
            valid_reports.append((report, lat, lon))

    if not valid_reports:
        st.info("📍 No GPS reports available yet.")
        return

    first_report = valid_reports[0]

    m = folium.Map(
        location=[first_report[1], first_report[2]],
        zoom_start=13
    )

    for report, lat, lon in valid_reports:

        issue = report.get(
            "issue", {}
        ).get("type", "Unknown")

        priority = report.get(
            "priority", {}
        ).get("level", "LOW")

        status = report.get(
            "status", "Reported"
        )

        folium.Marker(
            [lat, lon],
            popup=f"""
            <b>Issue:</b> {issue}<br>
            <b>Priority:</b> {priority}<br>
            <b>Status:</b> {status}
            """,
            tooltip=issue
        ).add_to(m)

    st_folium(
        m,
        width=900,
        height=500
    )


def render_dashboard(reports):

    st.title("🏙️ CivicSense Dashboard")

    # =========================
    # KPI CARDS
    # =========================

    total = len(reports)

    resolved = sum(
        1 for r in reports
        if r.get("status") in ["Resolved", "Closed"]
    )

    pending = total - resolved

    critical = sum(
        1 for r in reports
        if r.get("priority", {}).get("level") == "CRITICAL"
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "📋 Total Reports",
        total
    )

    col2.metric(
        "✅ Resolved",
        resolved
    )

    col3.metric(
        "⏳ Pending",
        pending
    )

    col4.metric(
        "🚨 Critical Issues",
        critical
    )

    st.markdown("---")

    # =========================
    # ISSUE DISTRIBUTION
    # =========================

    st.subheader("📊 Issue Distribution")

    stats = issue_statistics(reports)

    if stats:

        df = pd.DataFrame(
            stats.items(),
            columns=["Issue", "Reports"]
        )

        st.bar_chart(
            df.set_index("Issue")
        )

    else:
        st.info("No reports available yet.")

    st.markdown("---")

    # =========================
    # STATUS DISTRIBUTION
    # =========================

    st.subheader("📌 Report Status")

    status_counter = Counter(
        r.get("status", "Reported")
        for r in reports
    )

    status_df = pd.DataFrame(
        status_counter.items(),
        columns=["Status", "Reports"]
    )

    if not status_df.empty:
        st.bar_chart(
            status_df.set_index("Status")
        )

    st.markdown("---")

    # =========================
    # HOTSPOT MAP
    # =========================

    st.subheader("🗺️ Civic Issue Hotspots")

    render_issue_map(reports)