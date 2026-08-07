"""Export brand research summaries as JSON."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from instagram_agent.domain.models import BrandProfile, BrandResearchResult

logger = logging.getLogger(__name__)


class JsonExporter:
    """Write a compact JSON summary of brand research results."""

    def export(
        self,
        brand: BrandProfile,
        results: list[BrandResearchResult],
        output_path: str,
    ) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        ranked = sorted(
            results,
            key=lambda item: item.research.brand_fit,
            reverse=True,
        )
        payload = {
            "brand": brand.model_dump(),
            "generated_at": datetime.now(UTC).isoformat(),
            "profiles_analysed": len(ranked),
            "average_brand_fit": (
                round(
                    sum(item.research.brand_fit for item in ranked) / len(ranked),
                    2,
                )
                if ranked
                else None
            ),
            "results": [
                {
                    "profile": item.profile.model_dump(),
                    "analysis": item.analysis.model_dump(),
                    "research": item.research.model_dump(),
                }
                for item in ranked
            ],
        }

        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        logger.info("Wrote JSON summary (%s rows) to %s", len(ranked), path)
