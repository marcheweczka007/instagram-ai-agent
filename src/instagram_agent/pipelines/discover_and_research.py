"""Discover creators, analyse them, then score brand fit."""

from __future__ import annotations

from instagram_agent.agents.discovery import DiscoveryAgent
from instagram_agent.agents.research import ResearchAgent
from instagram_agent.domain.models import BrandProfile, BrandResearchResult
from instagram_agent.logging_utils import (
    default_csv_path,
    default_json_path,
    default_report_path,
    pipeline_logging,
)
from instagram_agent.pipelines.analyse_profiles import analyse_profiles
from instagram_agent.services.csv_exporter import CsvExporter
from instagram_agent.services.json_exporter import JsonExporter
from instagram_agent.services.report_generator import ReportGenerator, save_markdown


async def discover_and_research(
    query: str,
    brand: BrandProfile,
    output_csv: str | None = None,
    output_report: str | None = None,
    output_json: str | None = None,
) -> list[BrandResearchResult]:
    """Discover creators for ``query``, analyse them, and research brand fit.

    Results are always sorted by ``research.brand_fit`` descending.
    Optional exports write under ``outputs/`` when paths are omitted defaults.
    """
    with pipeline_logging("discover_and_research"):
        discovery = await DiscoveryAgent().discover(query)
        analyses = await analyse_profiles(discovery.profile_urls)

        researcher = ResearchAgent()
        results: list[BrandResearchResult] = []
        for analysis in analyses:
            research = researcher.research(
                brand=brand,
                profile=analysis.profile,
                analysis=analysis.analysis,
            )
            results.append(
                BrandResearchResult(
                    profile=analysis.profile,
                    analysis=analysis.analysis,
                    research=research,
                )
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

        # Always produce the three v1.0 artifacts when running this pipeline.
        CsvExporter().export(results, csv_path)
        report = ReportGenerator().generate(brand, results)
        save_markdown(report, report_path)
        JsonExporter().export(brand, results, json_path)

        return results
