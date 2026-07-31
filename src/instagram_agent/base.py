from openai import OpenAI
from instagram_agent.config import OPENAI_API_KEY


class BaseAgent:

    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)