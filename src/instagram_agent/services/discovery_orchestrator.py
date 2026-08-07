"""Orchestrate AI search planning + multi-query channel discovery."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable

from instagram_agent.agents.search_planner import SearchPlannerAgent
from instagram_agent.config import get_settings
from instagram_agent.domain.models import BrandProfile, DiscoveryResult, SearchPlan
from instagram_agent.services.search_channels import (
    GoogleInstagramSearchChannel,
    SearchChannel,
)
from instagram_agent.services.search_history import SearchHistoryStore

logger = logging.getLogger(__name__)

ProgressFn = Callable[[str], None]


class DiscoveryOrchestrator:
    """Plan many queries, execute channels, merge/dedupe, learn over time.

    SearchPlanner stays channel-agnostic. New sources (TikTok, Reddit, …)
    plug in as additional ``SearchChannel`` instances.
    """

    def __init__(
        self,
        *,
        planner: SearchPlannerAgent | None = None,
        channels: list[SearchChannel] | None = None,
        history: SearchHistoryStore | None = None,
    ) -> None:
        self._planner = planner or SearchPlannerAgent()
        self._channels = channels or [GoogleInstagramSearchChannel()]
        self._history = history or SearchHistoryStore()

    async def discover_for_brand(
        self,
        brand: BrandProfile,
        *,
        deadline: float | None = None,
        on_progress: ProgressFn | None = None,
        plan: SearchPlan | None = None,
    ) -> DiscoveryResult:
        """Run the full AI-planned discovery flow for ``brand``."""
        settings = get_settings()
        search_plan = plan or self._planner.plan(brand)
        queries = list(search_plan.search_queries)
        if len(queries) < settings.discovery_min_plan_queries:
            logger.warning(
                "Search plan has only %s queries (expected >= %s)",
                len(queries),
                settings.discovery_min_plan_queries,
            )

        to_run, skipped, cached = self._history.partition_queries(queries)
        max_run = settings.discovery_max_queries_per_run
        if max_run > 0 and len(to_run) > max_run:
            # Keep highest-weight queries; remainder treated like deferred.
            deferred = to_run[max_run:]
            to_run = to_run[:max_run]
            skipped.extend(deferred)
            logger.info(
                "Capping discovery to top %s weighted queries (%s deferred)",
                max_run,
                len(deferred),
            )

        def emit(message: str) -> None:
            logger.info(message)
            if on_progress is not None:
                on_progress(message)

        emit(
            f"Search plan: {len(queries)} queries "
            f"({len(to_run)} to run, {len(skipped)} skipped/cached)"
        )

        url_sources: dict[str, list[str]] = {}
        ordered_urls: list[str] = []
        seen: set[str] = set()

        def _add(url: str, query: str) -> None:
            normalized = url if url.endswith("/") else f"{url}/"
            key = normalized.rstrip("/").lower()
            sources = url_sources.setdefault(normalized, [])
            if query not in sources:
                sources.append(query)
            if key not in seen:
                seen.add(key)
                ordered_urls.append(normalized)

        for query, urls in cached.items():
            for url in urls:
                _add(url, query)

        queries_run: list[str] = []
        for index, query in enumerate(to_run, start=1):
            if deadline is not None and time.perf_counter() >= deadline:
                emit("Discovery time budget reached — stopping remaining queries")
                skipped.extend(to_run[index - 1 :])
                break
            emit(f"Searching [{index}/{len(to_run)}]: {query}")
            urls_for_query: list[str] = []
            for channel in self._channels:
                try:
                    result = await channel.search(query)
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "Channel %s failed for %r: %s",
                        channel.name,
                        query,
                        exc,
                    )
                    continue
                urls_for_query.extend(result.profile_urls)
                for url in result.profile_urls:
                    _add(url, query)
            queries_run.append(query)
            unique_urls = list(dict.fromkeys(urls_for_query))
            self._history.record_run(query, unique_urls)

        max_results = settings.discovery_max_results
        profile_urls = ordered_urls[:max_results]
        trimmed_sources = {url: url_sources.get(url, []) for url in profile_urls}
        emit(f"Discovery merged {len(profile_urls)} unique creators")
        return DiscoveryResult(
            profile_urls=profile_urls,
            query_sources=trimmed_sources,
            search_plan=search_plan,
            queries_run=queries_run,
            queries_skipped=skipped,
        )

    @property
    def history(self) -> SearchHistoryStore:
        return self._history
