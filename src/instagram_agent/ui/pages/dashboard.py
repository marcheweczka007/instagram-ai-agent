"""Dashboard home page."""

from __future__ import annotations

import streamlit as st

from instagram_agent.services.workspace import build_dashboard_snapshot
from instagram_agent.ui import state
from instagram_agent.ui.components.dashboard_stats import render_dashboard_stats
from instagram_agent.ui.components.greeting import render_greeting, render_impact_tasks


def render_dashboard_page() -> None:
    snapshot = build_dashboard_snapshot(
        state.get_creators(),
        weekly_goal=int(st.session_state.weekly_goal),
    )
    render_greeting(snapshot)
    render_dashboard_stats(snapshot)

    st.divider()
    col, _ = st.columns([1, 2])
    with col:
        st.button(
            "Start Marketing Session",
            type="primary",
            use_container_width=True,
            on_click=state.request_page,
            args=("Discover",),
        )

    st.divider()
    render_impact_tasks(snapshot)
