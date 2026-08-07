"""Today's Opportunities — default action landing page."""

from __future__ import annotations

import streamlit as st

from instagram_agent.services.opportunities import HIGH_PRIORITY_THRESHOLD
from instagram_agent.ui import state
from instagram_agent.ui.components.opportunity_card import render_opportunity_card


def render_opportunities_page() -> None:
    opportunities = state.get_opportunities()
    active = [item for item in opportunities if item.status == "active"]
    high = [
        item
        for item in active
        if item.opportunity_score >= HIGH_PRIORITY_THRESHOLD
    ]
    lower = [
        item
        for item in active
        if item.opportunity_score < HIGH_PRIORITY_THRESHOLD
    ]
    done = [item for item in opportunities if item.status == "done"]
    skipped = [item for item in opportunities if item.status == "skipped"]

    st.title(f"Today's Opportunities ({len(high)})")
    st.caption(
        "Highest-impact comment actions first — sorted by Opportunity Score, "
        "not Brand Fit alone."
    )

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

    if high:
        for opportunity in high:
            render_opportunity_card(opportunity)
    else:
        st.success("No high-priority opportunities left. Nice work.")

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
                    f"- {item.creator_name} — score {item.opportunity_score:.0f}"
                )
    with cols[1], st.expander(f"Skipped ({len(skipped)})", expanded=False):
        if not skipped:
            st.caption("Nothing skipped yet.")
        else:
            for item in skipped:
                st.write(
                    f"- {item.creator_name} — score {item.opportunity_score:.0f}"
                )
