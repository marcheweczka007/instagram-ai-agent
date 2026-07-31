import asyncio

from instagram_agent.browser.instagram_scraper import InstagramScraper


async def main():
    scraper = InstagramScraper()

    profile = await scraper.scrape(
        "https://www.instagram.com/upcycle.lab.jollyzu/"
    )

    print(profile.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())