import logging

from instagram_agent.agents.scorer import ScorerAgent
from instagram_agent.browser.instagram_scraper import InstagramScraper
from instagram_agent.domain.models import ProfileAnalysis
from instagram_agent.pipelines.analyse_profile import analyse_profile

logger = logging.getLogger(__name__)


async def analyse_profiles(urls: list[str]) -> list[ProfileAnalysis]:
    """Analyse many Instagram profiles, skipping failures."""
    logger.info("Starting batch analysis of %s profiles", len(urls))

    scraper = InstagramScraper()
    scorer = ScorerAgent()
    results: list[ProfileAnalysis] = []

    for url in urls:
        logger.info("Analysing profile: %s", url)
        try:
            analysis = await analyse_profile(url, scraper=scraper, scorer=scorer)
            results.append(analysis)
            logger.info("Successfully analysed profile: %s", url)
        except Exception:
            logger.exception("Failed to analyse profile: %s", url)

    logger.info(
        "Finished batch analysis (%s/%s succeeded)",
        len(results),
        len(urls),
    )
    return results
