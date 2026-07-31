import asyncio
import logging

from instagram_agent.pipelines import analyse_profiles

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        print("=" * 50)
        print(result.profile.name)
        print(result.profile.followers)
        print(result.analysis.score)
        print(result.analysis.follow)
        print(result.analysis.reason)
        print(result.analysis.comment)


if __name__ == "__main__":
    asyncio.run(main())
