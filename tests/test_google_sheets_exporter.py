from pathlib import Path
from unittest.mock import MagicMock, patch

from instagram_agent.domain.models import (
    AnalysisResult,
    BrandResearchResult,
    InstagramProfile,
    ProfileAnalysis,
    ResearchAnalysis,
)
from instagram_agent.services.google_sheets_exporter import (
    HEADERS,
    GoogleSheetsExporter,
)


def _analysis_result() -> AnalysisResult:
    return AnalysisResult(
        profile=InstagramProfile(
            name="EcoMaker",
            profile_url="https://www.instagram.com/ecomaker/",
            bio="bags",
            followers=1200,
            following=40,
            recent_posts=[],
        ),
        analysis=ProfileAnalysis(
            score=7,
            follow=True,
            reason="fit",
            comment="Great colour story",
        ),
    )


def _research_result() -> BrandResearchResult:
    base = _analysis_result()
    return BrandResearchResult(
        profile=base.profile,
        analysis=base.analysis,
        research=ResearchAnalysis(
            brand_fit=9,
            confidence=8,
            audience_match="a",
            aesthetic_match="b",
            value_alignment="c",
            collaboration_potential="d",
            overall_summary="Strong fit",
            strengths=["s"],
            weaknesses=["w"],
            collaboration_ideas=["i"],
            first_outreach_angle="Hello DM",
        ),
    )


def test_to_row_for_research_result() -> None:
    row = GoogleSheetsExporter._to_row(_research_result())
    assert row[0] == "EcoMaker"
    assert row[4] == 9
    assert row[7] == "Hello DM"
    assert row[8] == "researched"


def test_append_result_falls_back_to_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "fallback.csv"
    exporter = GoogleSheetsExporter(
        spreadsheet_id="sheet-id",
        worksheet_name="Creators",
        credentials_path=tmp_path / "missing.json",
        fallback_csv_path=csv_path,
    )

    with patch.object(exporter, "connect", side_effect=RuntimeError("boom")):
        exporter.append_result(_research_result())

    content = csv_path.read_text(encoding="utf-8")
    assert ",".join(HEADERS) in content
    assert "EcoMaker" in content
    assert "Hello DM" in content


def test_create_sheet_if_missing_writes_headers() -> None:
    import gspread

    exporter = GoogleSheetsExporter(
        spreadsheet_id="sheet-id",
        worksheet_name="Creators",
        credentials_path="credentials.json",
    )
    worksheet = MagicMock()
    worksheet.row_values.return_value = []
    spreadsheet = MagicMock()
    spreadsheet.worksheet.side_effect = gspread.WorksheetNotFound("Creators")
    spreadsheet.add_worksheet.return_value = worksheet
    exporter._spreadsheet = spreadsheet

    exporter.create_sheet_if_missing()

    spreadsheet.add_worksheet.assert_called_once()
    worksheet.append_row.assert_called()
