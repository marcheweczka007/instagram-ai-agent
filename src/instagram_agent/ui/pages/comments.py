"""Comments page."""

from __future__ import annotations

import streamlit as st

from instagram_agent.ui import state
from instagram_agent.ui.components.comment_card import render_comment_cards


def render_comments_page() -> None:
    st.title("Comments")
    st.caption("Ready-to-post comments for today's creators")
    render_comment_cards(state.get_creators())
