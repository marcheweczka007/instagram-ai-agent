"""Report / export open actions."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from instagram_agent.ui import state


def render_reports_bar() -> None:
    outcome = state.get_outcome()
    st.subheader("Reports")
    if outcome is None:
        st.caption("Export buttons appear after a session finishes.")
        return

    c1, c2, c3 = st.columns(3)
    with c1:
        if outcome.report_path and Path(outcome.report_path).exists():
            st.download_button(
                "Open Markdown Report",
                data=Path(outcome.report_path).read_text(encoding="utf-8"),
                file_name=Path(outcome.report_path).name,
                mime="text/markdown",
                use_container_width=True,
            )
            st.caption(str(outcome.report_path))
        else:
            st.button("Open Markdown Report", disabled=True, use_container_width=True)

    with c2:
        if outcome.csv_path and Path(outcome.csv_path).exists():
            st.download_button(
                "Open CSV",
                data=Path(outcome.csv_path).read_text(encoding="utf-8"),
                file_name=Path(outcome.csv_path).name,
                mime="text/csv",
                use_container_width=True,
            )
            st.caption(str(outcome.csv_path))
        else:
            st.button("Open CSV", disabled=True, use_container_width=True)

    with c3:
        if outcome.notion_url:
            st.link_button("Open Notion", outcome.notion_url, use_container_width=True)
        else:
            st.button("Open Notion", disabled=True, use_container_width=True)
            st.caption("Configure NOTION_* in .env to enable")
