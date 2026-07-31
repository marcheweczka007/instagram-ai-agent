"""Export analysis results to CSV."""

from __future__ import annotations

import csv
import logging
from pathlib import Path

from instagram_agent.domain.models import AnalysisResult

logger = logging.getLogger(__name__)

_CSV_COLUMNS: tuple[str, ...] = (
    "profile_name",
    "profile_url",
    "followers",
    "following",
    "score",
    "follow",
    "reason",
    "comment",
)


class CsvExporter:
    """Write ``AnalysisResult`` rows to a CSV file."""

    def export(
        self,
        results: list[AnalysisResult],
        output_path: str,
    ) -> None:
        path = Path(output_path)
        logger.info("Export started → %s", path)

        if not results:
            logger.warning("No analysis results to export; writing header only")

        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=_CSV_COLUMNS)
            writer.writeheader()
            for result in results:
                writer.writerow(self._to_row(result))

        logger.info("Wrote %s data row(s) to %s", len(results), path)
        logger.info("Export completed")

    @staticmethod
    def _to_row(result: AnalysisResult) -> dict[str, str | int | bool]:
        return {
            "profile_name": result.profile.name,
            "profile_url": result.profile.profile_url,
            "followers": result.profile.followers,
            "following": result.profile.following,
            "score": result.analysis.score,
            "follow": result.analysis.follow,
            "reason": result.analysis.reason,
            "comment": result.analysis.comment,
        }
