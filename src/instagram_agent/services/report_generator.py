"""Generate human-readable brand research reports from structured results."""

from __future__ import annotations

import logging
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from instagram_agent.config import get_settings
from instagram_agent.domain.models import BrandProfile, BrandResearchResult

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Format brand research results as Markdown for marketing managers."""

    def generate(
        self,
        brand: BrandProfile,
        results: list[BrandResearchResult],
    ) -> str:
        """Return a complete Brand Research Report as Markdown."""
        logger.info(
            "Generating brand research report for %s (%s profiles)",
            brand.name,
            len(results),
        )
        settings = get_settings()
        ranked = sorted(
            results,
            key=lambda item: item.research.brand_fit,
            reverse=True,
        )
        sections = [
            self._render_header(brand, ranked),
            self._render_top_matches(ranked),
            self._render_recommended(
                ranked,
                min_fit=settings.recommend_brand_fit_min,
            ),
            self._render_to_avoid(
                ranked,
                max_fit=settings.avoid_brand_fit_max,
            ),
            self._render_overall_insights(brand, ranked),
        ]
        report = "\n\n".join(section for section in sections if section)
        logger.info("Brand research report generated (%s characters)", len(report))
        return report

    def _render_header(
        self,
        brand: BrandProfile,
        results: list[BrandResearchResult],
    ) -> str:
        average_fit = self._average_brand_fit(results)
        average_text = f"{average_fit:.1f}" if average_fit is not None else "n/a"
        return "\n".join(
            [
                "# Brand Research Report",
                "",
                f"**Brand:** {brand.name}",
                "",
                f"**Date:** {datetime.now(UTC).date().isoformat()}",
                "",
                f"**Profiles analysed:** {len(results)}",
                "",
                f"**Average Brand Fit:** {average_text}",
                "",
                "---",
            ]
        )

    def _render_top_matches(self, results: list[BrandResearchResult]) -> str:
        lines = ["## Top Matches", ""]
        if not results:
            lines.append("_No creators were analysed._")
        else:
            for index, result in enumerate(results):
                if index:
                    lines.append("")
                lines.extend(self._render_creator_block(result))

        lines.extend(["", "---"])
        return "\n".join(lines)

    def _render_creator_block(self, result: BrandResearchResult) -> list[str]:
        research = result.research
        profile = result.profile
        return [
            f"### {profile.name}",
            "",
            f"- **Instagram URL:** {profile.profile_url}",
            f"- **Followers:** {profile.followers:,}",
            f"- **Brand Fit:** {research.brand_fit}/10",
            f"- **Confidence:** {research.confidence}/10",
            "",
            "**Overall Summary**",
            "",
            research.overall_summary,
            "",
            "**Strengths**",
            "",
            *self._bullet_list(research.strengths),
            "",
            "**Weaknesses**",
            "",
            *self._bullet_list(research.weaknesses),
            "",
            "**Collaboration Ideas**",
            "",
            *self._bullet_list(research.collaboration_ideas),
            "",
            f"**First Outreach Angle:** {research.first_outreach_angle}",
        ]

    def _render_recommended(
        self,
        results: list[BrandResearchResult],
        *,
        min_fit: int,
    ) -> str:
        recommended = [item for item in results if item.research.brand_fit >= min_fit]
        lines = ["## Recommended Creators", ""]
        if not recommended:
            lines.append(f"_No creators scored brand fit {min_fit} or higher._")
            lines.extend(["", "---"])
            return "\n".join(lines)

        for result in recommended:
            reason = (
                f"{result.profile.name} should be prioritised because "
                f"{self._first_sentence(result.research.overall_summary)} "
                f"(brand fit {result.research.brand_fit}/10)."
            )
            lines.append(f"- **{result.profile.name}** — {reason}")
        lines.extend(["", "---"])
        return "\n".join(lines)

    def _render_to_avoid(
        self,
        results: list[BrandResearchResult],
        *,
        max_fit: int,
    ) -> str:
        weak = [item for item in results if item.research.brand_fit <= max_fit]
        lines = ["## Creators To Avoid", ""]
        if not weak:
            lines.append(f"_No creators scored brand fit {max_fit} or lower._")
            lines.extend(["", "---"])
            return "\n".join(lines)

        for result in weak:
            weakness = (
                result.research.weaknesses[0]
                if result.research.weaknesses
                else result.research.overall_summary
            )
            lines.append(
                f"- **{result.profile.name}** — Poor fit "
                f"(brand fit {result.research.brand_fit}/10): {weakness}"
            )
        lines.extend(["", "---"])
        return "\n".join(lines)

    def _render_overall_insights(
        self,
        brand: BrandProfile,
        results: list[BrandResearchResult],
    ) -> str:
        lines = ["## Overall Insights", ""]
        if not results:
            lines.append("_Not enough data to derive insights._")
            return "\n".join(lines)

        strengths = self._top_phrases(
            [item for result in results for item in result.research.strengths]
        )
        weaknesses = self._top_phrases(
            [item for result in results for item in result.research.weaknesses]
        )
        ideas = self._top_phrases(
            [item for result in results for item in result.research.collaboration_ideas]
        )
        avg = self._average_brand_fit(results)
        avg_text = f"{avg:.1f}" if avg is not None else "n/a"

        lines.extend(
            [
                (
                    f"**Common audience characteristics:** Across {len(results)} "
                    f"creators researched for {brand.name}, audience notes most often "
                    f"point to: {self._join_audience_notes(results)}."
                ),
                "",
                f"**Common strengths:** {self._join_phrases(strengths)}",
                "",
                f"**Common weaknesses:** {self._join_phrases(weaknesses)}",
                "",
                (
                    f"**Interesting trends:** Average brand fit is {avg_text}/10. "
                    "Higher-confidence matches tend to align with "
                    f"{', '.join(brand.values[:3]) or 'core brand values'}."
                ),
                "",
                (f"**Potential campaign opportunities:** {self._join_phrases(ideas)}"),
            ]
        )
        return "\n".join(lines)

    @staticmethod
    def _average_brand_fit(results: list[BrandResearchResult]) -> float | None:
        if not results:
            return None
        total = sum(result.research.brand_fit for result in results)
        return total / len(results)

    @staticmethod
    def _bullet_list(items: list[str]) -> list[str]:
        if not items:
            return ["- _None noted_"]
        return [f"- {item}" for item in items]

    @staticmethod
    def _first_sentence(text: str) -> str:
        cleaned = " ".join(text.split())
        if not cleaned:
            return "they show meaningful brand alignment"
        for separator in (". ", "! ", "? "):
            if separator in cleaned:
                sentence = cleaned.split(separator, maxsplit=1)[0].rstrip(".")
                return sentence[0].lower() + sentence[1:] if sentence else cleaned
        return cleaned[0].lower() + cleaned[1:] if cleaned else cleaned

    @staticmethod
    def _top_phrases(items: list[str], limit: int = 5) -> list[str]:
        if not items:
            return []
        counts = Counter(item.strip() for item in items if item.strip())
        return [phrase for phrase, _ in counts.most_common(limit)]

    @staticmethod
    def _join_phrases(items: list[str]) -> str:
        if not items:
            return "_No recurring themes identified._"
        return "; ".join(items)

    @staticmethod
    def _join_audience_notes(results: list[BrandResearchResult]) -> str:
        notes = [
            result.research.audience_match.strip()
            for result in results
            if result.research.audience_match.strip()
        ]
        if not notes:
            return "no clear shared audience pattern"
        # Keep report readable: show up to three distinct notes.
        unique: list[str] = []
        for note in notes:
            if note not in unique:
                unique.append(note)
            if len(unique) == 3:
                break
        return "; ".join(unique)


def save_markdown(report: str, output_path: str) -> None:
    """Write a Markdown report to ``output_path``."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")
    logger.info("Saved Markdown report to %s", path)
