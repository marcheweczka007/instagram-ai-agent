import asyncio
import logging

from instagram_agent.domain.models import AnalysisResult
from instagram_agent.pipelines import analyse_profiles

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def print_analysis_result(result: AnalysisResult) -> None:
    print(f"Profile name: {result.profile.name}")
    print(f"Followers: {result.profile.followers}")
    print(f"Score: {result.analysis.score}")
    print(f"Follow recommendation: {result.analysis.follow}")
    print(f"Reason: {result.analysis.reason}")
    print(f"Suggested comment: {result.analysis.comment}")
    print()


async def main() -> None:
    urls = [
        "https://www.instagram.com/upcycle.lab.jollyzu/",
        "https://www.instagram.com/patagonia/",
        "https://www.instagram.com/nike/",
    ]

    try:
        results = await analyse_profiles(urls)
    except Exception:
        logger.exception("Batch analysis failed")
        return

    for result in results:
        print_analysis_result(result)


if __name__ == "__main__":
    asyncio.run(main())
