"""Comment cards for the Comments page."""

from __future__ import annotations

import streamlit as st

from instagram_agent.domain.models import BrandResearchResult


def render_comment_cards(results: list[BrandResearchResult]) -> None:
    comments = [item for item in results if item.analysis.comment.strip()]
    if not comments:
        st.info("No comments generated yet.")
        return

    for index, result in enumerate(comments):
        with st.container(border=True):
            st.markdown(f"### {result.profile.name}")
            st.write(result.analysis.comment)
            cols = st.columns(2)
            with cols[0]:
                if st.button(
                    "Copy",
                    key=f"comment_copy_{index}",
                    use_container_width=True,
                ):
                    st.code(result.analysis.comment, language=None)
            cols[1].link_button(
                "Open Instagram",
                result.profile.profile_url,
                use_container_width=True,
            )
