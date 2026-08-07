from pathlib import Path

from instagram_agent.domain.models import (
    BrandResearchResult,
    InstagramProfile,
    ProfileAnalysis,
    ResearchAnalysis,
)
from instagram_agent.fixtures import build_jollyzu_brand
from instagram_agent.services.report_generator import ReportGenerator, save_markdown


def _result(name: str, fit: int) -> BrandResearchResult:
    return BrandResearchResult(
        profile=InstagramProfile(
            name=name,
            profile_url=f"https://www.instagram.com/{name.lower()}/",
            bio="bio",
            followers=1000,
            following=10,
            recent_posts=["post"],
        ),
        analysis=ProfileAnalysis(
            score=fit,
            follow=fit >= 7,
            reason="reason",
            comment="comment",
        ),
        research=ResearchAnalysis(
            brand_fit=fit,
            confidence=7,
            audience_match="Eco audience",
            aesthetic_match="Craft aesthetic",
            value_alignment="Aligned",
            collaboration_potential="Medium",
            overall_summary=f"{name} is a useful collaboration candidate.",
            strengths=["Authentic"],
            weaknesses=["Niche"],
            collaboration_ideas=["Capsule"],
            first_outreach_angle="Loved your latest drop",
        ),
    )


def test_report_generator_ranks_and_sections() -> None:
    brand = build_jollyzu_brand()
    report = ReportGenerator().generate(
        brand,
        [_result("LowFit", 3), _result("HighFit", 9)],
    )
    assert "# Brand Research Report" in report
    assert "HighFit" in report
    assert report.index("HighFit") < report.index("LowFit")
    assert "## Recommended Creators" in report
    assert "## Creators To Avoid" in report
    assert "## Overall Insights" in report


def test_save_markdown(tmp_path: Path) -> None:
    path = tmp_path / "report.md"
    save_markdown("# Hello", str(path))
    assert path.read_text(encoding="utf-8") == "# Hello"
