"""Shared available-time slider (5–60 min, step 5)."""

from __future__ import annotations

import streamlit as st


def render_available_time_slider(
    *,
    label: str = "Available time",
    help_text: str | None = None,
    key: str = "duration_minutes",
) -> int:
    """Render the session time selector and return the chosen minutes."""
    return int(
        st.slider(
            label,
            min_value=5,
            max_value=60,
            value=int(st.session_state.get(key, 30)),
            step=5,
            format="%d min",
            help=help_text
            or "How much time do you have? The AI will plan the highest-impact session.",
            key=key,
        )
    )
