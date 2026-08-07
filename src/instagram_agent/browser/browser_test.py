import asyncio

from browser_use import Agent, ChatOpenAI
from dotenv import load_dotenv

load_dotenv()


async def main():
    agent = Agent(
        task="Open https://example.com and tell me the page title.",
        llm=ChatOpenAI(
            model="gpt-5",
        ),
    )

    result = await agent.run()

    print(result.final_result())


if __name__ == "__main__":
    asyncio.run(main())
