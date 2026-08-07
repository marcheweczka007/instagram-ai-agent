import asyncio
import logging

from instagram_agent.domain.models import BrandProfile
from instagram_agent.pipelines.analyse_profile import analyse_profile
from instagram_agent.pipelines.research_profile import research_profile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_jollyzu_brand() -> BrandProfile:
    return BrandProfile(
        name="JollyZu",
        description=(
            "Handmade colourful upcycled bags crafted for eco-conscious "
            "creative women who love slow fashion."
        ),
        target_audience=[
            "Women 25-40",
            "Eco-conscious shoppers",
            "Creative makers and designers",
            "Slow fashion community",
        ],
        values=[
            "Sustainability",
            "Craftsmanship",
            "Circular economy",
            "Colour",
            "Creativity",
        ],
        products=[
            "Handmade colourful upcycled bags",
        ],
        tone_of_voice="Friendly, creative, and authentic",
    )


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
