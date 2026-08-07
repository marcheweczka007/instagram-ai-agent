"""Streamlit marketing workspace — page router only."""

from __future__ import annotations

import streamlit as st

from instagram_agent.ui import state
from instagram_agent.ui.components.sidebar import render_sidebar
from instagram_agent.ui.pages.comments import render_comments_page
from instagram_agent.ui.pages.creators import render_creators_page
from instagram_agent.ui.pages.dashboard import render_dashboard_page
from instagram_agent.ui.pages.discover import render_discover_page
from instagram_agent.ui.pages.outreach import render_outreach_page
from instagram_agent.ui.pages.reports import render_reports_page
from instagram_agent.ui.pages.settings import render_settings_page

_PAGE_RENDERERS = {
    "Dashboard": render_dashboard_page,
    "Discover": render_discover_page,
    "Creator Database": render_creators_page,
    "Comments": render_comments_page,
    "Outreach": render_outreach_page,
    "Reports": render_reports_page,
    "Settings": render_settings_page,
}


def render_app() -> None:
    st.set_page_config(
        page_title="Marketing Workspace",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    state.init_state()
    page = render_sidebar()
    renderer = _PAGE_RENDERERS.get(page, render_dashboard_page)
    renderer()
