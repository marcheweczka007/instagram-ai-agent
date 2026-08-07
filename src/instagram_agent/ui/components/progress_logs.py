"""Live progress + log panel used by Discover."""

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


def render_progress_logs() -> None:
    progress: SessionProgress = state.get_progress()
    st.subheader("Progress")
    st.write(f"**Current task:** {progress.current_task}")

    if progress.total:
        ratio = min(progress.analysed / max(progress.total, 1), 1.0)
        st.progress(ratio, text=f"{progress.analysed} / {progress.total}")
    elif progress.is_complete:
        st.progress(1.0, text="Complete")
    else:
        st.progress(0.0, text="Waiting")

    c1, c2 = st.columns(2)
    c1.metric("Analysed", progress.analysed)
    c2.metric("ETA", _format_eta(progress.estimated_remaining_seconds))

    if progress.error:
        st.error(progress.error)

    if progress.notion_saved_names:
        st.success(f"Saved to Notion: {progress.notion_saved_names[-1]}")

    with st.expander("Live logs", expanded=True):
        if not progress.logs:
            st.caption("Logs appear when a discovery run starts.")
        else:
            st.code("\n".join(progress.logs[-100:]), language="text")
