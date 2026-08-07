"""Streamlit marketing workspace — page router only."""

from __future__ import annotations

import streamlit as st

from instagram_agent.ui import state
from instagram_agent.ui.components.sidebar import render_sidebar
from instagram_agent.ui.pages.creators import render_creators_page
from instagram_agent.ui.pages.discover import render_discover_page
from instagram_agent.ui.pages.opportunities import render_opportunities_page
from instagram_agent.ui.pages.reports import render_reports_page
from instagram_agent.ui.pages.settings import render_settings_page

_PAGE_RENDERERS = {
    "Today's Opportunities": render_opportunities_page,
    "Creators": render_creators_page,
    "Discovery": render_discover_page,
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
    renderer = _PAGE_RENDERERS.get(page, render_opportunities_page)
    renderer()
