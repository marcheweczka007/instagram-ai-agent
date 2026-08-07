"""Creator database cards."""

from __future__ import annotations

import streamlit as st

from instagram_agent.domain.models import BrandResearchResult
from instagram_agent.services.marketing_session import (
    build_ai_notes,
    priority_from_brand_fit,
)


def render_creator_cards(
    results: list[BrandResearchResult],
    *,
    notion_saved: list[str] | None = None,
) -> None:
    if not results:
        st.info("No creators yet. Run Discover to populate the database.")
        return

    saved = set(notion_saved or [])
    for index, result in enumerate(results):
        _card(result, index=index, saved=result.profile.name in saved)


def _card(result: BrandResearchResult, *, index: int, saved: bool) -> None:
    priority = priority_from_brand_fit(result.research.brand_fit)
    with st.container(border=True):
        head = st.columns([3, 1])
        head[0].markdown(f"### {result.profile.name}")
        head[1].markdown(f"**{priority}**")

        meta = st.columns(4)
        meta[0].write(f"Followers: **{result.profile.followers:,}**")
        meta[1].write(f"Brand Fit: **{result.research.brand_fit}/10**")
        meta[2].write(f"Priority: **{priority}**")
        meta[3].write("Status: **New**")

        if saved:
            st.success("Saved to Notion")

        actions = st.columns(3)
        actions[0].link_button(
            "Open Instagram",
            result.profile.profile_url,
            use_container_width=True,
        )
        with actions[1]:
            if st.button(
                "Copy Comment", key=f"db_copy_comment_{index}", use_container_width=True
            ):
                st.session_state[f"db_show_comment_{index}"] = True
        with actions[2]:
            if st.button(
                "Copy DM", key=f"db_copy_dm_{index}", use_container_width=True
            ):
                st.session_state[f"db_show_dm_{index}"] = True

        if st.session_state.get(f"db_show_comment_{index}"):
            st.caption("Comment — use the copy icon")
            st.code(result.analysis.comment or "(empty)", language=None)
        if st.session_state.get(f"db_show_dm_{index}"):
            st.caption("DM — use the copy icon")
            st.code(result.research.first_outreach_angle or "(empty)", language=None)

        if st.checkbox("Expand", key=f"db_expand_{index}"):
            st.markdown("**Research summary**")
            st.write(result.research.overall_summary)

            left, right = st.columns(2)
            with left:
                st.markdown("**Strengths**")
                _bullets(result.research.strengths)
            with right:
                st.markdown("**Weaknesses**")
                _bullets(result.research.weaknesses)

            st.markdown("**Collaboration ideas**")
            _bullets(result.research.collaboration_ideas)

            st.markdown("**AI Notes**")
            st.write(build_ai_notes(result.research))


def _bullets(items: list[str]) -> None:
    if not items:
        st.caption("None listed")
        return
    for item in items:
        st.write(f"- {item}")
