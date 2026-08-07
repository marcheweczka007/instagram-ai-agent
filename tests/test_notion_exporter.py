from pathlib import Path
from unittest.mock import MagicMock, patch

from instagram_agent.domain.models import (
    BrandResearchResult,
    InstagramProfile,
    ProfileAnalysis,
    ResearchAnalysis,
)
from instagram_agent.services.notion_exporter import (
    REQUIRED_PROPERTIES,
    NotionExporter,
)


def _result(brand_fit: int = 9) -> BrandResearchResult:
    return BrandResearchResult(
        profile=InstagramProfile(
            name="EcoMaker",
            profile_url="https://www.instagram.com/ecomaker/",
            bio="bags",
            followers=1000,
            following=10,
            recent_posts=[],
        ),
        analysis=ProfileAnalysis(
            score=8,
            follow=True,
            reason="fit",
            comment="Nice colour story",
        ),
        research=ResearchAnalysis(
            brand_fit=brand_fit,
            confidence=8,
            audience_match="audience overlaps heavily with the brand",
            aesthetic_match="strong visual storytelling",
            value_alignment="excellent sustainability alignment",
            collaboration_potential="recommended for collaboration",
            overall_summary="Great fit",
            strengths=["Authentic"],
            weaknesses=["Niche"],
            collaboration_ideas=["Capsule"],
            first_outreach_angle="Hello there",
        ),
    )


def test_priority_mapping() -> None:
    assert NotionExporter._priority_from_brand_fit(9) == "High"
    assert NotionExporter._priority_from_brand_fit(7) == "Medium"
    assert NotionExporter._priority_from_brand_fit(6) == "Low"


def test_ai_notes_are_readable() -> None:
    notes = NotionExporter._build_ai_notes(_result().research)
    assert "Excellent sustainability alignment." in notes
    assert "Strong visual storytelling." in notes
    assert "Audience overlaps heavily with the brand." in notes
    assert "Recommended for collaboration." in notes


def test_create_includes_status_update_does_not() -> None:
    exporter = NotionExporter(token="t", database_id="d")
    created = exporter._build_properties(_result(), include_status=True)
    updated = exporter._build_properties(_result(), include_status=False)
    assert "Status" in created
    assert created["Status"]["status"]["name"] == "New"
    assert "Status" not in updated


def test_schema_validation_reports_missing_property() -> None:
    exporter = NotionExporter(token="t", database_id="db")
    client = MagicMock()
    client.data_sources.retrieve.return_value = {
        "properties": {
            "Creator": {"type": "title"},
            "Instagram URL": {"type": "url"},
        }
    }
    exporter._client = client
    exporter._data_source_id = "ds"

    try:
        exporter._validate_schema()
        raised = False
    except RuntimeError as exc:
        raised = True
        message = str(exc)
        assert "Missing properties" in message
        assert "Brand Fit" in message

    assert raised is True


def test_upsert_falls_back_to_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "notion_fallback.csv"
    exporter = NotionExporter(
        token="t",
        database_id="db",
        fallback_csv_path=csv_path,
    )
    with patch.object(exporter, "connect", side_effect=RuntimeError("boom")):
        exporter.upsert_creator(_result())

    content = csv_path.read_text(encoding="utf-8")
    assert "EcoMaker" in content
    assert "Hello there" in content


def test_required_properties_cover_expected_schema() -> None:
    assert REQUIRED_PROPERTIES["Priority"] == "select"
    assert REQUIRED_PROPERTIES["Status"] == "status"
    assert REQUIRED_PROPERTIES["Last Analysed"] == "date"
