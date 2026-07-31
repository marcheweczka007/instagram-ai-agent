from openai import OpenAI

from instagram_agent.config import OPENAI_API_KEY


def create_client() -> OpenAI:
    return OpenAI(api_key=OPENAI_API_KEY)