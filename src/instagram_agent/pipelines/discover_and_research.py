"""Discover creators, analyse them, then score brand fit."""

from __future__ import annotations

import logging

from instagram_agent.agents.discovery import DiscoveryAgent
from instagram_agent.agents.research import ResearchAgent
from instagram_agent.config import get_settings
from instagram_agent.domain.models import BrandProfile, BrandResearchResult
from instagram_agent.logging_utils import (
    default_csv_path,
    default_json_path,
    default_report_path,
    pipeline_logging,
)
from instagram_agent.pipelines.analyse_profiles import analyse_profiles
from instagram_agent.services.crm_exporter import CrmExporter
from instagram_agent.services.csv_exporter import CsvExporter
from instagram_agent.services.google_sheets_exporter import GoogleSheetsExporter
from instagram_agent.services.json_exporter import JsonExporter
from instagram_agent.services.notion_exporter import NotionExporter
from instagram_agent.services.report_generator import ReportGenerator, save_markdown

logger = logging.getLogger(__name__)


def _build_crm_exporter() -> CrmExporter | None:
    """Prefer Notion CRM; optionally keep Google Sheets as secondary live sink."""
    settings = get_settings()
    notion_configured = settings.notion_enabled and bool(
        settings.notion_token and settings.notion_database_id
    )
    if notion_configured:
        exporter = NotionExporter(settings=settings)
        try:
            exporter.connect()
            return exporter
        except Exception:
            logger.warning(
                "Notion setup failed; upserts will fall back to CSV",
                exc_info=True,
            )
            return exporter

    sheets_configured = settings.google_sheets_enabled or bool(
        settings.google_sheets_spreadsheet_id
    )
    if not sheets_configured:
        return None

    sheets = GoogleSheetsExporter(settings=settings)
    try:
        sheets.connect()
        sheets.create_sheet_if_missing()
    except Exception:
        logger.warning(
            "Google Sheets setup failed; rows will fall back to CSV",
            exc_info=True,
        )
    return _SheetsCrmAdapter(sheets)


class _SheetsCrmAdapter(CrmExporter):
    """Adapt GoogleSheetsExporter to the CRM upsert interface."""

    def __init__(self, sheets: GoogleSheetsExporter) -> None:
        self._sheets = sheets

    def connect(self) -> None:
        self._sheets.connect()
        self._sheets.create_sheet_if_missing()

    def upsert_creator(self, result: BrandResearchResult) -> None:
        self._sheets.append_result(result)


async def discover_and_research(
    query: str,
    brand: BrandProfile,
    output_csv: str | None = None,
    output_report: str | None = None,
    output_json: str | None = None,
) -> list[BrandResearchResult]:
    """Discover creators for ``query``, analyse them, and research brand fit.

    Results are always sorted by ``research.brand_fit`` descending.
    Each creator is upserted to Notion (or Sheets) immediately after research.
    """
    with pipeline_logging("discover_and_research"):
        discovery = await DiscoveryAgent().discover(query)
        analyses = await analyse_profiles(discovery.profile_urls)

        crm = _build_crm_exporter()
        researcher = ResearchAgent()
        results: list[BrandResearchResult] = []

        for analysis in analyses:
            research = researcher.research(
                brand=brand,
                profile=analysis.profile,
                analysis=analysis.analysis,
            )
            result = BrandResearchResult(
                profile=analysis.profile,
                analysis=analysis.analysis,
                research=research,
            )
            results.append(result)
            if crm is not None:
                try:
                    crm.upsert_creator(result)
                except Exception:
                    logger.warning(
                        "CRM upsert failed for %s; continuing pipeline",
                        result.profile.name,
                        exc_info=True,
                    )

        results = sorted(
            results,
            key=lambda item: item.research.brand_fit,
            reverse=True,
        )

        stem = brand.name.lower().replace(" ", "_")
        csv_path = output_csv or str(default_csv_path(f"{stem}_research"))
        report_path = output_report or str(default_report_path(f"{stem}_report"))
        json_path = output_json or str(default_json_path(f"{stem}_summary"))

        CsvExporter().export(results, csv_path)
        report = ReportGenerator().generate(brand, results)
        save_markdown(report, report_path)
        JsonExporter().export(brand, results, json_path)

        return results
