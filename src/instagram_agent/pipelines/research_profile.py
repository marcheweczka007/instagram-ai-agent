"""Run brand-fit research for a single analysed creator."""

from __future__ import annotations

from instagram_agent.agents.research import ResearchAgent
from instagram_agent.domain.models import (
    AnalysisResult,
    BrandProfile,
    ResearchAnalysis,
)
from instagram_agent.logging_utils import pipeline_logging


async def research_profile(
    brand: BrandProfile,
    result: AnalysisResult,
    researcher: ResearchAgent | None = None,
) -> ResearchAnalysis:
    """Evaluate how well an analysed creator matches ``brand``."""
    with pipeline_logging("research_profile"):
        agent = researcher or ResearchAgent()
        return agent.research(
            brand=brand,
            profile=result.profile,
            analysis=result.analysis,
        )
