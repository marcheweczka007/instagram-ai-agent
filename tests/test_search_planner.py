from datetime import timedelta
from pathlib import Path

import pytest

from instagram_agent.agents.search_planner import SearchPlannerAgent
from instagram_agent.domain.models import (
    BrandResearchResult,
    CommentOpportunity,
    InstagramProfile,
    OpportunityScoreBreakdown,
    OpportunityTimeBreakdown,
    ProfileAnalysis,
    ResearchAnalysis,
    SearchPlan,
)
from instagram_agent.fixtures import build_jollyzu_brand
from instagram_agent.services.discovery_orchestrator import DiscoveryOrchestrator
from instagram_agent.services.search_channels.base import (
    ChannelSearchResult,
    SearchChannel,
)
from instagram_agent.services.search_history import SearchHistoryStore


class _FakeChannel(SearchChannel):
    name = "fake"

    def __init__(self, mapping: dict[str, list[str]]) -> None:
        self.mapping = mapping
        self.calls: list[str] = []

    async def search(self, query: str) -> ChannelSearchResult:
        self.calls.append(query)
        return ChannelSearchResult(
            channel=self.name,
            query=query,
            profile_urls=list(self.mapping.get(query, [])),
        )


def test_search_planner_fallback_has_at_least_30_queries() -> None:
    brand = build_jollyzu_brand()
    plan = SearchPlannerAgent()._fallback_plan(brand)
    assert len(plan.search_queries) >= 30
    assert plan.core_themes
    assert "handmade bags UK" in plan.search_queries or any(
        "handmade" in q.lower() for q in plan.search_queries
    )


def test_search_history_ranks_successful_queries(tmp_path: Path) -> None:
    store = SearchHistoryStore(path=tmp_path / "history.json")
    store.record_run("weak query", ["https://www.instagram.com/a/"])
    store.record_run("strong query", ["https://www.instagram.com/b/"])

    results = [
        BrandResearchResult(
            profile=InstagramProfile(
                name="B",
                profile_url="https://www.instagram.com/b/",
                bio="x",
                followers=1000,
                following=1,
                recent_posts=["post"],
            ),
            analysis=ProfileAnalysis(score=8, follow=True, reason="r", comment="c"),
            research=ResearchAnalysis(
                brand_fit=9,
                confidence=8,
                audience_match="a",
                aesthetic_match="a",
                value_alignment="v",
                collaboration_potential="c",
                overall_summary="o",
                strengths=[],
                weaknesses=[],
                collaboration_ideas=[],
                first_outreach_angle="hi",
            ),
        )
    ]
    opportunities = [
        CommentOpportunity(
            id="1",
            creator_name="B",
            creator_url="https://www.instagram.com/b/",
            profile_picture_url="https://example.com/x.png",
            brand_fit=9,
            opportunity_score=88,
            priority="High",
            post_preview="post",
            post_url="https://www.instagram.com/b/",
            why_now="now",
            score_breakdown=OpportunityScoreBreakdown(
                brand_fit=30,
                post_freshness=20,
                comment_room=15,
                brand_similarity=12,
                visibility_potential=11,
            ),
            score_explanation="x",
            comment_suggestions=["a", "b", "c"],
            time_breakdown=OpportunityTimeBreakdown(),
        )
    ]
    store.record_outcomes(
        query_sources={"https://www.instagram.com/b/": ["strong query"]},
        results=results,
        opportunities=opportunities,
    )
    ranked = store.rank_queries(["weak query", "strong query"])
    assert ranked[0] == "strong query"
    assert store.get_stats("strong query").weight > store.get_stats("weak query").weight


def test_search_history_skips_recent_queries(tmp_path: Path) -> None:
    store = SearchHistoryStore(path=tmp_path / "history.json")
    store.record_run(
        "recent query",
        ["https://www.instagram.com/cached/"],
    )
    # Force last_run_at to now (already set by record_run).
    to_run, skipped, cached = store.partition_queries(["recent query", "fresh query"])
    assert "recent query" in skipped
    assert "fresh query" in to_run
    assert cached["recent query"] == ["https://www.instagram.com/cached/"]


@pytest.mark.asyncio
async def test_orchestrator_merges_and_dedupes(tmp_path: Path) -> None:
    brand = build_jollyzu_brand()
    plan = SearchPlan(
        core_themes=["bags"],
        adjacent_themes=["craft"],
        search_keywords=["bags"],
        hashtags=["bags"],
        creator_archetypes=["maker"],
        brand_archetypes=["indie"],
        search_queries=["q1", "q2", "q3"],
    )
    channel = _FakeChannel(
        {
            "q1": [
                "https://www.instagram.com/one/",
                "https://www.instagram.com/two/",
            ],
            "q2": ["https://www.instagram.com/two/"],
            "q3": ["https://www.instagram.com/three/"],
        }
    )
    history = SearchHistoryStore(path=tmp_path / "history.json")
    # Make cooldown tiny by patching after init
    history._cooldown = timedelta(hours=48)

    planner = SearchPlannerAgent()
    orchestrator = DiscoveryOrchestrator(
        planner=planner,
        channels=[channel],
        history=history,
    )
    result = await orchestrator.discover_for_brand(brand, plan=plan)
    assert result.profile_urls == [
        "https://www.instagram.com/one/",
        "https://www.instagram.com/two/",
        "https://www.instagram.com/three/",
    ]
    assert set(channel.calls) == {"q1", "q2", "q3"}
    assert "q1" in result.query_sources["https://www.instagram.com/one/"]
    assert "q1" in result.query_sources["https://www.instagram.com/two/"]
    assert "q2" in result.query_sources["https://www.instagram.com/two/"]

    # Second run should skip all queries and reuse cache.
    channel.calls.clear()
    result2 = await orchestrator.discover_for_brand(brand, plan=plan)
    assert channel.calls == []
    assert set(result2.queries_skipped) >= {"q1", "q2", "q3"}
    assert "https://www.instagram.com/one/" in result2.profile_urls
