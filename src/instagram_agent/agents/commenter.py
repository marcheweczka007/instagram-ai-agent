"""Generate comment suggestions for opportunity cards."""

from __future__ import annotations

import logging

from pydantic import BaseModel, Field

from instagram_agent.agents.base import BaseAgent
from instagram_agent.config import get_settings
from instagram_agent.domain.models import BrandProfile, BrandResearchResult

logger = logging.getLogger(__name__)


class _CommentBundle(BaseModel):
    suggestions: list[str] = Field(min_length=3, max_length=3)
    thread_preview: list[str] = Field(min_length=3, max_length=5)


class CommenterAgent(BaseAgent):
    """Produce three short Instagram comments tailored to one post."""

    def generate_suggestions(
        self,
        *,
        brand: BrandProfile,
        result: BrandResearchResult,
        post_preview: str,
    ) -> list[str]:
        try:
            bundle = self._generate_with_llm(brand, result, post_preview)
            return bundle.suggestions
        except Exception:
            logger.warning(
                "CommenterAgent LLM failed; using deterministic suggestions",
                exc_info=True,
            )
            return self._fallback_suggestions(brand, result, post_preview)

    def preview_thread(
        self,
        *,
        post_preview: str,
        estimated_comments: int,
    ) -> list[str]:
        """Return 3–5 recent-comment style previews for the UI."""
        snippet = post_preview.strip()[:60] or "this"
        return [
            f"Love this — {snippet}!",
            "The colours are incredible",
            "Where did you get the materials?",
            "Saving this for inspiration",
            f"So many comments already (~{estimated_comments}) — still worth joining",
        ][:5]

    def _generate_with_llm(
        self,
        brand: BrandProfile,
        result: BrandResearchResult,
        post_preview: str,
    ) -> _CommentBundle:
        settings = get_settings()
        prompt = f"""
You write Instagram comments for brand outreach.

Brand: {brand.name}
Brand tone: {brand.tone_of_voice}
Brand values: {", ".join(brand.values)}
Creator: {result.profile.name}
Post: {post_preview}
Seed comment: {result.analysis.comment}

Return exactly 3 distinct comment suggestions (1-2 sentences, natural, no hashtags spam)
and 3-5 short example comments that might already appear under the post.
""".strip()
        completion = self.client.chat.completions.parse(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You write natural Instagram comments for brand outreach. "
                        "No hashtag spam. Keep comments short and specific."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format=_CommentBundle,
        )
        parsed = completion.choices[0].message.parsed
        if parsed is None:
            raise RuntimeError("CommenterAgent returned empty parse result")
        return parsed

    def _fallback_suggestions(
        self,
        brand: BrandProfile,
        result: BrandResearchResult,
        post_preview: str,
    ) -> list[str]:
        seed = result.analysis.comment.strip() or (
            f"Really love how this captures {brand.values[0] if brand.values else 'your craft'}."
        )
        focus = post_preview.strip()[:80] or "your latest post"
        return [
            seed,
            f"This is beautiful — {focus}. The storytelling feels so aligned with {brand.name}.",
            (
                f"Stopping by from the {brand.name} world — "
                f"your take on this is inspiring. Would love to connect!"
            ),
        ]
