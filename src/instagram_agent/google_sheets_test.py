"""Manual smoke test for Google Sheets export."""

from __future__ import annotations

import logging

from instagram_agent.domain.models import (
    BrandResearchResult,
    InstagramProfile,
    ProfileAnalysis,
    ResearchAnalysis,
)
from instagram_agent.logging_utils import setup_logging
from instagram_agent.services.google_sheets_exporter import GoogleSheetsExporter

setup_logging()
logger = logging.getLogger(__name__)


def _sample_result() -> BrandResearchResult:
    return BrandResearchResult(
        profile=InstagramProfile(
            name="Sample Creator",
            profile_url="https://www.instagram.com/sample.creator/",
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
            brand_fit=9,
            confidence=8,
            audience_match="Eco-conscious creative women",
            aesthetic_match="Colourful craft-led visuals",
            value_alignment="Strong sustainability alignment",
            collaboration_potential="High",
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
    exporter = GoogleSheetsExporter()
    try:
        exporter.connect()
        exporter.create_sheet_if_missing()
        exporter.append_result(_sample_result())
        print("Google Sheets append succeeded.")
    except Exception:
        logger.exception(
            "Google Sheets test failed (CSV fallback may still have written)"
        )
        # Demonstrate fallback path explicitly.
        exporter.append_result(_sample_result())
        print("Fell back to CSV. Check outputs/csv/google_sheets_fallback.csv")


if __name__ == "__main__":
    main()
