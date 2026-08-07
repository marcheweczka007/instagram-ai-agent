"""Session-state helpers for the Streamlit owner console."""

from __future__ import annotations

from typing import Any

import streamlit as st

from instagram_agent.services.marketing_session import SessionOutcome, SessionProgress

_DEFAULT_BRAND_URL = "https://www.instagram.com/upcycle.lab.jollyzu/"


def init_state() -> None:
    defaults: dict[str, Any] = {
        "nav_page": "Marketing Session",
        "brand_instagram_url": _DEFAULT_BRAND_URL,
        "opt_discover": True,
        "opt_research": True,
        "opt_comments": True,
        "opt_outreach": True,
        "opt_notion": True,
        "opt_markdown": True,
        "opt_csv": True,
        "duration_minutes": 30,
        "progress": SessionProgress(),
        "outcome": None,
        "expanded_creators": set(),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_progress() -> SessionProgress:
    return st.session_state.progress


def set_progress(progress: SessionProgress) -> None:
    st.session_state.progress = progress


def get_outcome() -> SessionOutcome | None:
    return st.session_state.outcome


def set_outcome(outcome: SessionOutcome | None) -> None:
    st.session_state.outcome = outcome
