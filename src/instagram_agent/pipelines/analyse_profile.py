from instagram_agent.agents.scorer import ScorerAgent
from instagram_agent.browser.instagram_scraper import InstagramScraper
from instagram_agent.domain.models import ProfileAnalysis


async def analyse_profile(
    url: str,
    scraper: InstagramScraper | None = None,
    scorer: ScorerAgent | None = None,
) -> ProfileAnalysis:
    """Scrape an Instagram profile and return a scored analysis."""
    active_scraper = scraper or InstagramScraper()
    active_scorer = scorer or ScorerAgent()

    profile = await active_scraper.scrape(url)
    return active_scorer.score(profile)
