"""Export analysis (and optional brand-research) results to CSV."""

from __future__ import annotations

import csv
import logging
from pathlib import Path

from instagram_agent.domain.models import AnalysisResult, BrandResearchResult

logger = logging.getLogger(__name__)

_BASE_COLUMNS: tuple[str, ...] = (
    "profile_name",
    "profile_url",
    "followers",
    "following",
    "score",
    "follow",
    "reason",
    "comment",
)

_RESEARCH_COLUMNS: tuple[str, ...] = (
    "brand_fit",
    "confidence",
    "first_outreach_angle",
    "overall_summary",
)

ExportableResult = AnalysisResult | BrandResearchResult


class CsvExporter:
    """Write analysis rows to a CSV file."""

    def export(
        self,
        results: list[ExportableResult],
        output_path: str,
    ) -> None:
        path = Path(output_path)
        logger.info("Export started → %s", path)

        if not results:
            logger.warning("No analysis results to export; writing header only")

        include_research = any(
            isinstance(result, BrandResearchResult) for result in results
        )
        fieldnames = (
            _BASE_COLUMNS + _RESEARCH_COLUMNS if include_research else _BASE_COLUMNS
        )

        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for result in results:
                writer.writerow(self._to_row(result, include_research=include_research))

        logger.info("Wrote %s data row(s) to %s", len(results), path)
        logger.info("Export completed")

    @staticmethod
    def _to_row(
        result: ExportableResult,
        *,
        include_research: bool,
    ) -> dict[str, str | int | bool]:
        row: dict[str, str | int | bool] = {
            "profile_name": result.profile.name,
            "profile_url": result.profile.profile_url,
            "followers": result.profile.followers,
            "following": result.profile.following,
            "score": result.analysis.score,
            "follow": result.analysis.follow,
            "reason": result.analysis.reason,
            "comment": result.analysis.comment,
        }

        if include_research:
            if isinstance(result, BrandResearchResult):
                row.update(
                    {
                        "brand_fit": result.research.brand_fit,
                        "confidence": result.research.confidence,
                        "first_outreach_angle": result.research.first_outreach_angle,
                        "overall_summary": result.research.overall_summary,
                    }
                )
            else:
                row.update(
                    {
                        "brand_fit": "",
                        "confidence": "",
                        "first_outreach_angle": "",
                        "overall_summary": "",
                    }
                )

        return row
