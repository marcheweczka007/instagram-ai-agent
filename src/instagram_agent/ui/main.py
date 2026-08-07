"""Streamlit owner console entry composition."""

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
from instagram_agent.ui.components.marketing_tasks import render_marketing_tasks
from instagram_agent.ui.components.progress_panel import render_progress_panel
from instagram_agent.ui.components.reports_bar import render_reports_bar
from instagram_agent.ui.components.result_cards import render_result_cards
from instagram_agent.ui.components.sidebar import render_sidebar
from instagram_agent.ui.components.top_bar import render_top_bar

logger = logging.getLogger(__name__)


def render_app() -> None:
    st.set_page_config(
        page_title="Instagram Brand Research",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    state.init_state()

    options = render_sidebar()
    page = st.session_state.nav_page

    st.title("Instagram Brand Research Assistant")
    st.caption("Owner console")

    if page != "Marketing Session":
        st.info(
            f"**{page}** is reserved for a future release. "
            "Use Marketing Session for now."
        )
        render_top_bar()
        return

    if options is not None:
        _run_session(options)

    render_top_bar()
    st.divider()
    render_progress_panel()
    st.divider()

    progress = state.get_progress()
    outcome = state.get_outcome()
    results = outcome.results if outcome is not None else progress.results
    notion_saved = progress.notion_saved_names
    render_result_cards(results, notion_saved=notion_saved)
    st.divider()
    render_reports_bar()
    render_marketing_tasks()


def _run_session(options: SessionOptions) -> None:
    if not options.brand_instagram_url.strip():
        st.error("Enter a Brand Instagram URL before starting.")
        return

    state.set_outcome(None)
    state.set_progress(
        SessionProgress(is_running=True, current_task="Starting session…")
    )

    status = st.status("Running marketing session…", expanded=True)
    live = st.empty()

    def on_progress(progress: SessionProgress) -> None:
        state.set_progress(progress)
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
        service = MarketingSessionService()
        outcome = asyncio.run(service.run(options, on_progress=on_progress))
        state.set_outcome(outcome)
        state.set_progress(outcome.progress)
        status.update(label="Session complete", state="complete")
        st.toast(f"Finished — {len(outcome.results)} creators analysed")
    except Exception as exc:
        logger.exception("Marketing session failed")
        progress = state.get_progress()
        progress.is_running = False
        progress.is_complete = True
        progress.error = f"{type(exc).__name__}: {exc}"
        progress.current_task = "Session failed"
        state.set_progress(progress)
        status.update(label="Session failed", state="error")
        st.error(progress.error)
