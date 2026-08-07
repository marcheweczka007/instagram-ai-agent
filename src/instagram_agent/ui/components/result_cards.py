"""Creator result cards."""

from __future__ import annotations

import streamlit as st

from instagram_agent.domain.models import BrandResearchResult
from instagram_agent.services.marketing_session import (
    build_ai_notes,
    priority_from_brand_fit,
)


def render_result_cards(
    results: list[BrandResearchResult], *, notion_saved: list[str]
) -> None:
    st.subheader("Results")
    if not results:
        st.caption("Creator cards will appear here after analysis.")
        return

    saved = set(notion_saved)
    for index, result in enumerate(results):
        _render_card(result, index=index, saved_to_notion=result.profile.name in saved)


def _render_card(
    result: BrandResearchResult,
    *,
    index: int,
    saved_to_notion: bool,
) -> None:
    priority = priority_from_brand_fit(result.research.brand_fit)
    with st.container(border=True):
        top = st.columns([3, 1])
        top[0].markdown(f"### {result.profile.name}")
        top[1].markdown(f"**Priority:** {priority}")

        meta = st.columns(4)
        meta[0].write(f"Followers: **{result.profile.followers:,}**")
        meta[1].write(f"Brand Fit: **{result.research.brand_fit}/10**")
        meta[2].write(f"Confidence: **{result.research.confidence}/10**")
        meta[3].write("Status: **New**")

        st.markdown(f"[Instagram profile]({result.profile.profile_url})")
        if saved_to_notion:
            st.success("Saved to Notion")

        actions = st.columns(3)
        actions[0].link_button(
            "Open Instagram",
            result.profile.profile_url,
            use_container_width=True,
        )
        with actions[1]:
            if st.button(
                "Copy Comment", key=f"copy_comment_{index}", use_container_width=True
            ):
                st.session_state[f"show_comment_{index}"] = True
        with actions[2]:
            if st.button("Copy DM", key=f"copy_dm_{index}", use_container_width=True):
                st.session_state[f"show_dm_{index}"] = True

        if st.session_state.get(f"show_comment_{index}"):
            st.caption("Suggested comment — use the copy icon")
            st.code(result.analysis.comment or "(empty)", language=None)

        if st.session_state.get(f"show_dm_{index}"):
            st.caption("Suggested DM — use the copy icon")
            st.code(result.research.first_outreach_angle or "(empty)", language=None)

        expanded = st.checkbox("Expand", key=f"expand_{index}")
        if expanded:
            st.markdown("**Overall summary**")
            st.write(result.research.overall_summary)

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Strengths**")
                if result.research.strengths:
                    for item in result.research.strengths:
                        st.write(f"- {item}")
                else:
                    st.caption("None listed")
            with c2:
                st.markdown("**Weaknesses**")
                if result.research.weaknesses:
                    for item in result.research.weaknesses:
                        st.write(f"- {item}")
                else:
                    st.caption("None listed")

            st.markdown("**Collaboration ideas**")
            if result.research.collaboration_ideas:
                for item in result.research.collaboration_ideas:
                    st.write(f"- {item}")
            else:
                st.caption("None listed")

            st.markdown("**AI Notes**")
            st.write(build_ai_notes(result.research))
