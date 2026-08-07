"""Run brand-fit research for a single analysed creator."""

from __future__ import annotations

import logging

from instagram_agent.agents.research import ResearchAgent
from instagram_agent.domain.models import (
    AnalysisResult,
    BrandProfile,
    ResearchAnalysis,
)

logger = logging.getLogger(__name__)


async def research_profile(
    brand: BrandProfile,
    result: AnalysisResult,
) -> ResearchAnalysis:
    """Evaluate how well an analysed creator matches ``brand``."""
    logger.info(
        "research_profile started: brand=%s creator=%s",
        brand.name,
        result.profile.name,
    )
    research = ResearchAgent().research(
        brand=brand,
        profile=result.profile,
        analysis=result.analysis,
    )
    logger.info(
        "research_profile completed: brand_fit=%s",
        research.brand_fit,
    )
    return research
