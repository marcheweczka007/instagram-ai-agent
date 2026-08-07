from instagram_agent.agents.commenter import CommenterAgent
from instagram_agent.domain.models import (
    BrandResearchResult,
    InstagramProfile,
    ProfileAnalysis,
    ResearchAnalysis,
)
from instagram_agent.fixtures import build_jollyzu_brand
from instagram_agent.services.opportunities import (
    HIGH_PRIORITY_THRESHOLD,
    OpportunityService,
    explain_score,
    priority_from_opportunity_score,
    score_opportunity,
)


def _result(
    *, name: str, brand_fit: int, followers: int, posts: list[str]
) -> BrandResearchResult:
    return BrandResearchResult(
        profile=InstagramProfile(
            name=name,
            profile_url=f"https://www.instagram.com/{name.lower()}/",
            bio="upcycled colourful bags",
            followers=followers,
            following=10,
            recent_posts=posts,
        ),
        analysis=ProfileAnalysis(
            score=8,
            follow=True,
            reason="fit",
            comment="Love the upcycled colour story here.",
        ),
        research=ResearchAnalysis(
            brand_fit=brand_fit,
            confidence=9,
            audience_match="eco creative women",
            aesthetic_match="colourful handmade",
            value_alignment="sustainability and craftsmanship",
            collaboration_potential="strong",
            overall_summary="Great fit for colourful upcycled bags",
            strengths=["authentic"],
            weaknesses=["small"],
            collaboration_ideas=["collab drop"],
            first_outreach_angle="Hi!",
        ),
    )


def test_opportunity_score_prefers_fresh_open_threads() -> None:
    brand = build_jollyzu_brand()
    high = score_opportunity(
        brand_fit=9,
        confidence=9,
        followers=8000,
        post_index=0,
        estimated_comments=5,
        brand=brand,
        post_preview="Colourful upcycled bag from reclaimed fabric",
        research_text="sustainability craftsmanship colourful handmade",
    )
    low = score_opportunity(
        brand_fit=4,
        confidence=4,
        followers=500_000,
        post_index=3,
        estimated_comments=200,
        brand=brand,
        post_preview="Random lunch photo",
        research_text="weak match",
    )
    assert high.total > low.total
    assert priority_from_opportunity_score(high.total) == "High"
    assert "Brand Fit" in explain_score(high)


def test_opportunity_service_ranks_by_opportunity_score() -> None:
    brand = build_jollyzu_brand()
    results = [
        _result(
            name="LowFit",
            brand_fit=5,
            followers=400_000,
            posts=["Old lunch photo"],
        ),
        _result(
            name="HighFit",
            brand_fit=10,
            followers=9000,
            posts=["Handmade colourful upcycled tote"],
        ),
    ]
    service = OpportunityService(commenter=CommenterAgent())
    opportunities = service.build_from_results(brand, results)
    assert len(opportunities) == 2
    assert opportunities[0].creator_name == "HighFit"
    assert opportunities[0].opportunity_score >= opportunities[1].opportunity_score
    assert len(opportunities[0].comment_suggestions) == 3
    assert opportunities[0].priority == "High"
    assert opportunities[0].opportunity_score >= HIGH_PRIORITY_THRESHOLD
