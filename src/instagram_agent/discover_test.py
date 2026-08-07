import asyncio
import logging

from instagram_agent.pipelines.discover_and_analyse import discover_and_analyse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    try:
        results = await discover_and_analyse(
            "upcycled bags",
            output_csv="upcycled.csv",
        )
    except Exception:
        logger.exception("discover_and_analyse failed")
        return

    for result in results:
        print(result.profile.name)
        print(result.analysis.score)


if __name__ == "__main__":
    asyncio.run(main())
