"""Shared helper to run MarketingSessionService from Streamlit pages."""

from __future__ import annotations

import asyncio
import logging

import streamlit as st

from instagram_agent.services.marketing_session import (
    MarketingSessionService,
    SessionOptions,
    SessionProgress,
)
from instagram_agent.ui import state

logger = logging.getLogger(__name__)


def run_marketing_session(options: SessionOptions, *, label: str) -> None:
    """Execute a session and store outcome/creators in session state."""
    if not options.brand_instagram_url.strip():
        st.error("Enter a Brand Instagram URL first.")
        return

    state.set_outcome(None)
    state.set_progress(SessionProgress(is_running=True, current_task="Starting…"))

    status = st.status(label, expanded=True)
    live = st.empty()

    def on_progress(progress: SessionProgress) -> None:
        state.set_progress(progress)
        if progress.results:
            state.set_creators(progress.results)
        with live.container():
            st.write(progress.current_task)
            if progress.total:
                st.progress(
                    min(progress.analysed / max(progress.total, 1), 1.0),
                    text=f"{progress.analysed}/{progress.total}",
                )
            if progress.notion_saved_names:
                st.success(f"Saved to Notion: {progress.notion_saved_names[-1]}")
            if progress.logs:
                st.caption(progress.logs[-1])

    try:
        outcome = asyncio.run(
            MarketingSessionService().run(options, on_progress=on_progress)
        )
        state.set_outcome(outcome)
        state.set_progress(outcome.progress)
        state.set_creators(outcome.results)
        status.update(label="Complete", state="complete")
        st.toast(f"Finished — {len(outcome.results)} creators")
    except Exception as exc:
        logger.exception("Session failed")
        progress = state.get_progress()
        progress.is_running = False
        progress.is_complete = True
        progress.error = f"{type(exc).__name__}: {exc}"
        progress.current_task = "Failed"
        state.set_progress(progress)
        status.update(label="Failed", state="error")
        st.error(progress.error)
