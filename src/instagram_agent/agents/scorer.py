from pathlib import Path

from instagram_agent.agents.base import BaseAgent
from instagram_agent.domain.models import (
    InstagramProfile,
    ProfileAnalysis,
)


class ScorerAgent(BaseAgent):
    def __init__(self):
        super().__init__()

        prompt_path = (
            Path(__file__).parent.parent
            / "prompts"
            / "scorer.md"
        )

        self.system_prompt = prompt_path.read_text()

    def score(self, profile: InstagramProfile) -> ProfileAnalysis:
        prompt = f"""
Name: {profile.name}

Bio:
{profile.bio}

Followers:
{profile.followers}

Recent posts:
{chr(10).join(profile.recent_posts)}
"""

        completion = self.client.chat.completions.parse(
            model="gpt-5",
            messages=[
                {
                    "role": "system",
                    "content": self.system_prompt,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            response_format=ProfileAnalysis,
        )

        return completion.choices[0].message.parsed