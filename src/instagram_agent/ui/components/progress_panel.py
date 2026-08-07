"""Live session progress panel."""

from __future__ import annotations

import streamlit as st

from instagram_agent.services.marketing_session import SessionProgress
from instagram_agent.ui import state


def _format_eta(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    if minutes <= 0:
        return f"{secs}s"
    return f"{minutes}m {secs}s"


def render_progress_panel() -> None:
    progress: SessionProgress = state.get_progress()

    st.subheader("Session progress")
    st.write(f"**Current task:** {progress.current_task}")

    total = max(progress.total, 1) if progress.total or progress.is_running else 1
    ratio = (
        min(progress.analysed / total, 1.0)
        if progress.total
        else (1.0 if progress.is_complete else 0.0)
    )
    st.progress(ratio, text=f"{progress.analysed} / {progress.total or '—'} analysed")

    c1, c2 = st.columns(2)
    c1.metric("Number analysed", progress.analysed)
    c2.metric(
        "Estimated time remaining", _format_eta(progress.estimated_remaining_seconds)
    )

    if progress.error:
        st.error(progress.error)

    with st.expander("Logs", expanded=progress.is_running or bool(progress.logs)):
        if not progress.logs:
            st.caption("Logs will appear when a session starts.")
        else:
            st.code("\n".join(progress.logs[-80:]), language="text")
