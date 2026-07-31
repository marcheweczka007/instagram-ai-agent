from browser_use import Agent, ChatOpenAI


class InstagramScraper:
    def __init__(self):
        self.agent = Agent(
            task="",
            llm=ChatOpenAI(model="gpt-5"),
        )

    async def scrape(self, url: str):
        pass