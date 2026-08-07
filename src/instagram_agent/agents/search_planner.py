"""AI Search Planner — BrandProfile → SearchPlan (channel-agnostic)."""

from __future__ import annotations

import logging
from pathlib import Path

from instagram_agent.agents.base import BaseAgent
from instagram_agent.config import get_settings
from instagram_agent.domain.models import BrandProfile, SearchPlan

logger = logging.getLogger(__name__)

_MIN_QUERIES = 30


class SearchPlannerAgent(BaseAgent):
    """Generate a diverse, ranked-ready search plan for a brand."""

    def __init__(self, client=None, *, min_queries: int | None = None) -> None:
        super().__init__(client=client)
        prompt_path = Path(__file__).parent.parent / "prompts" / "search_planner.md"
        self._system_prompt = prompt_path.read_text(encoding="utf-8")
        self._model = get_settings().openai_model
        self._min_queries = min_queries or get_settings().discovery_min_plan_queries

    def plan(self, brand: BrandProfile) -> SearchPlan:
        """Return a SearchPlan with at least ``min_queries`` diverse queries."""
        try:
            plan = self._plan_with_llm(brand)
        except Exception:
            logger.warning(
                "SearchPlannerAgent LLM failed; using deterministic fallback",
                exc_info=True,
            )
            plan = self._fallback_plan(brand)

        plan = self._ensure_min_queries(brand, plan)
        logger.info(
            "Search plan ready for %s (%s queries, %s core themes)",
            brand.name,
            len(plan.search_queries),
            len(plan.core_themes),
        )
        return plan

    def _plan_with_llm(self, brand: BrandProfile) -> SearchPlan:
        user_prompt = f"""
Brand name: {brand.name}
Description: {brand.description}
Target audience: {", ".join(brand.target_audience)}
Values: {", ".join(brand.values)}
Products: {", ".join(brand.products)}
Tone of voice: {brand.tone_of_voice}

Generate at least {self._min_queries} diverse search_queries.
""".strip()
        completion = self.client.chat.completions.parse(
            model=self._model,
            messages=[
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format=SearchPlan,
        )
        parsed = completion.choices[0].message.parsed
        if parsed is None:
            raise RuntimeError("SearchPlannerAgent returned empty SearchPlan")
        return parsed

    def _ensure_min_queries(self, brand: BrandProfile, plan: SearchPlan) -> SearchPlan:
        queries = _dedupe_queries(list(plan.search_queries))
        if len(queries) >= self._min_queries:
            return plan.model_copy(update={"search_queries": queries})

        fallback = self._fallback_plan(brand)
        merged = _dedupe_queries(queries + fallback.search_queries)
        return plan.model_copy(
            update={
                "search_queries": merged[: max(self._min_queries, len(merged))],
                "core_themes": plan.core_themes or fallback.core_themes,
                "adjacent_themes": plan.adjacent_themes or fallback.adjacent_themes,
                "search_keywords": plan.search_keywords or fallback.search_keywords,
                "hashtags": plan.hashtags or fallback.hashtags,
                "creator_archetypes": plan.creator_archetypes
                or fallback.creator_archetypes,
                "brand_archetypes": plan.brand_archetypes or fallback.brand_archetypes,
            }
        )

    def _fallback_plan(self, brand: BrandProfile) -> SearchPlan:
        seeds = _dedupe_queries(
            [
                *brand.products,
                *brand.values,
                *brand.target_audience,
                brand.name,
            ]
        )
        themes = seeds[:6] or ["handmade", "slow fashion"]
        adjacent = [
            "repair culture",
            "visible mending",
            "textile artist",
            "craft business",
            "eco lifestyle",
            "independent maker",
            "artisan accessories",
            "creative sewing",
        ]
        archetypes = [
            "slow fashion creator",
            "ethical fashion blogger",
            "handmade bags UK",
            "upcycled clothing",
            "outdoor handmade gear",
            "colourful fashion",
        ]
        queries: list[str] = []
        for theme in themes:
            queries.extend(
                [
                    theme,
                    f"{theme} creator",
                    f"{theme} maker",
                    f"{theme} Instagram",
                    f"{theme} small business",
                ]
            )
        queries.extend(adjacent)
        queries.extend(archetypes)
        queries.extend(
            [
                "handmade bags UK",
                "slow fashion creator",
                "ethical fashion blogger",
                "independent maker",
                "artisan accessories",
                "eco lifestyle creator",
                "colourful fashion",
                "textile artist",
                "craft business",
                "outdoor handmade gear",
                "repair culture",
                "visible mending",
                "upcycled clothing",
                "creative sewing",
                "zero waste fashion",
                "circular fashion maker",
                "reclaimed materials design",
                "cottagecore handmade",
                "studio craft fashion",
                "slow living creator",
            ]
        )
        queries = _dedupe_queries(queries)
        while len(queries) < self._min_queries:
            queries.append(f"{themes[0]} creator niche {len(queries)}")
        return SearchPlan(
            core_themes=themes,
            adjacent_themes=adjacent,
            search_keywords=themes + adjacent[:8],
            hashtags=[t.replace(" ", "") for t in themes[:8]],
            creator_archetypes=archetypes,
            brand_archetypes=[f"{brand.name} style brand", "indie craft label"],
            search_queries=queries[: max(self._min_queries, 30)],
        )


def _dedupe_queries(queries: list[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for query in queries:
        cleaned = " ".join(str(query).split()).strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(cleaned)
    return unique
