"""Dashboard statistics metrics."""

from __future__ import annotations

import streamlit as st

from instagram_agent.services.workspace import DashboardSnapshot


def render_dashboard_stats(snapshot: DashboardSnapshot) -> None:
    st.subheader("Today's statistics")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Creators analysed", snapshot.creators_analysed)
    c2.metric("High priority creators", snapshot.high_priority)
    c3.metric("Comments ready", snapshot.comments_ready)
    c4.metric("DMs ready", snapshot.dms_ready)

    st.progress(
        min(snapshot.weekly_progress / max(snapshot.weekly_goal, 1), 1.0),
        text=(
            f"Weekly goal: {snapshot.weekly_progress} / {snapshot.weekly_goal} creators"
        ),
    )
    st.caption(
        f"Estimated remaining outreach work: "
        f"{snapshot.estimated_work_minutes:.0f} minutes"
    )
