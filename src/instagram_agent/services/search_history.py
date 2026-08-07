"""Persistent search history and query ranking for discovery."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from instagram_agent.config import get_settings
from instagram_agent.domain.models import BrandResearchResult, CommentOpportunity

logger = logging.getLogger(__name__)


@dataclass
class QueryStats:
    query: str
    runs: int = 0
    urls_found: int = 0
    useful_creators: int = 0
    brand_fit_sum: float = 0.0
    brand_fit_count: int = 0
    opportunity_score_sum: float = 0.0
    opportunity_score_count: int = 0
    weight: float = 1.0
    last_run_at: str | None = None
    last_urls: list[str] | None = None

    @property
    def average_brand_fit(self) -> float:
        if self.brand_fit_count <= 0:
            return 0.0
        return round(self.brand_fit_sum / self.brand_fit_count, 2)

    @property
    def average_opportunity_score(self) -> float:
        if self.opportunity_score_count <= 0:
            return 0.0
        return round(self.opportunity_score_sum / self.opportunity_score_count, 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "runs": self.runs,
            "urls_found": self.urls_found,
            "useful_creators": self.useful_creators,
            "brand_fit_sum": self.brand_fit_sum,
            "brand_fit_count": self.brand_fit_count,
            "opportunity_score_sum": self.opportunity_score_sum,
            "opportunity_score_count": self.opportunity_score_count,
            "weight": self.weight,
            "last_run_at": self.last_run_at,
            "last_urls": self.last_urls or [],
            "average_brand_fit": self.average_brand_fit,
            "average_opportunity_score": self.average_opportunity_score,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QueryStats:
        return cls(
            query=str(data.get("query", "")),
            runs=int(data.get("runs", 0)),
            urls_found=int(data.get("urls_found", 0)),
            useful_creators=int(data.get("useful_creators", 0)),
            brand_fit_sum=float(data.get("brand_fit_sum", 0.0)),
            brand_fit_count=int(data.get("brand_fit_count", 0)),
            opportunity_score_sum=float(data.get("opportunity_score_sum", 0.0)),
            opportunity_score_count=int(data.get("opportunity_score_count", 0)),
            weight=float(data.get("weight", 1.0)),
            last_run_at=data.get("last_run_at"),
            last_urls=list(data.get("last_urls") or []),
        )


class SearchHistoryStore:
    """JSON-backed history used to skip recent queries and rank strategies."""

    def __init__(self, path: Path | None = None) -> None:
        settings = get_settings()
        settings.ensure_output_dirs()
        self._path = path or (settings.output_dir / "search" / "search_history.json")
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._cooldown = timedelta(hours=settings.discovery_query_cooldown_hours)
        self._stats: dict[str, QueryStats] = {}
        self._load()

    def rank_queries(self, queries: list[str]) -> list[str]:
        """Return queries sorted by learned weight (best strategies first)."""
        return sorted(
            queries,
            key=lambda query: self.get_stats(query).weight,
            reverse=True,
        )

    def partition_queries(
        self, queries: list[str]
    ) -> tuple[list[str], list[str], dict[str, list[str]]]:
        """Split into (to_run, skipped, cached_urls_by_query)."""
        ranked = self.rank_queries(queries)
        to_run: list[str] = []
        skipped: list[str] = []
        cached: dict[str, list[str]] = {}
        now = datetime.now(UTC)
        for query in ranked:
            stats = self.get_stats(query)
            if self._is_recent(stats, now) and stats.last_urls:
                skipped.append(query)
                cached[query] = list(stats.last_urls)
            else:
                to_run.append(query)
        return to_run, skipped, cached

    def record_run(self, query: str, profile_urls: list[str]) -> None:
        stats = self.get_stats(query)
        stats.runs += 1
        stats.urls_found += len(profile_urls)
        stats.last_run_at = datetime.now(UTC).isoformat()
        stats.last_urls = list(profile_urls)
        stats.weight = self._compute_weight(stats)
        self._stats[_key(query)] = stats
        self._save()

    def record_outcomes(
        self,
        *,
        query_sources: dict[str, list[str]],
        results: list[BrandResearchResult],
        opportunities: list[CommentOpportunity] | None = None,
        useful_brand_fit_min: float = 7.0,
    ) -> None:
        """Update query weights from research / opportunity outcomes."""
        url_to_fit = {
            item.profile.profile_url.rstrip("/").lower(): item.research.brand_fit
            for item in results
        }
        url_to_opp: dict[str, float] = {}
        if opportunities:
            for opportunity in opportunities:
                key = opportunity.creator_url.rstrip("/").lower()
                url_to_opp[key] = max(
                    url_to_opp.get(key, 0.0), opportunity.opportunity_score
                )

        touched: set[str] = set()
        for url, queries in query_sources.items():
            url_key = url.rstrip("/").lower()
            brand_fit = url_to_fit.get(url_key)
            opp_score = url_to_opp.get(url_key)
            for query in queries:
                stats = self.get_stats(query)
                if brand_fit is not None:
                    stats.brand_fit_sum += brand_fit
                    stats.brand_fit_count += 1
                    if brand_fit >= useful_brand_fit_min:
                        stats.useful_creators += 1
                if opp_score is not None:
                    stats.opportunity_score_sum += opp_score
                    stats.opportunity_score_count += 1
                stats.weight = self._compute_weight(stats)
                self._stats[_key(query)] = stats
                touched.add(_key(query))

        if touched:
            self._save()
            logger.info("Updated search history weights for %s queries", len(touched))

    def get_stats(self, query: str) -> QueryStats:
        key = _key(query)
        if key not in self._stats:
            self._stats[key] = QueryStats(query=query.strip())
        return self._stats[key]

    def _is_recent(self, stats: QueryStats, now: datetime) -> bool:
        if not stats.last_run_at:
            return False
        try:
            last = datetime.fromisoformat(stats.last_run_at)
        except ValueError:
            return False
        if last.tzinfo is None:
            last = last.replace(tzinfo=UTC)
        return now - last <= self._cooldown

    @staticmethod
    def _compute_weight(stats: QueryStats) -> float:
        """Blend usefulness signals into a ranking weight.

        New queries start at 1.0. Successful strategies climb; weak ones decay.
        """
        base = 1.0
        if stats.runs <= 0:
            return base
        urls_per_run = stats.urls_found / stats.runs
        useful_rate = stats.useful_creators / max(stats.runs, 1)
        avg_fit = stats.average_brand_fit / 10.0
        avg_opp = stats.average_opportunity_score / 100.0
        weight = (
            base
            + 0.35 * min(urls_per_run / 5.0, 2.0)
            + 0.9 * useful_rate
            + 0.6 * avg_fit
            + 0.8 * avg_opp
        )
        return round(max(0.2, weight), 3)

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            logger.warning("Could not read search history at %s", self._path)
            return
        queries = payload.get("queries", {})
        for key, data in queries.items():
            if isinstance(data, dict):
                self._stats[key] = QueryStats.from_dict(data)

    def _save(self) -> None:
        payload = {
            "updated_at": datetime.now(UTC).isoformat(),
            "queries": {key: stats.to_dict() for key, stats in self._stats.items()},
        }
        self._path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _key(query: str) -> str:
    return " ".join(query.lower().split())
