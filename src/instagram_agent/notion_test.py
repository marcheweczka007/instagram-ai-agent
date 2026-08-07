"""Manual smoke test for Notion CRM upsert (create + update, no duplicates)."""

from __future__ import annotations

import logging

from instagram_agent.domain.models import (
    BrandResearchResult,
    InstagramProfile,
    ProfileAnalysis,
    ResearchAnalysis,
)
from instagram_agent.logging_utils import setup_logging
from instagram_agent.services.notion_exporter import NotionExporter

setup_logging()
logger = logging.getLogger(__name__)


def _sample_result(*, brand_fit: int = 9) -> BrandResearchResult:
    return BrandResearchResult(
        profile=InstagramProfile(
            name="Notion Test Creator",
            profile_url="https://www.instagram.com/notion.test.creator/",
            bio="Handmade upcycled bags",
            followers=4200,
            following=180,
            recent_posts=["Colourful tote from reclaimed fabric"],
        ),
        analysis=ProfileAnalysis(
            score=8,
            follow=True,
            reason="Strong handmade audience overlap",
            comment="Love how you turn old fabrics into joyful everyday bags.",
        ),
        research=ResearchAnalysis(
            brand_fit=brand_fit,
            confidence=8,
            audience_match="Audience overlaps heavily with the brand",
            aesthetic_match="Strong visual storytelling",
            value_alignment="Excellent sustainability alignment",
            collaboration_potential="Recommended for collaboration",
            overall_summary="Excellent collaboration candidate for upcycled bag campaigns.",
            strengths=["Authentic craft storytelling"],
            weaknesses=["Smaller reach than mass accounts"],
            collaboration_ideas=["Limited-edition capsule drop"],
            first_outreach_angle=(
                "Hi! I loved your latest upcycled bag story — "
                "would you be open to a colourful collaboration?"
            ),
        ),
    )


def main() -> None:
    exporter = NotionExporter()
    try:
        exporter.connect()
    except Exception:
        logger.exception("Notion connect failed")
        print("Connect failed. Check NOTION_TOKEN / NOTION_DATABASE_ID / schema.")
        return

    first = _sample_result(brand_fit=9)
    exporter.upsert_creator(first)
    page_id = exporter.creator_exists(first.profile.profile_url)
    print(f"After create: page_id={page_id}")

    second = _sample_result(brand_fit=8)
    exporter.upsert_creator(second)
    page_id_again = exporter.creator_exists(second.profile.profile_url)
    print(f"After update: page_id={page_id_again}")

    if page_id and page_id_again and page_id == page_id_again:
        print("No duplicates: create + update reused the same Notion page.")
    else:
        print("Unexpected page IDs — check Notion manually.")


if __name__ == "__main__":
    main()
