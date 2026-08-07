"""Outreach / DM cards."""

from __future__ import annotations

import streamlit as st

from instagram_agent.domain.models import BrandResearchResult
from instagram_agent.services.workspace import dm_subject


def render_outreach_cards(results: list[BrandResearchResult]) -> None:
    outreach = [item for item in results if item.research.first_outreach_angle.strip()]
    if not outreach:
        st.info("No DMs generated yet.")
        return

    for index, result in enumerate(outreach):
        with st.container(border=True):
            st.markdown(f"### {result.profile.name}")
            st.write(f"**Subject:** {dm_subject(result)}")
            st.write(result.research.first_outreach_angle)
            cols = st.columns(2)
            with cols[0]:
                if st.button(
                    "Copy",
                    key=f"dm_copy_{index}",
                    use_container_width=True,
                ):
                    st.code(result.research.first_outreach_angle, language=None)
            cols[1].link_button(
                "Open Instagram",
                result.profile.profile_url,
                use_container_width=True,
            )
