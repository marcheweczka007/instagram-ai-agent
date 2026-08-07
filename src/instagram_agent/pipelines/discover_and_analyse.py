"""Orchestrate discovery, analysis, optional CSV export."""

from __future__ import annotations

from instagram_agent.agents.discovery import DiscoveryAgent
from instagram_agent.domain.models import AnalysisResult
from instagram_agent.logging_utils import pipeline_logging
from instagram_agent.pipelines.analyse_profiles import analyse_profiles
from instagram_agent.services.csv_exporter import CsvExporter


async def discover_and_analyse(
    query: str,
    output_csv: str | None = None,
) -> list[AnalysisResult]:
    """Discover Instagram profiles for ``query``, analyse them, optionally export."""
    with pipeline_logging("discover_and_analyse"):
        discovery = await DiscoveryAgent().discover(query)
        results = await analyse_profiles(discovery.profile_urls)
        results = sorted(
            results,
            key=lambda result: result.analysis.score,
            reverse=True,
        )

        if output_csv is not None:
            CsvExporter().export(results, output_csv)

        return results
