"""Orchestrate discovery, analysis, optional CSV export."""

from __future__ import annotations

import logging

from instagram_agent.agents.discovery import DiscoveryAgent
from instagram_agent.domain.models import AnalysisResult
from instagram_agent.pipelines.analyse_profiles import analyse_profiles
from instagram_agent.services.csv_exporter import CsvExporter

logger = logging.getLogger(__name__)


async def discover_and_analyse(
    query: str,
    output_csv: str | None = None,
) -> list[AnalysisResult]:
    """Discover Instagram profiles for ``query``, analyse them, optionally export."""
    logger.info("Discovery started for query=%r", query)

    discovery = await DiscoveryAgent().discover(query)
    logger.info(
        "Number of profiles discovered: %s",
        len(discovery.profile_urls),
    )

    logger.info("Analysis started")
    results = await analyse_profiles(discovery.profile_urls)
    results = sorted(
        results,
        key=lambda result: result.analysis.score,
        reverse=True,
    )

    if output_csv is not None:
        logger.info("Export started → %s", output_csv)
        CsvExporter().export(results, output_csv)

    logger.info("Completed (%s analysed profiles)", len(results))
    return results
