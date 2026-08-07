"""Sidebar navigation for the marketing workspace."""

from __future__ import annotations

import streamlit as st

from instagram_agent.ui.state import PAGES


def render_sidebar() -> str:
    with st.sidebar:
        st.header("Marketing Workspace")
        st.caption("Daily creator research console")
        page = st.radio("Navigate", options=PAGES, key="nav_page")
        st.divider()
        st.caption("Tip: start on Dashboard, then Discover.")
    return page
