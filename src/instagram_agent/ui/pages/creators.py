"""Creator database page."""

from __future__ import annotations

import streamlit as st

from instagram_agent.ui import state
from instagram_agent.ui.components.creator_card import render_creator_cards


def render_creators_page() -> None:
    st.title("Creator Database")
    st.caption("All analysed creators from this workspace")

    progress = state.get_progress()
    render_creator_cards(
        state.get_creators(),
        notion_saved=progress.notion_saved_names,
    )
