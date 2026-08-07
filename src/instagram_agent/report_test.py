import asyncio
import logging

from instagram_agent.domain.models import BrandProfile, BrandResearchResult
from instagram_agent.pipelines.analyse_profile import analyse_profile
from instagram_agent.pipelines.research_profile import research_profile
from instagram_agent.services.report_generator import ReportGenerator, save_markdown

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
        logger.exception("Brand research report test failed")
        return

    results = [
        BrandResearchResult(
            profile=analysis_result.profile,
            analysis=analysis_result.analysis,
            research=research,
        )
    ]

    report = ReportGenerator().generate(brand, results)
    save_markdown(report, "brand_report.md")
    print("Report generated successfully.")


if __name__ == "__main__":
    asyncio.run(main())
