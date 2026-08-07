from pathlib import Path

from instagram_agent.domain.models import (
    AnalysisResult,
    BrandResearchResult,
    InstagramProfile,
    ProfileAnalysis,
    ResearchAnalysis,
)
from instagram_agent.services.csv_exporter import CsvExporter


def _analysis_result() -> AnalysisResult:
    return AnalysisResult(
        profile=InstagramProfile(
            name="EcoMaker",
            profile_url="https://www.instagram.com/ecomaker/",
            bio="bags",
            followers=12,
            following=3,
            recent_posts=[],
        ),
        analysis=ProfileAnalysis(
            score=7,
            follow=True,
            reason="reason",
            comment="comment",
        ),
    )


def test_csv_exporter_writes_header_for_empty_results(tmp_path: Path) -> None:
    path = tmp_path / "empty.csv"
    CsvExporter().export([], str(path))
    content = path.read_text(encoding="utf-8")
    assert "profile_name" in content
    assert "brand_fit" not in content


def test_csv_exporter_includes_research_columns(tmp_path: Path) -> None:
    base = _analysis_result()
    result = BrandResearchResult(
        profile=base.profile,
        analysis=base.analysis,
        research=ResearchAnalysis(
            brand_fit=9,
            confidence=8,
            audience_match="a",
            aesthetic_match="b",
            value_alignment="c",
            collaboration_potential="d",
            overall_summary="summary",
            strengths=["s"],
            weaknesses=["w"],
            collaboration_ideas=["i"],
            first_outreach_angle="hello",
        ),
    )
    path = tmp_path / "research.csv"
    CsvExporter().export([result], str(path))
    content = path.read_text(encoding="utf-8")
    assert "brand_fit" in content
    assert "hello" in content
