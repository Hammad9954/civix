import streamlit as st
import pandas as pd


def render_admin_dashboard(
    reports
):

    st.title(
        "🏛️ Authority Control Panel"
    )

    st.caption(
        "CivicSense administration "
        "and issue management"
    )

    if not reports:

        st.info(
            "No reports available yet."
        )

        return

    # -----------------------------
    # FILTER OPTIONS
    # -----------------------------

    priorities = sorted(
        set(

            r.get(
                "priority",
                {}
            ).get(
                "level"
            )
            or "LOW"

            for r in reports
        )
    )

    statuses = sorted(
        set(

            r.get(
                "status"
            )
            or "Reported"

            for r in reports
        )
    )

    departments = sorted(
        set(

            r.get(
                "assignment",
                {}
            ).get(
                "department"
            )
            or "Unassigned"

            for r in reports
        )
    )

    # -----------------------------
    # FILTER UI
    # -----------------------------

    col1, col2, col3 = (
        st.columns(3)
    )

    with col1:

        selected_priority = (
            st.selectbox(
                "Priority",
                ["All"] + priorities
            )
        )

    with col2:

        selected_status = (
            st.selectbox(
                "Status",
                ["All"] + statuses
            )
        )

    with col3:

        selected_department = (
            st.selectbox(
                "Department",
                ["All"] + departments
            )
        )

    # -----------------------------
    # APPLY FILTERS
    # -----------------------------

    filtered = reports

    if selected_priority != "All":

        filtered = [

            r for r in filtered

            if (
                r.get(
                    "priority",
                    {}
                ).get(
                    "level"
                )
                or "LOW"
            )
            == selected_priority

        ]

    if selected_status != "All":

        filtered = [

            r for r in filtered

            if (
                r.get("status")
                or "Reported"
            )
            == selected_status

        ]

    if selected_department != "All":

        filtered = [

            r for r in filtered

            if (
                r.get(
                    "assignment",
                    {}
                ).get(
                    "department"
                )
                or "Unassigned"
            )
            == selected_department

        ]

    st.markdown("---")

    # -----------------------------
    # KPI CARDS
    # -----------------------------

    total = len(filtered)

    critical = sum(

        1
        for r in filtered

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

    pending = sum(

        1
        for r in filtered

        if (
            r.get("status")
            or "Reported"
        )
        not in [
            "Resolved",
            "Closed"
        ]
    )

    resolved = sum(

        1
        for r in filtered

        if r.get("status")
        in [
            "Resolved",
            "Closed"
        ]
    )

    c1, c2, c3, c4 = (
        st.columns(4)
    )

    c1.metric(
        "📋 Reports",
        total
    )

    c2.metric(
        "🚨 Critical",
        critical
    )

    c3.metric(
        "⏳ Pending",
        pending
    )

    c4.metric(
        "✅ Resolved",
        resolved
    )

    st.markdown("---")

    # -----------------------------
    # REPORT TABLE
    # -----------------------------

    st.subheader(
        "📋 Complaint Management"
    )

    rows = []

    for report in filtered:

        rows.append({

            "ID":
                report.get(
                    "id",
                    "N/A"
                ),

            "Issue":
                report.get(
                    "issue",
                    {}
                ).get(
                    "type",
                    "Unknown"
                ),

            "Priority":
                report.get(
                    "priority",
                    {}
                ).get(
                    "level"
                )
                or "LOW",

            "Score":
                report.get(
                    "priority",
                    {}
                ).get(
                    "score"
                )
                or 0,

            "Status":
                report.get(
                    "status"
                )
                or "Reported",

            "Department":
                report.get(
                    "assignment",
                    {}
                ).get(
                    "department"
                )
                or "Unassigned",

            "Spam Score":
                report.get(
                    "spam",
                    {}
                ).get(
                    "score"
                )
                or 0
        })

    df = pd.DataFrame(
        rows
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    # -----------------------------
    # REPORT DETAILS
    # -----------------------------

    st.subheader(
        "🔎 Report Details"
    )

    report_ids = [

        r.get("id")

        for r in filtered

        if r.get("id") is not None

    ]

    if not report_ids:

        st.info(
            "No reports match "
            "the selected filters."
        )

        return

    selected_id = st.selectbox(
        "Select a report",
        report_ids
    )

    selected_report = next(

        r for r in filtered

        if r.get("id")
        == selected_id

    )

    col1, col2 = (
        st.columns(2)
    )

    with col1:

        st.write(
            "**Issue:**",
            selected_report.get(
                "issue",
                {}
            ).get(
                "type",
                "Unknown"
            )
        )

        st.write(
            "**Priority:**",
            selected_report.get(
                "priority",
                {}
            ).get(
                "level"
            )
            or "LOW"
        )

        st.write(
            "**Status:**",
            selected_report.get(
                "status"
            )
            or "Reported"
        )

    with col2:

        st.write(
            "**Department:**",
            selected_report.get(
                "assignment",
                {}
            ).get(
                "department"
            )
            or "Unassigned"
        )

        st.write(
            "**Authority:**",
            selected_report.get(
                "assignment",
                {}
            ).get(
                "authority_name"
            )
            or "Unassigned"
        )

        st.write(
            "**Spam Score:**",
            selected_report.get(
                "spam",
                {}
            ).get(
                "score"
            )
            or 0
        )

    st.subheader(
        "📄 Complete Report"
    )

    with st.expander(
        "🔧 Developer: View Raw Report"
    ):

        st.json(
            selected_report
        )