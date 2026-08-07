"""Sidebar controls for configuring a marketing session."""

from __future__ import annotations

import streamlit as st

from instagram_agent.services.marketing_session import SessionOptions
from instagram_agent.ui import state


def render_sidebar() -> SessionOptions | None:
    """Render sidebar controls. Returns options when Start is clicked."""
    with st.sidebar:
        st.header("Marketing Session")
        st.caption("Owner console — productivity first")

        brand_url = st.text_input(
            "Brand Instagram URL",
            key="brand_instagram_url",
        )

        st.subheader("Workflow")
        discover = st.checkbox("Discover creators", value=st.session_state.opt_discover)
        research = st.checkbox("Research", value=st.session_state.opt_research)
        comments = st.checkbox("Generate comments", value=st.session_state.opt_comments)
        outreach = st.checkbox("Generate outreach", value=st.session_state.opt_outreach)
        export_notion = st.checkbox(
            "Export to Notion", value=st.session_state.opt_notion
        )
        export_markdown = st.checkbox(
            "Export Markdown report", value=st.session_state.opt_markdown
        )
        export_csv = st.checkbox("Export CSV", value=st.session_state.opt_csv)

        st.session_state.opt_discover = discover
        st.session_state.opt_research = research
        st.session_state.opt_comments = comments
        st.session_state.opt_outreach = outreach
        st.session_state.opt_notion = export_notion
        st.session_state.opt_markdown = export_markdown
        st.session_state.opt_csv = export_csv

        st.subheader("Marketing Session")
        duration = st.radio(
            "Duration",
            options=[15, 30, 60],
            index=[15, 30, 60].index(st.session_state.duration_minutes),
            format_func=lambda minutes: {
                15: "15 minutes",
                30: "30 minutes",
                60: "1 hour",
            }[minutes],
            horizontal=False,
        )
        st.session_state.duration_minutes = duration

        started = st.button(
            "Start Marketing Session",
            type="primary",
            use_container_width=True,
            disabled=state.get_progress().is_running,
        )

        st.divider()
        st.caption("Future modules")
        st.radio(
            "Navigate",
            options=[
                "Marketing Session",
                "Dashboard (soon)",
                "Content planner (soon)",
                "Weekly report (soon)",
                "Trend analysis (soon)",
            ],
            key="nav_page",
            label_visibility="collapsed",
        )

    if not started:
        return None

    return SessionOptions(
        brand_instagram_url=brand_url.strip(),
        discover=discover,
        research=research,
        generate_comments=comments,
        generate_outreach=outreach,
        export_notion=export_notion,
        export_markdown=export_markdown,
        export_csv=export_csv,
        duration_minutes=int(duration),
    )
