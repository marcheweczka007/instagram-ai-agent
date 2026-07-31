import asyncio

from instagram_agent.browser.instagram_scraper import InstagramScraper


async def main():
    scraper = InstagramScraper()

    urls = [
        "https://www.instagram.com/upcycle.lab.jollyzu/",
        "https://www.instagram.com/patagonia/",
        "https://www.instagram.com/nike/",
    ]

    for url in urls:
        print(f"\n=== Testing {url} ===")

        try:
            profile = await scraper.scrape(url)
            print(profile.model_dump_json(indent=2))
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())