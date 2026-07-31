import asyncio
import logging

from instagram_agent.pipelines import analyse_profiles
from instagram_agent.services.csv_exporter import CsvExporter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    urls = [
        "https://www.instagram.com/upcycle.lab.jollyzu/",
        "https://www.instagram.com/patagonia/",
        "https://www.instagram.com/nike/",
    ]

    results = await analyse_profiles(urls)

    print(f"Number of results: {len(results)}")

    for result in results:
        print(result.profile.name)

    exporter = CsvExporter()
    exporter.export(results, "analysis_results.csv")


if __name__ == "__main__":
    asyncio.run(main())
