"""Placeholder: discover creators, analyse them, then score brand fit."""

from __future__ import annotations

from instagram_agent.domain.models import BrandProfile, BrandResearchResult


async def discover_and_research(
    query: str,
    brand: BrandProfile,
    output_csv: str | None = None,
) -> list[BrandResearchResult]:
    """Discover creators for ``query``, analyse them, and research brand fit.

    Intended workflow (not implemented yet):

    1. ``DiscoveryAgent().discover(query)``
    2. ``analyse_profiles(discovery.profile_urls)``
    3. ``ResearchAgent`` / ``research_profile`` for each result
    4. Sort by ``research.brand_fit`` descending
    5. Optional ``CsvExporter().export(...)``
    6. Return ``list[BrandResearchResult]``
    """
    raise NotImplementedError(
        "discover_and_research is a placeholder. "
        "Use research_profile() with an AnalysisResult for now."
    )
