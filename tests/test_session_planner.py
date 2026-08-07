from instagram_agent.domain.models import (
    CommentOpportunity,
    OpportunityScoreBreakdown,
    OpportunityTimeBreakdown,
)
from instagram_agent.services.session_planner import (
    impact_to_stars,
    plan_marketing_session,
)


def _opp(
    *,
    opp_id: str,
    score: float,
    minutes: int,
    impact: str = "High",
) -> CommentOpportunity:
    seconds = minutes * 60
    return CommentOpportunity(
        id=opp_id,
        creator_name=f"Creator {opp_id}",
        creator_url=f"https://www.instagram.com/{opp_id}/",
        profile_picture_url="https://example.com/a.png",
        brand_fit=8,
        opportunity_score=score,
        priority="High" if score >= 70 else "Medium",
        marketing_impact=impact,  # type: ignore[arg-type]
        estimated_time_seconds=seconds,
        estimated_time_label=f"~{minutes} min",
        time_breakdown=OpportunityTimeBreakdown(),
        post_preview="post",
        post_url=f"https://www.instagram.com/{opp_id}/",
        why_now="now",
        score_breakdown=OpportunityScoreBreakdown(
            brand_fit=28,
            post_freshness=18,
            comment_room=12,
            brand_similarity=10,
            visibility_potential=12,
        ),
        score_explanation="x",
        comment_suggestions=["a", "b", "c"],
    )


def test_plan_maximises_score_not_first_n() -> None:
    # First cards are low score; later cards are high score but fit better.
    opportunities = [
        _opp(opp_id="a", score=40, minutes=20),
        _opp(opp_id="b", score=40, minutes=20),
        _opp(opp_id="c", score=90, minutes=10, impact="Very High"),
        _opp(opp_id="d", score=85, minutes=10, impact="Very High"),
        _opp(opp_id="e", score=80, minutes=10, impact="High"),
    ]
    plan = plan_marketing_session(opportunities, available_minutes=30)
    selected_ids = {item.id for item in plan.opportunities}
    assert selected_ids == {"c", "d", "e"}
    assert plan.available_minutes == 30
    assert plan.planned_minutes == 30
    assert plan.buffer_minutes == 0
    assert plan.total_opportunity_score == 255
    assert "maximising total Opportunity Score" in plan.rationale
    assert impact_to_stars(plan.estimated_marketing_impact).startswith("★")


def test_plan_leaves_buffer_when_under_budget() -> None:
    opportunities = [
        _opp(opp_id="a", score=90, minutes=10),
        _opp(opp_id="b", score=80, minutes=10),
    ]
    plan = plan_marketing_session(opportunities, available_minutes=30)
    assert plan.planned_minutes == 20
    assert plan.buffer_minutes == 10
    assert len(plan.opportunities) == 2
