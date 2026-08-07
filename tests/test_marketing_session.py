from instagram_agent.domain.models import (
    BrandResearchResult,
    InstagramProfile,
    ProfileAnalysis,
    ResearchAnalysis,
)
from instagram_agent.services.marketing_session import (
    build_marketing_tasks,
    creator_cap_for_duration,
    extract_instagram_username,
    priority_from_brand_fit,
    resolve_brand_and_query,
    session_stats,
)


def _result(name: str, brand_fit: int) -> BrandResearchResult:
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
            comment=f"Nice work {name}",
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
            first_outreach_angle=f"Hi {name}",
        ),
    )


def test_priority_and_caps() -> None:
    assert priority_from_brand_fit(9) == "High"
    assert creator_cap_for_duration(15) == 5
    assert creator_cap_for_duration(60) == 20


def test_resolve_jollyzu_brand() -> None:
    brand, query = resolve_brand_and_query(
        "https://www.instagram.com/upcycle.lab.jollyzu/"
    )
    assert brand.name == "JollyZu"
    assert query == "upcycled bags"


def test_username_extraction() -> None:
    assert (
        extract_instagram_username("https://www.instagram.com/patagonia/")
        == "patagonia"
    )


def test_marketing_tasks_and_stats() -> None:
    results = [
        _result("A", 9),
        _result("B", 8),
        _result("C", 6),
    ]
    tasks = build_marketing_tasks(results)
    assert len(tasks) == 3
    assert tasks[0].action == "Comment"
    assert tasks[1].action == "Send DM"
    assert tasks[2].action == "Research"

    stats = session_stats(results)
    assert stats["creators_analysed"] == 3
    assert stats["high_priority"] == 1
    assert stats["average_brand_fit"] == 7.7
