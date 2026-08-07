from __future__ import annotations

from pathlib import Path

from instagram_agent.agents.base import BaseAgent
from instagram_agent.config import get_settings
from instagram_agent.domain.models import InstagramProfile, ProfileAnalysis


class ScorerAgent(BaseAgent):
    """Score an Instagram creator profile."""

    def __init__(self, client=None) -> None:
        super().__init__(client=client)
        prompt_path = Path(__file__).parent.parent / "prompts" / "scorer.md"
        self.system_prompt = prompt_path.read_text(encoding="utf-8")
        self._model = get_settings().openai_model

    def score(self, profile: InstagramProfile) -> ProfileAnalysis:
        """Return a structured profile quality analysis."""
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
            model=self._model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ],
            response_format=ProfileAnalysis,
        )

        parsed = completion.choices[0].message.parsed
        if parsed is None:
            raise RuntimeError("OpenAI did not return a ProfileAnalysis.")
        return parsed
