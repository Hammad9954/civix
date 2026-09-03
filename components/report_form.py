"""
CivicAI — Report Form Component

Displays the AI prediction (if available), lets the user confirm or
override the suggested category, optionally add a description, and
returns the collected data to the caller.
"""

from __future__ import annotations

import streamlit as st

from config.constants import ISSUE_TYPES


def render_report_form(
    ai_result: dict,
) -> dict | None:
    """Render the report-submission form and return user inputs on submit.

    Parameters
    ----------
    ai_result:
        The structured dict returned by ``CivicIssueClassifier.predict()``.

    Returns
    -------
    dict | None
        A dict with keys ``confirmed_category`` and ``description`` when
        the user clicks **Submit Report**, otherwise ``None``.
    """
    st.subheader("📋 Issue Details")

    # ── AI Suggestion Banner ─────────────────────────────────
    if ai_result and ai_result.get("available"):
        category = ai_result.get("category", "Unknown")
        subcategory = ai_result.get("subcategory")
        confidence = ai_result.get("confidence", 0.0)
        confidence_pct = f"{confidence * 100:.0f}%"

        # Colour-code confidence
        if confidence >= 0.75:
            badge_colour = "🟢"
        elif confidence >= 0.50:
            badge_colour = "🟡"
        else:
            badge_colour = "🔴"

        label_display = f"**AI Suggestion:** {category}"
        if subcategory and subcategory != category:
            label_display += f"  •  *{subcategory}*"

        st.success(
            f"{label_display}  \n"
            f"{badge_colour} Confidence: **{confidence_pct}**"
        )

        # Show annotated detection image if present
        annotated_img = ai_result.get("annotated_image")
        if annotated_img is not None:
            st.image(
                annotated_img,
                caption="AI Detection & Bounding Boxes",
                use_container_width=True,
            )

        # Show full probability breakdown in an expander
        probabilities = ai_result.get("probabilities", {})
        if probabilities:
            with st.expander("View detailed AI detections & scores"):
                for label, prob in sorted(
                    probabilities.items(), key=lambda x: x[1], reverse=True
                ):
                    st.write(f"- **{label}:** {prob * 100:.1f}%")
    else:
        st.info(
            ai_result.get(
                "message",
                "AI analysis is not available. Please select the issue category manually.",
            )
        )

    # ── Issue Category Selection ─────────────────────────────
    # Pre-select the AI-suggested category if it maps to a known issue type
    ai_suggested_issue: str | None = None
    if ai_result.get("available"):
        ai_suggested_issue = ai_result.get("category")

    default_index = 0
    if ai_suggested_issue and ai_suggested_issue in ISSUE_TYPES:
        default_index = ISSUE_TYPES.index(ai_suggested_issue)

    confirmed_category: str = st.selectbox(
        "Confirm Issue Category",
        options=ISSUE_TYPES,
        index=default_index,
        help="The AI may have suggested a category above. You can accept it or choose a different one.",
        key="issue_category_select",
    )

    # ── Description ──────────────────────────────────────────
    description: str = st.text_area(
        "Description (optional)",
        placeholder="Briefly describe the issue, e.g. 'Large pothole near the bus stop on MG Road, causing traffic slowdown.'",
        max_chars=500,
        key="issue_description",
    )

    # ── Submit ───────────────────────────────────────────────
    submitted = st.button("🚀 Submit Report", type="primary", use_container_width=True)

    if submitted:
        return {
            "confirmed_category": confirmed_category,
            "description": description.strip(),
        }

    return None
