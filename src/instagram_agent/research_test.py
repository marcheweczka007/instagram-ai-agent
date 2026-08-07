import asyncio
import logging

from instagram_agent.fixtures import build_jollyzu_brand
from instagram_agent.logging_utils import setup_logging
from instagram_agent.pipelines.analyse_profile import analyse_profile
from instagram_agent.pipelines.research_profile import research_profile

setup_logging()
logger = logging.getLogger(__name__)


async def main() -> None:
    brand = build_jollyzu_brand()

    try:
        analysis_result = await analyse_profile("https://www.instagram.com/patagonia/")
        research = await research_profile(brand, analysis_result)
    except Exception:
        logger.exception("Brand research test failed")
        return

    print("Brand fit:", research.brand_fit)
    print("Confidence:", research.confidence)
    print("Strengths:")
    for item in research.strengths:
        print(f"- {item}")
    print("Weaknesses:")
    for item in research.weaknesses:
        print(f"- {item}")
    print("Collaboration ideas:")
    for item in research.collaboration_ideas:
        print(f"- {item}")
    print("First outreach angle:", research.first_outreach_angle)


if __name__ == "__main__":
    asyncio.run(main())
