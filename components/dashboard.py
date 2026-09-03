from app_streamlit import reports
import streamlit as st
from collections import Counter

import pandas as pd

import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap


def issue_statistics(reports):

    issues = []

    for report in reports:

        issue = (
            report.get("issue", {})
            .get("type")
        )

        if issue:

            issues.append(issue)

    return Counter(issues)

def render_issue_heatmap(reports):

    points = []

    st.write("Total reports:", len(reports))

    for report in reports:
        location = report.get("location", {})

        lat = location.get("latitude")
        lon = location.get("longitude")

        if lat is None or lon is None:
            continue

        points.append([float(lat), float(lon)])

    st.write("GPS points found:", len(points))
    st.write("Points:", points)

    if not points:
        st.warning("No GPS coordinates found in reports.")
        return

    avg_lat = sum(p[0] for p in points) / len(points)
    avg_lon = sum(p[1] for p in points) / len(points)

    m = folium.Map(
        location=[avg_lat, avg_lon],
        zoom_start=13
    )

    HeatMap(
        points,
        radius=30,
        blur=25,
        min_opacity=0.35
    ).add_to(m)

    st_folium(m, width=900, height=550)


def render_dashboard(reports):

    st.title(
        "🏙️ CivicSense Dashboard"
    )

    total = len(reports)

    resolved = sum(

        1
        for r in reports

        if r.get("status")
        in [
            "Resolved",
            "Closed"
        ]
    )

    pending = (
        total -
        resolved
    )

    critical = sum(

        1
        for r in reports

        if (
            r.get(
                "priority",
                {}
            ).get(
                "level"
            )
            == "CRITICAL"
        )
    )

    col1, col2, col3, col4 = (
        st.columns(4)
    )

    col1.metric(
        "Total Reports",
        total
    )

    col2.metric(
        "Resolved",
        resolved
    )

    col3.metric(
        "Pending",
        pending
    )

    col4.metric(
        "Critical Issues",
        critical
    )

    stats = issue_statistics(
        reports
    )

    df = pd.DataFrame(
        stats.items(),
        columns=[
            "Issue",
            "Reports"
        ]
    )

    st.subheader(
        "📊 Issue Distribution"
    )

    if not df.empty:

        st.bar_chart(
            df.set_index(
                "Issue"
            )
        )

    st.subheader("🔥 Civic Issue Hotspots")
st.caption("Areas with a higher concentration of reported civic issues appear hotter.")

render_issue_heatmap(reports)