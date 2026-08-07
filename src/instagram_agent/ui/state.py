"""Session-state helpers for the marketing workspace."""

from __future__ import annotations

from typing import Any

import streamlit as st

from instagram_agent.config import get_settings
from instagram_agent.domain.models import BrandResearchResult, CommentOpportunity
from instagram_agent.services.marketing_session import SessionOutcome, SessionProgress
from instagram_agent.services.opportunities import HIGH_PRIORITY_THRESHOLD
from instagram_agent.services.workspace import (
    DEFAULT_WEEKLY_GOAL,
    load_latest_results,
)

PAGES = (
    "Today's Opportunities",
    "Creators",
    "Discovery",
    "Reports",
    "Settings",
)

_DEFAULT_BRAND_URL = "https://www.instagram.com/upcycle.lab.jollyzu/"
_PENDING_NAV_KEY = "pending_nav_page"


def init_state() -> None:
    settings = get_settings()
    defaults: dict[str, Any] = {
        "nav_page": "Today's Opportunities",
        "brand_instagram_url": _DEFAULT_BRAND_URL,
        "duration_minutes": 30,
        "weekly_goal": DEFAULT_WEEKLY_GOAL,
        "progress": SessionProgress(),
        "outcome": None,
        "creators": [],
        "opportunities": [],
        "show_lower_priority": False,
        "setting_openai_model": settings.openai_model,
        "setting_notion_enabled": settings.notion_enabled,
        "setting_headless_browser": True,
        "setting_output_dir": str(settings.output_dir),
        "settings_saved_message": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Migrate old default page name if present from earlier builds.
    if st.session_state.nav_page in {
        "Dashboard",
        "Discover",
        "Creator Database",
        "Comments",
        "Outreach",
    }:
        st.session_state.nav_page = "Today's Opportunities"

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
        st.session_state.opportunities = [
            item.model_copy(deep=True) for item in outcome.opportunities
        ]
        # Land on the action list after a successful discovery/research run.
        request_page("Today's Opportunities")


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


def get_opportunities() -> list[CommentOpportunity]:
    return list(st.session_state.opportunities or [])


def set_opportunities(items: list[CommentOpportunity]) -> None:
    st.session_state.opportunities = [
        item.model_copy(deep=True) if isinstance(item, CommentOpportunity) else item
        for item in items
    ]


def high_priority_active_count() -> int:
    return sum(
        1
        for item in get_opportunities()
        if item.status == "active" and item.opportunity_score >= HIGH_PRIORITY_THRESHOLD
    )


def mark_opportunity_done(opportunity_id: str) -> None:
    _set_opportunity_status(opportunity_id, "done")


def skip_opportunity(opportunity_id: str) -> None:
    _set_opportunity_status(opportunity_id, "skipped")


def _set_opportunity_status(opportunity_id: str, status: str) -> None:
    updated: list[CommentOpportunity] = []
    for item in get_opportunities():
        if item.id == opportunity_id:
            updated.append(item.model_copy(update={"status": status}))
        else:
            updated.append(item)
    set_opportunities(updated)
