import asyncio
import sys

from instagram_agent.pipelines import analyse_profile


async def main() -> None:
    url = sys.argv[1] if len(sys.argv) > 1 else (
        "https://www.instagram.com/upcycle.lab.jollyzu/"
    )
    analysis = await analyse_profile(url)
    print(analysis.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
