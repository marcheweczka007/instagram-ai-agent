"""Generate ranked comment opportunities after brand research."""

from __future__ import annotations

import hashlib
import logging
import math
import re
from dataclasses import dataclass
from urllib.parse import quote

from instagram_agent.agents.commenter import CommenterAgent
from instagram_agent.domain.models import (
    BrandProfile,
    BrandResearchResult,
    CommentOpportunity,
    MarketingImpact,
    OpportunityPriority,
    OpportunityScoreBreakdown,
    OpportunityTimeBreakdown,
)

logger = logging.getLogger(__name__)

HIGH_PRIORITY_THRESHOLD = 70.0
MEDIUM_PRIORITY_THRESHOLD = 50.0

# Baseline action times (seconds) for one comment opportunity.
_BASE_TIME = OpportunityTimeBreakdown()


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


def estimate_time_breakdown(estimated_comments: int) -> OpportunityTimeBreakdown:
    """Estimate user effort from the actions required to complete one comment."""
    # Busier threads take longer to skim.
    extra_read = 0
    if estimated_comments > 25:
        extra_read = 20
    elif estimated_comments > 8:
        extra_read = 10
    return OpportunityTimeBreakdown(
        read_post=_BASE_TIME.read_post,
        read_comments=_BASE_TIME.read_comments + extra_read,
        choose_suggestion=_BASE_TIME.choose_suggestion,
        copy_comment=_BASE_TIME.copy_comment,
        open_instagram=_BASE_TIME.open_instagram,
        paste_and_publish=_BASE_TIME.paste_and_publish,
    )


def format_estimated_time(total_seconds: int) -> str:
    minutes = max(1, math.ceil(total_seconds / 60))
    return f"~{minutes} min"


def marketing_impact_from_breakdown(
    breakdown: OpportunityScoreBreakdown,
) -> MarketingImpact:
    """Map score components to a habit-friendly impact label."""
    points = (
        (breakdown.brand_fit / 35) * 25
        + (breakdown.post_freshness / 20) * 25
        + (breakdown.comment_room / 15) * 20
        + (breakdown.brand_similarity / 15) * 15
        + (breakdown.visibility_potential / 15) * 15
    )
    if points >= 80:
        return "Very High"
    if points >= 65:
        return "High"
    if points >= 45:
        return "Medium"
    return "Low"


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


@dataclass(frozen=True)
class OpportunitiesSessionSummary:
    """Top-of-page session snapshot for Today's Opportunities."""

    high_priority_count: int
    active_count: int
    completed_count: int
    skipped_count: int
    estimated_total_seconds: int
    estimated_total_label: str
    average_opportunity_score: float
    estimated_marketing_impact: MarketingImpact
    today_summary: str
    is_session_complete: bool
    completed_seconds: int
    completed_time_label: str


def build_session_summary(
    opportunities: list[CommentOpportunity],
) -> OpportunitiesSessionSummary:
    active = [item for item in opportunities if item.status == "active"]
    high = [
        item for item in active if item.opportunity_score >= HIGH_PRIORITY_THRESHOLD
    ]
    done = [item for item in opportunities if item.status == "done"]
    skipped = [item for item in opportunities if item.status == "skipped"]

    # Habit focus: estimate remaining work on what is still actionable.
    focus = high or active
    total_seconds = sum(item.estimated_time_seconds for item in focus)
    completed_seconds = sum(item.estimated_time_seconds for item in done)

    scored = focus or opportunities
    average = (
        round(sum(item.opportunity_score for item in scored) / len(scored), 1)
        if scored
        else 0.0
    )
    impact = _session_impact(focus or done)
    summary = build_today_summary(
        opportunities=opportunities,
        focus=focus,
        total_seconds=total_seconds,
        impact=impact,
    )
    is_complete = bool(opportunities) and not active

    return OpportunitiesSessionSummary(
        high_priority_count=len(high),
        active_count=len(active),
        completed_count=len(done),
        skipped_count=len(skipped),
        estimated_total_seconds=total_seconds,
        estimated_total_label=(
            format_estimated_time(total_seconds) if total_seconds else "~0 min"
        ),
        average_opportunity_score=average,
        estimated_marketing_impact=impact,
        today_summary=summary,
        is_session_complete=is_complete,
        completed_seconds=completed_seconds,
        completed_time_label=(
            format_estimated_time(completed_seconds) if completed_seconds else "~0 min"
        ),
    )


def build_today_summary(
    *,
    opportunities: list[CommentOpportunity],
    focus: list[CommentOpportunity],
    total_seconds: int,
    impact: MarketingImpact,
) -> str:
    """Short coaching summary that encourages finishing today's session."""
    if not opportunities:
        return (
            "No opportunities yet today. Run Discovery to build a fresh "
            "high-impact comment list — consistency beats intensity."
        )
    if not focus:
        return (
            "You've cleared today's active list. Come back tomorrow for a "
            "fresh set of opportunities and keep the streak going."
        )

    fresh = sum(1 for item in focus if item.score_breakdown.post_freshness >= 18)
    open_threads = sum(1 for item in focus if item.score_breakdown.comment_room >= 11)
    strength = (
        "particularly strong"
        if impact in {"High", "Very High"}
        else "solid"
        if impact == "Medium"
        else "a useful warm-up"
    )
    freshness_line = (
        f"Most recommended creators posted recently and currently have low "
        f"comment competition ({open_threads}/{len(focus)} open threads)."
        if fresh or open_threads
        else "Prioritise the top cards — they offer the best effort-to-impact ratio."
    )
    minutes = format_estimated_time(total_seconds).lstrip("~")
    return (
        f"Today's opportunities are {strength}. {freshness_line} "
        f"Estimated session: {minutes}. "
        f"Expected impact: {impact}."
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
        time_breakdown = estimate_time_breakdown(estimated_comments)
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
            marketing_impact=marketing_impact_from_breakdown(breakdown),
            estimated_time_seconds=time_breakdown.total_seconds,
            estimated_time_label=format_estimated_time(time_breakdown.total_seconds),
            time_breakdown=time_breakdown,
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


def _session_impact(items: list[CommentOpportunity]) -> MarketingImpact:
    if not items:
        return "Low"
    rank = {"Low": 0, "Medium": 1, "High": 2, "Very High": 3}
    average = sum(rank[item.marketing_impact] for item in items) / len(items)
    if average >= 2.5:
        return "Very High"
    if average >= 1.5:
        return "High"
    if average >= 0.75:
        return "Medium"
    return "Low"


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
