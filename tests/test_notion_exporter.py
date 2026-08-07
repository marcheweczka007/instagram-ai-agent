from pathlib import Path
from unittest.mock import MagicMock, patch

from notion_client.errors import APIResponseError

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


def _full_schema() -> dict:
    return {
        name: {"type": expected, expected: {}}
        for name, expected in REQUIRED_PROPERTIES.items()
    }


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


def test_create_uses_select_when_status_fallback() -> None:
    exporter = NotionExporter(token="t", database_id="d")
    exporter._status_property_type = "select"
    created = exporter._build_properties(_result(), include_status=True)
    assert created["Status"] == {"select": {"name": "New"}}


def test_ensure_schema_creates_missing_properties() -> None:
    exporter = NotionExporter(token="t", database_id="db")
    client = MagicMock()
    exporter._client = client
    exporter._data_source_id = "ds"

    initial = {
        "Name": {"type": "title", "title": {}},
        "Instagram URL": {"type": "url", "url": {}},
    }
    after_rename = {
        "Creator": {"type": "title", "title": {}},
        "Instagram URL": {"type": "url", "url": {}},
    }
    full = _full_schema()
    # Priority/Status option helpers re-read schema; return full once created.
    client.data_sources.retrieve.side_effect = [
        {"properties": initial},
        {"properties": after_rename},
        {"properties": full},
        {"properties": full},
        {"properties": full},
    ]

    exporter.ensure_schema()

    updates = [
        call.kwargs["properties"] for call in client.data_sources.update.call_args_list
    ]
    assert updates[0] == {"Name": {"name": "Creator"}}
    created_names = set()
    for payload in updates[1:]:
        created_names.update(payload.keys())
    assert "Followers" in created_names
    assert "Brand Fit" in created_names
    assert "Priority" in created_names
    assert "Status" in created_names
    assert "AI Notes" in created_names
    assert "Last Analysed" in created_names


def test_status_falls_back_to_select() -> None:
    exporter = NotionExporter(token="t", database_id="db")
    client = MagicMock()
    exporter._client = client
    exporter._data_source_id = "ds"

    def update_side_effect(*, data_source_id: str, properties: dict) -> None:
        if "Status" in properties and properties["Status"].get("type") == "status":
            raise APIResponseError(
                code="validation_error",
                status=400,
                message="status not allowed",
                headers=MagicMock(),
                raw_body_text="{}",
            )

    client.data_sources.update.side_effect = update_side_effect
    created = exporter._create_status_property()
    assert created == "select"
    assert exporter._status_property_type == "select"
    second = client.data_sources.update.call_args_list[1].kwargs["properties"]
    assert second["Status"]["type"] == "select"


def test_schema_validation_reports_missing_property() -> None:
    exporter = NotionExporter(token="t", database_id="db")
    exporter._client = MagicMock()
    exporter._data_source_id = "ds"

    try:
        exporter._validate_schema(
            {
                "Creator": {"type": "title"},
                "Instagram URL": {"type": "url"},
            }
        )
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
