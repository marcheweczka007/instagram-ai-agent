"""Top statistics bar."""

from __future__ import annotations

import streamlit as st

from instagram_agent.services.marketing_session import session_stats
from instagram_agent.ui import state


def render_top_bar() -> None:
    outcome = state.get_outcome()
    progress = state.get_progress()
    results = outcome.results if outcome is not None else progress.results
    stats = session_stats(results)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Creators analysed", stats["creators_analysed"])
    c2.metric("Average Brand Fit", stats["average_brand_fit"])
    c3.metric("High priority creators", stats["high_priority"])
    c4.metric("New creators", stats["new_creators"])
