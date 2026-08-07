"""Scrape an Instagram profile and return profile plus scored analysis."""

from __future__ import annotations

from instagram_agent.agents.scorer import ScorerAgent
from instagram_agent.browser.instagram_scraper import InstagramScraper
from instagram_agent.domain.models import AnalysisResult
from instagram_agent.logging_utils import pipeline_logging


async def analyse_profile(
    url: str,
    scraper: InstagramScraper | None = None,
    scorer: ScorerAgent | None = None,
) -> AnalysisResult:
    """Scrape an Instagram profile and return profile plus scored analysis."""
    with pipeline_logging("analyse_profile"):
        active_scraper = scraper or InstagramScraper()
        active_scorer = scorer or ScorerAgent()

        profile = await active_scraper.scrape(url)
        analysis = active_scorer.score(profile)
        return AnalysisResult(profile=profile, analysis=analysis)
