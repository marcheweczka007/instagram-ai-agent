from datetime import datetime
from zoneinfo import ZoneInfo

from instagram_agent.domain.models import (
    BrandResearchResult,
    InstagramProfile,
    ProfileAnalysis,
    ResearchAnalysis,
)
from instagram_agent.services.workspace import (
    build_dashboard_snapshot,
    dm_subject,
    greeting_for_now,
    workspace_stats,
)


def _result(name: str, brand_fit: int, *, comment: str, dm: str) -> BrandResearchResult:
    return BrandResearchResult(
        profile=InstagramProfile(
            name=name,
            profile_url=f"https://www.instagram.com/{name.lower()}/",
            bio="bio",
            followers=1000,
            following=10,
            recent_posts=[],
        ),
        analysis=ProfileAnalysis(
            score=8,
            follow=True,
            reason="fit",
            comment=comment,
        ),
        research=ResearchAnalysis(
            brand_fit=brand_fit,
            confidence=8,
            audience_match="audience",
            aesthetic_match="aesthetic",
            value_alignment="values",
            collaboration_potential="collab",
            overall_summary="summary",
            strengths=["s1"],
            weaknesses=["w1"],
            collaboration_ideas=["idea"],
            first_outreach_angle=dm,
        ),
    )


def test_greeting_morning() -> None:
    morning = datetime(2026, 8, 7, 9, 0, tzinfo=ZoneInfo("Europe/London"))
    assert greeting_for_now(now=morning) == "Good morning Zuza 👋"


def test_workspace_stats_and_dashboard() -> None:
    results = [
        _result("A", 9, comment="hi", dm="dm1"),
        _result("B", 8, comment="", dm="dm2"),
        _result("C", 6, comment="hey", dm=""),
    ]
    stats = workspace_stats(results, weekly_goal=10)
    assert stats["comments_ready"] == 2
    assert stats["dms_ready"] == 2
    assert stats["high_priority"] == 1

    snapshot = build_dashboard_snapshot(results, weekly_goal=10)
    assert snapshot.creators_analysed == 3
    assert snapshot.weekly_goal == 10
    assert len(snapshot.tasks) == 3
    assert "High priority collab" in dm_subject(results[0])
