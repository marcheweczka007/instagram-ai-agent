"""Session-state helpers for the marketing workspace dashboard."""

from __future__ import annotations

from typing import Any

import streamlit as st

from instagram_agent.config import get_settings
from instagram_agent.domain.models import BrandResearchResult
from instagram_agent.services.marketing_session import SessionOutcome, SessionProgress
from instagram_agent.services.workspace import (
    DEFAULT_WEEKLY_GOAL,
    load_latest_results,
)

PAGES = (
    "Dashboard",
    "Discover",
    "Creator Database",
    "Comments",
    "Outreach",
    "Reports",
    "Settings",
)

_DEFAULT_BRAND_URL = "https://www.instagram.com/upcycle.lab.jollyzu/"
_PENDING_NAV_KEY = "pending_nav_page"


def init_state() -> None:
    settings = get_settings()
    defaults: dict[str, Any] = {
        "nav_page": "Dashboard",
        "brand_instagram_url": _DEFAULT_BRAND_URL,
        "duration_minutes": 30,
        "weekly_goal": DEFAULT_WEEKLY_GOAL,
        "progress": SessionProgress(),
        "outcome": None,
        "creators": [],
        "setting_openai_model": settings.openai_model,
        "setting_notion_enabled": settings.notion_enabled,
        "setting_headless_browser": True,
        "setting_output_dir": str(settings.output_dir),
        "settings_saved_message": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Apply queued navigation before any widget with key="nav_page" is created.
    apply_pending_navigation()

    if not st.session_state.creators:
        st.session_state.creators = load_latest_results()


def request_page(page: str) -> None:
    """Queue a page change safely (call from button on_click callbacks)."""
    if page not in PAGES:
        raise ValueError(f"Unknown page: {page}")
    st.session_state[_PENDING_NAV_KEY] = page


def apply_pending_navigation() -> None:
    """Copy pending_nav_page → nav_page before the sidebar radio is rendered."""
    pending = st.session_state.pop(_PENDING_NAV_KEY, None)
    if pending is None:
        return
    if pending in PAGES:
        st.session_state.nav_page = pending


def get_progress() -> SessionProgress:
    return st.session_state.progress


def set_progress(progress: SessionProgress) -> None:
    st.session_state.progress = progress


def get_outcome() -> SessionOutcome | None:
    return st.session_state.outcome


def set_outcome(outcome: SessionOutcome | None) -> None:
    st.session_state.outcome = outcome
    if outcome is not None:
        st.session_state.creators = list(outcome.results)


def get_creators() -> list[BrandResearchResult]:
    creators: list[BrandResearchResult] = list(st.session_state.creators or [])
    if creators:
        return creators
    progress = get_progress()
    if progress.results:
        return list(progress.results)
    return []


def set_creators(results: list[BrandResearchResult]) -> None:
    st.session_state.creators = list(results)
