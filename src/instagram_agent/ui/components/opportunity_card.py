"""Opportunity action cards for Today's Opportunities."""

from __future__ import annotations

import streamlit as st

from instagram_agent.domain.models import CommentOpportunity
from instagram_agent.ui import state


def render_opportunity_card(opportunity: CommentOpportunity) -> None:
    with st.container(border=True):
        head = st.columns([1, 4, 1])
        with head[0]:
            st.image(opportunity.profile_picture_url, width=72)
        with head[1]:
            st.markdown(f"### {opportunity.creator_name}")
            st.caption(opportunity.creator_url)
        with head[2]:
            st.metric("Opportunity", f"{opportunity.opportunity_score:.0f}")
            st.caption(f"Brand Fit {opportunity.brand_fit}/10")

        st.markdown(f"**Latest post:** {opportunity.post_preview}")
        st.markdown(f"**Post URL:** [{opportunity.post_url}]({opportunity.post_url})")
        st.info(f"**Why this is recommended now:** {opportunity.why_now}")

        with st.expander("How Opportunity Score is calculated", expanded=False):
            breakdown = opportunity.score_breakdown
            st.write(opportunity.score_explanation)
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Brand Fit", f"{breakdown.brand_fit}/35")
            c2.metric("Freshness", f"{breakdown.post_freshness}/20")
            c3.metric("Comment room", f"{breakdown.comment_room}/15")
            c4.metric("Similarity", f"{breakdown.brand_similarity}/15")
            c5.metric("Visibility", f"{breakdown.visibility_potential}/15")

        st.markdown("**Latest comments preview**")
        for comment in opportunity.latest_comments[:5]:
            st.write(f"- {comment}")

        st.markdown("**AI comment suggestions**")
        for index, suggestion in enumerate(opportunity.comment_suggestions, start=1):
            st.markdown(f"**Comment #{index}**")
            st.write(suggestion)

        actions = st.columns(5)
        for index in range(3):
            suggestion = opportunity.comment_suggestions[index]
            with actions[index]:
                if st.button(
                    f"Copy Comment #{index + 1}",
                    key=f"copy_{opportunity.id}_{index}",
                    use_container_width=True,
                ):
                    st.code(suggestion, language=None)

        actions[3].link_button(
            "Open Post",
            opportunity.post_url,
            use_container_width=True,
        )
        with actions[4]:
            st.button(
                "Mark Done",
                key=f"done_{opportunity.id}",
                use_container_width=True,
                on_click=state.mark_opportunity_done,
                args=(opportunity.id,),
            )
            st.button(
                "Skip",
                key=f"skip_{opportunity.id}",
                use_container_width=True,
                on_click=state.skip_opportunity,
                args=(opportunity.id,),
            )
