import asyncio
import logging

from instagram_agent.agents.discovery import DiscoveryAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    agent = DiscoveryAgent()

    try:
        result = await agent.discover("upcycled bags")
    except Exception:
        logger.exception("Discovery failed")
        return

    print()
    print("Discovered profiles")
    for url in result.profile_urls:
        print(url)


if __name__ == "__main__":
    asyncio.run(main())
