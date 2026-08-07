"""Generate ranked comment opportunities after brand research."""

from __future__ import annotations

import hashlib
import logging
import re
from urllib.parse import quote

from instagram_agent.agents.commenter import CommenterAgent
from instagram_agent.domain.models import (
    BrandProfile,
    BrandResearchResult,
    CommentOpportunity,
    OpportunityPriority,
    OpportunityScoreBreakdown,
)

logger = logging.getLogger(__name__)

HIGH_PRIORITY_THRESHOLD = 70.0
MEDIUM_PRIORITY_THRESHOLD = 50.0


def priority_from_opportunity_score(score: float) -> OpportunityPriority:
    if score >= HIGH_PRIORITY_THRESHOLD:
        return "High"
    if score >= MEDIUM_PRIORITY_THRESHOLD:
        return "Medium"
    return "Low"


def profile_picture_url(creator_name: str) -> str:
    return (
        "https://ui-avatars.com/api/"
        f"?name={quote(creator_name)}&background=1f2937&color=fff&size=128"
    )


def estimate_existing_comments(followers: int, post_index: int) -> int:
    """Heuristic comment count when the scraper has no thread data."""
    base = max(followers // 80, 3)
    # Newer posts (index 0) usually have fewer comments than older ones.
    return max(1, int(base * (0.55 + 0.2 * post_index)))


def score_opportunity(
    *,
    brand_fit: int,
    confidence: int,
    followers: int,
    post_index: int,
    estimated_comments: int,
    brand: BrandProfile,
    post_preview: str,
    research_text: str,
) -> OpportunityScoreBreakdown:
    """Combine weighted signals into an explainable Opportunity Score."""
    brand_fit_pts = round((brand_fit / 10) * 35, 1)

    freshness_table = (20.0, 14.0, 9.0, 5.0)
    post_freshness = freshness_table[min(post_index, len(freshness_table) - 1)]

    # Fewer existing comments → more room to be seen.
    if estimated_comments <= 8:
        comment_room = 15.0
    elif estimated_comments <= 25:
        comment_room = 11.0
    elif estimated_comments <= 60:
        comment_room = 7.0
    else:
        comment_room = 3.0

    brand_similarity = _similarity_points(
        brand=brand,
        post_preview=post_preview,
        research_text=research_text,
        confidence=confidence,
    )

    # Mid-size accounts tend to offer the best visibility / effort trade-off.
    if 2_000 <= followers <= 50_000:
        visibility = 15.0
    elif 800 <= followers < 2_000 or 50_000 < followers <= 150_000:
        visibility = 11.0
    elif followers > 150_000:
        visibility = 7.0
    else:
        visibility = 5.0

    return OpportunityScoreBreakdown(
        brand_fit=brand_fit_pts,
        post_freshness=post_freshness,
        comment_room=comment_room,
        brand_similarity=brand_similarity,
        visibility_potential=visibility,
    )


def explain_score(breakdown: OpportunityScoreBreakdown) -> str:
    return (
        f"Opportunity Score {breakdown.total}/100 = "
        f"Brand Fit {breakdown.brand_fit}/35 + "
        f"Post freshness {breakdown.post_freshness}/20 + "
        f"Comment room {breakdown.comment_room}/15 + "
        f"Brand similarity {breakdown.brand_similarity}/15 + "
        f"Visibility potential {breakdown.visibility_potential}/15."
    )


def build_why_now(
    *,
    brand_fit: int,
    post_preview: str,
    estimated_comments: int,
    breakdown: OpportunityScoreBreakdown,
) -> str:
    freshness = (
        "This is their newest post"
        if breakdown.post_freshness >= 18
        else "This post is still relatively fresh"
    )
    return (
        f"{freshness}, Brand Fit is {brand_fit}/10, "
        f"and the thread looks open (~{estimated_comments} comments estimated) "
        f"— commenting now maximises visibility. "
        f"Post focus: {post_preview[:120]}"
    )


class OpportunityService:
    """Build ranked CommentOpportunity rows from research results."""

    def __init__(self, commenter: CommenterAgent | None = None) -> None:
        self._commenter = commenter or CommenterAgent()

    def build_from_results(
        self,
        brand: BrandProfile,
        results: list[BrandResearchResult],
        *,
        posts_per_creator: int = 1,
    ) -> list[CommentOpportunity]:
        opportunities: list[CommentOpportunity] = []
        for result in results:
            posts = result.profile.recent_posts or [
                result.profile.bio or "Latest update"
            ]
            for post_index, post_preview in enumerate(posts[:posts_per_creator]):
                opportunities.append(
                    self._build_one(brand, result, post_preview, post_index)
                )
        opportunities.sort(key=lambda item: item.opportunity_score, reverse=True)
        logger.info("Built %s comment opportunities", len(opportunities))
        return opportunities

    def _build_one(
        self,
        brand: BrandProfile,
        result: BrandResearchResult,
        post_preview: str,
        post_index: int,
    ) -> CommentOpportunity:
        estimated_comments = estimate_existing_comments(
            result.profile.followers, post_index
        )
        research_text = (
            f"{result.research.value_alignment} "
            f"{result.research.aesthetic_match} "
            f"{result.research.audience_match} "
            f"{result.research.overall_summary}"
        )
        breakdown = score_opportunity(
            brand_fit=result.research.brand_fit,
            confidence=result.research.confidence,
            followers=result.profile.followers,
            post_index=post_index,
            estimated_comments=estimated_comments,
            brand=brand,
            post_preview=post_preview,
            research_text=research_text,
        )
        score = breakdown.total
        suggestions = self._commenter.generate_suggestions(
            brand=brand,
            result=result,
            post_preview=post_preview,
        )
        comments_preview = self._commenter.preview_thread(
            post_preview=post_preview,
            estimated_comments=estimated_comments,
        )
        opportunity_id = _opportunity_id(
            result.profile.profile_url, post_preview, post_index
        )
        post_url = result.profile.profile_url.rstrip("/") + "/"

        return CommentOpportunity(
            id=opportunity_id,
            creator_name=result.profile.name,
            creator_url=result.profile.profile_url,
            profile_picture_url=profile_picture_url(result.profile.name),
            brand_fit=result.research.brand_fit,
            opportunity_score=score,
            priority=priority_from_opportunity_score(score),
            post_preview=post_preview,
            post_url=post_url,
            post_index=post_index,
            why_now=build_why_now(
                brand_fit=result.research.brand_fit,
                post_preview=post_preview,
                estimated_comments=estimated_comments,
                breakdown=breakdown,
            ),
            score_breakdown=breakdown,
            score_explanation=explain_score(breakdown),
            latest_comments=comments_preview,
            comment_suggestions=suggestions[:3],
            estimated_existing_comments=estimated_comments,
            status="active",
        )


def _similarity_points(
    *,
    brand: BrandProfile,
    post_preview: str,
    research_text: str,
    confidence: int,
) -> float:
    corpus = f"{post_preview} {research_text}".lower()
    tokens: set[str] = set()
    for value in brand.values + brand.products + brand.target_audience:
        tokens.update(_tokens(value))
    tokens.update(_tokens(brand.description))
    if not tokens:
        return round((confidence / 10) * 15, 1)
    hits = sum(1 for token in tokens if token in corpus)
    overlap = min(hits / max(len(tokens), 1), 1.0)
    return round(overlap * 10 + (confidence / 10) * 5, 1)


def _tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]{4,}", text.lower())}


def _opportunity_id(creator_url: str, post_preview: str, post_index: int) -> str:
    raw = f"{creator_url}|{post_index}|{post_preview}".encode()
    return hashlib.sha1(raw).hexdigest()[:12]
