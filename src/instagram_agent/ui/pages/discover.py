"""Discovery page — find similar creators and build opportunities."""

from __future__ import annotations

import streamlit as st

from instagram_agent.services.marketing_session import SessionOptions
from instagram_agent.ui import state
from instagram_agent.ui.components.progress_logs import render_progress_logs
from instagram_agent.ui.components.session_runner import run_marketing_session


def render_discover_page() -> None:
    st.title("Discovery")
    st.caption("Find similar creators, then jump straight into today's actions")

    brand_url = st.text_input(
        "Brand Instagram URL",
        key="brand_instagram_url",
    )
    duration = st.select_slider(
        "Session length",
        options=[15, 30, 60],
        value=st.session_state.duration_minutes,
        format_func=lambda m: {15: "15 minutes", 30: "30 minutes", 60: "1 hour"}[m],
    )
    st.session_state.duration_minutes = duration

    started = st.button(
        "Find Similar Creators",
        type="primary",
        disabled=state.get_progress().is_running,
    )

    if started:
        options = SessionOptions(
            brand_instagram_url=brand_url.strip(),
            discover=True,
            research=True,
            generate_comments=True,
            generate_outreach=True,
            export_notion=bool(st.session_state.setting_notion_enabled),
            export_markdown=True,
            export_csv=True,
            duration_minutes=int(duration),
        )
        run_marketing_session(options, label="Finding similar creators…")
        if state.get_outcome() is not None and not state.get_progress().error:
            st.rerun()

    st.divider()
    render_progress_logs()
