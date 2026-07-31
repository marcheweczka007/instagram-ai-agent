from instagram_agent.agents.scorer import ScorerAgent
from instagram_agent.browser.instagram_scraper import InstagramScraper
from instagram_agent.domain.models import ProfileAnalysis


async def analyse_profile(url: str) -> ProfileAnalysis:
    """Scrape an Instagram profile and return a scored analysis."""
    scraper = InstagramScraper()
    scorer = ScorerAgent()

    profile = await scraper.scrape(url)
    return scorer.score(profile)
