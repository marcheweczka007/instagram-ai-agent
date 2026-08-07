"""Today's Opportunities — action-first daily session page."""

from __future__ import annotations

import streamlit as st

from instagram_agent.services.session_planner import (
    PlannedMarketingSession,
    plan_marketing_session,
)
from instagram_agent.ui import state
from instagram_agent.ui.components.opportunity_card import render_opportunity_card
from instagram_agent.ui.components.time_selector import render_available_time_slider


def render_opportunities_page() -> None:
    opportunities = state.get_opportunities()

    st.title("Today's Opportunities")
    st.caption("AI-planned for your available time — maximising marketing impact.")

    available = render_available_time_slider(
        label="How much time do you have today?",
        help_text=(
            "Drag to set your window (5–60 min). "
            "The AI builds an optimal session — not just the first N cards."
        ),
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

    active = [item for item in opportunities if item.status == "active"]
    done = [item for item in opportunities if item.status == "done"]
    skipped = [item for item in opportunities if item.status == "skipped"]
    plan = plan_marketing_session(opportunities, available_minutes=available)
    planned_ids = {item.id for item in plan.opportunities}
    deferred = [item for item in active if item.id not in planned_ids]

    st.subheader(f"Planned session · {len(plan.opportunities)} opportunities")
    _render_plan_summary(plan)

    if not active:
        _render_session_complete(done_count=len(done), done=done)
    else:
        st.markdown("### Why this session")
        st.write(plan.rationale)
        st.divider()

        if plan.opportunities:
            st.markdown("### Your planned actions")
            for opportunity in plan.opportunities:
                render_opportunity_card(opportunity)
        else:
            st.warning(
                "Nothing fits this time window yet. "
                "Increase available time or run Discovery for more opportunities."
            )

        if deferred:
            st.divider()
            st.toggle(
                f"Show deferred opportunities ({len(deferred)})",
                key="show_lower_priority",
            )
            if st.session_state.show_lower_priority:
                st.caption(
                    "These were deferred because other cards deliver more "
                    "Opportunity Score per minute in your window."
                )
                for opportunity in deferred:
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


def _render_plan_summary(plan: PlannedMarketingSession) -> None:
    example = st.container(border=True)
    with example:
        st.markdown(
            f"**Available:** {plan.available_minutes} min  \n"
            f"**Planned:** {plan.planned_minutes} min  \n"
            f"**Buffer:** {plan.buffer_minutes} min  \n"
            f"**Estimated Impact:** {plan.impact_stars}"
        )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Estimated Session Time", f"{plan.planned_minutes} min")
    c2.metric("Estimated Marketing Impact", plan.impact_stars)
    c3.metric("Number of Opportunities", len(plan.opportunities))
    c4.metric("Unused Buffer Time", f"{plan.buffer_minutes} min")
    st.caption(
        f"{plan.estimated_marketing_impact} impact · "
        f"total Opportunity Score {plan.total_opportunity_score:.0f}"
    )


def _render_session_complete(*, done_count: int, done: list) -> None:
    st.balloons()
    minutes = sum(max(1, (item.estimated_time_seconds + 59) // 60) for item in done)
    if done_count > 0:
        st.success(
            "### Great work — session complete!\n\n"
            f"You completed **{done_count} marketing actions** "
            f"in about **{minutes} min**.\n\n"
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
