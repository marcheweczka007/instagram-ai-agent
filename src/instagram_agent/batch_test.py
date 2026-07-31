import asyncio
import logging

from instagram_agent.pipelines import analyse_profiles

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    urls = [
        "https://www.instagram.com/upcycle.lab.jollyzu/",
        "https://www.instagram.com/patagonia/",
        "https://www.instagram.com/nike/",
    ]

    try:
        results = await analyse_profiles(urls)
    except Exception:
        logging.exception("Batch analysis failed")
        return

    for result in results:
        print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
