import asyncio
import logging

from instagram_agent.domain.models import BrandResearchResult
from instagram_agent.fixtures import build_jollyzu_brand
from instagram_agent.logging_utils import default_report_path, setup_logging
from instagram_agent.pipelines.analyse_profile import analyse_profile
from instagram_agent.pipelines.research_profile import research_profile
from instagram_agent.services.report_generator import ReportGenerator, save_markdown

setup_logging()
logger = logging.getLogger(__name__)


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
    path = default_report_path("brand_report")
    save_markdown(report, str(path))
    print("Report generated successfully.")
    print(path)


if __name__ == "__main__":
    asyncio.run(main())
