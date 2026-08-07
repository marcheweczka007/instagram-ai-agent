"""Brand-fit research agent for creator collaboration decisions."""

from __future__ import annotations

import logging
from pathlib import Path

from instagram_agent.agents.base import BaseAgent
from instagram_agent.config import get_settings
from instagram_agent.domain.models import (
    BrandProfile,
    InstagramProfile,
    ProfileAnalysis,
    ResearchAnalysis,
)

logger = logging.getLogger(__name__)


class ResearchAgent(BaseAgent):
    """Evaluate how well a creator matches a specific brand.

    Public API is platform-agnostic: pass any creator snapshot that fits
    ``InstagramProfile``-shaped data today; later adapters can map TikTok /
    YouTube / etc. into the same research call without changing callers.
    """

    def __init__(self, client=None) -> None:
        super().__init__(client=client)
        prompt_path = Path(__file__).parent.parent / "prompts" / "research.md"
        self.system_prompt = prompt_path.read_text(encoding="utf-8")
        self._model = get_settings().openai_model

    def research(
        self,
        brand: BrandProfile,
        profile: InstagramProfile,
        analysis: ProfileAnalysis,
    ) -> ResearchAnalysis:
        """Return brand-specific collaboration research for one creator."""
        logger.info(
            "Researching brand fit: brand=%s creator=%s",
            brand.name,
            profile.name,
        )

        completion = self.client.chat.completions.parse(
            model=self._model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user",
                    "content": self._build_user_prompt(brand, profile, analysis),
                },
            ],
            response_format=ResearchAnalysis,
        )

        result = completion.choices[0].message.parsed
        if result is None:
            raise RuntimeError("OpenAI did not return a ResearchAnalysis.")

        logger.info(
            "Research complete: brand_fit=%s confidence=%s",
            result.brand_fit,
            result.confidence,
        )
        return result

    def _build_user_prompt(
        self,
        brand: BrandProfile,
        profile: InstagramProfile,
        analysis: ProfileAnalysis,
    ) -> str:
        return f"""
Brand
-----
Name: {brand.name}
Description: {brand.description}
Target audience: {", ".join(brand.target_audience)}
Values: {", ".join(brand.values)}
Products: {", ".join(brand.products)}
Tone of voice: {brand.tone_of_voice}

Creator profile
---------------
Name: {profile.name}
URL: {profile.profile_url}
Bio: {profile.bio}
Followers: {profile.followers}
Following: {profile.following}
Recent posts:
{chr(10).join(f"- {post}" for post in profile.recent_posts) or "- (none)"}

Prior profile analysis
----------------------
Score: {analysis.score}
Follow recommendation: {analysis.follow}
Reason: {analysis.reason}
Suggested comment: {analysis.comment}

Assess collaboration fit for this brand only.
""".strip()
