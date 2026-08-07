"""Settings page — session preferences (no business logic)."""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from instagram_agent.config import get_settings


def render_settings_page() -> None:
    st.title("Settings")
    st.caption("Workspace preferences for this session")

    model = st.text_input("OpenAI model", key="setting_openai_model")
    notion_enabled = st.toggle("Notion enabled", key="setting_notion_enabled")
    headless = st.toggle("Headless browser", key="setting_headless_browser")
    output_dir = st.text_input("Output directory", key="setting_output_dir")
    weekly_goal = st.number_input(
        "Weekly creator goal",
        min_value=1,
        max_value=200,
        value=int(st.session_state.weekly_goal),
        step=1,
    )
    st.session_state.weekly_goal = int(weekly_goal)

    if st.button("Save settings", type="primary"):
        os.environ["OPENAI_MODEL"] = model.strip() or get_settings().openai_model
        os.environ["NOTION_ENABLED"] = "true" if notion_enabled else "false"
        os.environ["BROWSER_HEADLESS"] = "true" if headless else "false"
        if output_dir.strip():
            path = Path(output_dir.strip())
            path.mkdir(parents=True, exist_ok=True)
            os.environ["OUTPUT_DIR"] = str(path)
        get_settings.cache_clear()
        st.session_state.settings_saved_message = "Settings saved for this session."
        st.success(st.session_state.settings_saved_message)

    if st.session_state.settings_saved_message and not st.session_state.get(
        "_settings_just_shown"
    ):
        # Keep last save note visible until next save.
        pass

    st.divider()
    current = get_settings()
    st.markdown("**Active configuration**")
    st.code(
        "\n".join(
            [
                f"OPENAI_MODEL={current.openai_model}",
                f"NOTION_ENABLED={current.notion_enabled}",
                f"NOTION_DATABASE_ID={'set' if current.notion_database_id else 'missing'}",
                f"OUTPUT_DIR={current.output_dir}",
                f"BROWSER_HEADLESS={os.getenv('BROWSER_HEADLESS', 'true')}",
                f"WEEKLY_GOAL={st.session_state.weekly_goal}",
            ]
        ),
        language="text",
    )
    st.caption(
        "Headless browser is stored as a preference. "
        "Persist permanently by updating your `.env` file."
    )
