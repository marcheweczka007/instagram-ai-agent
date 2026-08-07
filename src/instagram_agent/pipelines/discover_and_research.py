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
from instagram_agent.services.csv_exporter import CsvExporter
from instagram_agent.services.google_sheets_exporter import GoogleSheetsExporter
from instagram_agent.services.json_exporter import JsonExporter
from instagram_agent.services.report_generator import ReportGenerator, save_markdown

logger = logging.getLogger(__name__)


def _build_sheets_exporter() -> GoogleSheetsExporter | None:
    settings = get_settings()
    configured = settings.google_sheets_enabled or bool(
        settings.google_sheets_spreadsheet_id
    )
    if not configured:
        return None

    exporter = GoogleSheetsExporter(settings=settings)
    try:
        exporter.connect()
        exporter.create_sheet_if_missing()
        return exporter
    except Exception:
        logger.exception(
            "Google Sheets setup failed; rows will fall back to CSV via exporter"
        )
        # Still return exporter so append_result can use CSV fallback.
        return exporter


async def discover_and_research(
    query: str,
    brand: BrandProfile,
    output_csv: str | None = None,
    output_report: str | None = None,
    output_json: str | None = None,
) -> list[BrandResearchResult]:
    """Discover creators for ``query``, analyse them, and research brand fit.

    Results are always sorted by ``research.brand_fit`` descending.
    When Google Sheets is configured, each creator is appended immediately
    after research (CSV fallback on Sheets errors).
    """
    with pipeline_logging("discover_and_research"):
        discovery = await DiscoveryAgent().discover(query)
        analyses = await analyse_profiles(discovery.profile_urls)

        sheets = _build_sheets_exporter()
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
            if sheets is not None:
                sheets.append_result(result)

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
