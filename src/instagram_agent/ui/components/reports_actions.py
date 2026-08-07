"""Report open / download actions."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from instagram_agent.config import get_settings
from instagram_agent.services.workspace import find_latest_artifact, notion_database_url
from instagram_agent.ui import state


def render_reports_actions() -> None:
    settings = get_settings()
    outcome = state.get_outcome()

    md_path = (
        Path(outcome.report_path)
        if outcome and outcome.report_path
        else find_latest_artifact("_report.md", settings.reports_dir)
    )
    csv_path = (
        Path(outcome.csv_path)
        if outcome and outcome.csv_path
        else find_latest_artifact("_research.csv", settings.csv_dir)
    )
    json_path = (
        Path(outcome.json_path)
        if outcome and outcome.json_path
        else find_latest_artifact("_summary.json", settings.reports_dir)
    )
    notion_url = (
        outcome.notion_url
        if outcome and outcome.notion_url
        else notion_database_url(settings)
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _download_or_disabled("Open Markdown", md_path, "text/markdown")
    with c2:
        _download_or_disabled("Open CSV", csv_path, "text/csv")
    with c3:
        _download_or_disabled("Open JSON", json_path, "application/json")
    with c4:
        if notion_url:
            st.link_button("Open Notion", notion_url, use_container_width=True)
        else:
            st.button("Open Notion", disabled=True, use_container_width=True)
            st.caption("Set NOTION_DATABASE_ID in Settings / .env")


def _download_or_disabled(label: str, path: Path | None, mime: str) -> None:
    if path and path.exists():
        st.download_button(
            label,
            data=path.read_text(encoding="utf-8"),
            file_name=path.name,
            mime=mime,
            use_container_width=True,
        )
        st.caption(str(path))
    else:
        st.button(label, disabled=True, use_container_width=True)
