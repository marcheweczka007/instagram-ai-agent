"""Outreach / DMs page."""

from __future__ import annotations

import streamlit as st

from instagram_agent.ui import state
from instagram_agent.ui.components.outreach_card import render_outreach_cards


def render_outreach_page() -> None:
    st.title("Outreach")
    st.caption("Suggested DMs for collaboration outreach")
    render_outreach_cards(state.get_creators())
