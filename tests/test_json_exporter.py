from pathlib import Path

from instagram_agent.domain.models import (
    BrandResearchResult,
    InstagramProfile,
    ProfileAnalysis,
    ResearchAnalysis,
)
from instagram_agent.fixtures import build_jollyzu_brand
from instagram_agent.services.json_exporter import JsonExporter


def test_json_exporter_writes_summary(tmp_path: Path) -> None:
    brand = build_jollyzu_brand()
    results = [
        BrandResearchResult(
            profile=InstagramProfile(
                name="A",
                profile_url="https://www.instagram.com/a/",
                bio="",
                followers=1,
                following=1,
                recent_posts=[],
            ),
            analysis=ProfileAnalysis(
                score=5,
                follow=False,
                reason="r",
                comment="c",
            ),
            research=ResearchAnalysis(
                brand_fit=6,
                confidence=5,
                audience_match="a",
                aesthetic_match="b",
                value_alignment="c",
                collaboration_potential="d",
                overall_summary="summary",
                strengths=[],
                weaknesses=[],
                collaboration_ideas=[],
                first_outreach_angle="hi",
            ),
        )
    ]
    path = tmp_path / "summary.json"
    JsonExporter().export(brand, results, str(path))
    text = path.read_text(encoding="utf-8")
    assert '"brand_fit": 6' in text
    assert "JollyZu" in text
