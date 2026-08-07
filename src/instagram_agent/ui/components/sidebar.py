"""Sidebar navigation for the action-oriented marketing workspace."""

from __future__ import annotations

import streamlit as st

from instagram_agent.ui import state
from instagram_agent.ui.state import PAGES


def render_sidebar() -> str:
    high_count = state.high_priority_active_count()

    def _label(page: str) -> str:
        if page == "Today's Opportunities":
            return f"Today's Opportunities ({high_count})"
        return page

    with st.sidebar:
        st.header("Marketing Workspace")
        st.caption("Do the next high-impact action")
        page = st.radio(
            "Navigate",
            options=list(PAGES),
            format_func=_label,
            key="nav_page",
        )
        st.divider()
        st.caption("Highest-impact opportunities first.")

    return page
