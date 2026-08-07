"""Greeting and high-impact task list."""

from __future__ import annotations

import streamlit as st

from instagram_agent.services.workspace import DashboardSnapshot


def render_greeting(snapshot: DashboardSnapshot) -> None:
    st.title(f"{snapshot.greeting}")
    st.caption("Your daily marketing workspace")


def render_impact_tasks(snapshot: DashboardSnapshot) -> None:
    st.subheader("Today's highest impact tasks")
    if not snapshot.tasks:
        st.info("Run Discover or a marketing session to generate tasks.")
        return

    for task in snapshot.tasks:
        st.markdown(
            f"{task.rank}. **{task.action} on {task.creator_name}**  \n{task.detail}"
        )
    st.write(f"Estimated work time: **{snapshot.estimated_work_minutes:.0f} minutes**")
