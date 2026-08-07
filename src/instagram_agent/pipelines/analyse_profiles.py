"""Analyse many Instagram profiles, skipping failures."""

from __future__ import annotations

import logging

from instagram_agent.agents.scorer import ScorerAgent
from instagram_agent.browser.instagram_scraper import InstagramScraper
from instagram_agent.domain.models import AnalysisResult
from instagram_agent.logging_utils import pipeline_logging
from instagram_agent.pipelines.analyse_profile import analyse_profile

logger = logging.getLogger(__name__)


async def analyse_profiles(urls: list[str]) -> list[AnalysisResult]:
    """Analyse many Instagram profiles, skipping failures."""
    with pipeline_logging("analyse_profiles"):
        scraper = InstagramScraper()
        scorer = ScorerAgent()
        results: list[AnalysisResult] = []

        for url in urls:
            logger.info("Current URL: %s", url)
            try:
                result = await analyse_profile(url, scraper=scraper, scorer=scorer)
                results.append(result)
                logger.info("Profile analysed successfully: %s", url)
            except Exception:
                logger.exception("Failed analysing %s", url)

        return results
