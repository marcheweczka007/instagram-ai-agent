from pathlib import Path

from instagram_agent.agents.base import BaseAgent
from instagram_agent.domain.models import InstagramProfile
from instagram_agent.infrastructure.openai_client import create_client


class ScorerAgent(BaseAgent):
    def __init__(self):
        super().__init__()

        self.client = create_client()

        prompt_path = (
            Path(__file__).parent.parent
            / "prompts"
            / "scorer.md"
        )

        self.system_prompt = prompt_path.read_text()

    def score(self, profile: InstagramProfile):
        prompt = f"""
Name: {profile.name}

Bio:
{profile.bio}

Followers:
{profile.followers}

Recent posts:
{chr(10).join(profile.recent_posts)}
"""

        response = self.client.responses.create(
            model="gpt-5",
            instructions=self.system_prompt,
            input=prompt,
        )

        return response.output_text