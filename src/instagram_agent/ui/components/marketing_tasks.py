"""Post-session marketing task list."""

from __future__ import annotations

import streamlit as st

from instagram_agent.ui import state


def render_marketing_tasks() -> None:
    outcome = state.get_outcome()
    if outcome is None or not outcome.tasks:
        return

    st.subheader("Today's Marketing Tasks")
    for task in outcome.tasks:
        st.markdown(
            f"{task.rank}. **{task.action} on {task.creator_name}**  \n{task.detail}"
        )
    st.info(
        f"Estimated remaining time: **{outcome.tasks_estimated_minutes:.0f} minutes**"
    )
