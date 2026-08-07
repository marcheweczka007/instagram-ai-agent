"""Today's Opportunities — action-first daily session page."""

from __future__ import annotations

import streamlit as st

from instagram_agent.services.opportunities import (
    HIGH_PRIORITY_THRESHOLD,
    OpportunitiesSessionSummary,
    build_session_summary,
)
from instagram_agent.ui import state
from instagram_agent.ui.components.opportunity_card import render_opportunity_card


def render_opportunities_page() -> None:
    opportunities = state.get_opportunities()
    summary = build_session_summary(opportunities)
    active = [item for item in opportunities if item.status == "active"]
    high = [
        item for item in active if item.opportunity_score >= HIGH_PRIORITY_THRESHOLD
    ]
    lower = [
        item for item in active if item.opportunity_score < HIGH_PRIORITY_THRESHOLD
    ]
    done = [item for item in opportunities if item.status == "done"]
    skipped = [item for item in opportunities if item.status == "skipped"]

    st.title(f"Today's Opportunities ({summary.high_priority_count})")
    st.caption("Finish today's list — small daily sessions build the habit.")

    if not opportunities:
        st.info(
            "No opportunities yet. Go to **Discovery** and run "
            "**Find Similar Creators** to generate today's list."
        )
        st.button(
            "Go to Discovery",
            type="primary",
            on_click=state.request_page,
            args=("Discovery",),
        )
        return

    _render_session_summary(summary)

    if summary.is_session_complete:
        _render_session_complete(summary)
    else:
        st.markdown("### Today summary")
        st.write(summary.today_summary)
        st.divider()

        if high:
            for opportunity in high:
                render_opportunity_card(opportunity)
        else:
            st.success(
                "High-priority cards are cleared. "
                "Open lower priority below, or come back tomorrow."
            )

        st.divider()
        st.toggle(
            "Show Lower Priority Opportunities",
            key="show_lower_priority",
        )
        if st.session_state.show_lower_priority:
            if not lower:
                st.caption("No lower-priority opportunities right now.")
            else:
                for opportunity in lower:
                    render_opportunity_card(opportunity)

    st.divider()
    cols = st.columns(2)
    with cols[0], st.expander(f"Completed ({len(done)})", expanded=False):
        if not done:
            st.caption("Nothing completed yet.")
        else:
            for item in done:
                st.write(
                    f"- {item.creator_name} — {item.estimated_time_label} — "
                    f"score {item.opportunity_score:.0f}"
                )
    with cols[1], st.expander(f"Skipped ({len(skipped)})", expanded=False):
        if not skipped:
            st.caption("Nothing skipped yet.")
        else:
            for item in skipped:
                st.write(f"- {item.creator_name} — score {item.opportunity_score:.0f}")


def _render_session_summary(summary: OpportunitiesSessionSummary) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Today's Opportunities", summary.high_priority_count)
    c2.metric("Estimated Total Time", summary.estimated_total_label)
    c3.metric("Estimated Marketing Impact", summary.estimated_marketing_impact)
    c4.metric("Average Opportunity Score", summary.average_opportunity_score)


def _render_session_complete(summary: OpportunitiesSessionSummary) -> None:
    st.balloons()
    if summary.completed_count > 0:
        st.success(
            "### Great work — session complete!\n\n"
            f"You completed **{summary.completed_count} marketing actions** "
            f"in **{summary.completed_time_label.lstrip('~')}**.\n\n"
            "Come back tomorrow for a fresh list of opportunities."
        )
    else:
        st.success(
            "### List cleared\n\n"
            "Today's opportunities are done for now.\n\n"
            "Come back tomorrow for a fresh list of opportunities."
        )
    st.info(
        "Habit tip: a short daily session beats an occasional long one. "
        "See you tomorrow."
    )
