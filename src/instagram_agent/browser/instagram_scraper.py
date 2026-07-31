from pathlib import Path

from browser_use import Agent, ChatOpenAI

from instagram_agent.domain.models import InstagramProfile


class InstagramScraper:
    def __init__(self):
        prompt_path = (
            Path(__file__).parent.parent
            / "prompts"
            / "scraper.md"
        )

        self.system_prompt = prompt_path.read_text()

        self.llm = ChatOpenAI(
            model="gpt-5",
        )

    async def scrape(self, url: str) -> InstagramProfile:
        task = f"""
{self.system_prompt}

Open this Instagram profile:

{url}
"""

        agent = Agent(
            task=task,
            llm=self.llm,
            output_model_schema=InstagramProfile,
        )

        history = await agent.run()

        profile = history.structured_output

        if profile is None:
            raise RuntimeError(
                "Browser Use did not return a structured InstagramProfile."
            )

        return profile