"""Reports page."""

from __future__ import annotations

import streamlit as st

from instagram_agent.ui.components.reports_actions import render_reports_actions


def render_reports_page() -> None:
    st.title("Reports")
    st.caption("Open the latest research exports")
    render_reports_actions()
