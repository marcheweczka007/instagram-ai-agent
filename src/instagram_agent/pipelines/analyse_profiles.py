import logging

from instagram_agent.domain.models import AnalysisResult
from instagram_agent.pipelines.analyse_profile import analyse_profile

logger = logging.getLogger(__name__)


async def analyse_profiles(urls: list[str]) -> list[AnalysisResult]:
    """Analyse many Instagram profiles, skipping failures."""
    logger.info("Batch started (%s profiles)", len(urls))

    results: list[AnalysisResult] = []

    for url in urls:
        logger.info("Current URL: %s", url)
        try:
            result = await analyse_profile(url)
            results.append(result)
            logger.info("Profile analysed successfully: %s", url)
        except Exception:
            logger.exception("Failed analysing %s", url)

    logger.info(
        "Batch completed (%s/%s succeeded)",
        len(results),
        len(urls),
    )
    return results
