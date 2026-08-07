"""Plan an optimal marketing session within a time budget.

Selects a subset of opportunities that maximises total Opportunity Score
without exceeding the user's available minutes (0/1 knapsack).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from instagram_agent.domain.models import CommentOpportunity, MarketingImpact


@dataclass(frozen=True)
class PlannedMarketingSession:
    """AI-planned subset of opportunities for today's available time."""

    available_minutes: int
    planned_minutes: int
    buffer_minutes: int
    opportunities: list[CommentOpportunity]
    total_opportunity_score: float
    average_opportunity_score: float
    estimated_marketing_impact: MarketingImpact
    impact_stars: str
    rationale: str
    deferred_count: int


def plan_marketing_session(
    opportunities: list[CommentOpportunity],
    *,
    available_minutes: int,
) -> PlannedMarketingSession:
    """Choose opportunities that maximise total score within ``available_minutes``."""
    budget = max(5, min(60, int(available_minutes)))
    # Only plan unfinished work.
    candidates = [item for item in opportunities if item.status == "active"]
    selected = _maximise_score_within_budget(candidates, budget_minutes=budget)

    planned_seconds = sum(item.estimated_time_seconds for item in selected)
    planned_minutes = _seconds_to_minutes(planned_seconds) if selected else 0
    buffer = max(0, budget - planned_minutes)
    total_score = round(sum(item.opportunity_score for item in selected), 1)
    average = round(total_score / len(selected), 1) if selected else 0.0
    impact = _session_impact(selected)
    stars = impact_to_stars(impact)
    deferred = max(0, len(candidates) - len(selected))
    rationale = _build_rationale(
        selected=selected,
        available_minutes=budget,
        planned_minutes=planned_minutes,
        buffer_minutes=buffer,
        total_score=total_score,
        deferred=deferred,
    )
    return PlannedMarketingSession(
        available_minutes=budget,
        planned_minutes=planned_minutes,
        buffer_minutes=buffer,
        opportunities=selected,
        total_opportunity_score=total_score,
        average_opportunity_score=average,
        estimated_marketing_impact=impact,
        impact_stars=stars,
        rationale=rationale,
        deferred_count=deferred,
    )


def impact_to_stars(impact: MarketingImpact) -> str:
    mapping = {
        "Low": "★☆☆☆☆",
        "Medium": "★★★☆☆",
        "High": "★★★★☆",
        "Very High": "★★★★★",
    }
    return mapping.get(impact, "★★★☆☆")


def _maximise_score_within_budget(
    candidates: list[CommentOpportunity],
    *,
    budget_minutes: int,
) -> list[CommentOpportunity]:
    """0/1 knapsack: maximise sum(opportunity_score) under minute capacity."""
    if not candidates or budget_minutes <= 0:
        return []

    # Work in whole minutes so the plan matches UI time labels.
    weights = [_opportunity_minutes(item) for item in candidates]
    values = [item.opportunity_score for item in candidates]
    n = len(candidates)
    capacity = budget_minutes

    # dp[i][w] = best score using first i items with capacity w
    dp = [[0.0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        weight = weights[i - 1]
        value = values[i - 1]
        for w in range(capacity + 1):
            best = dp[i - 1][w]
            if weight <= w:
                best = max(best, dp[i - 1][w - weight] + value)
            dp[i][w] = best

    # Reconstruct chosen set.
    chosen_idx: list[int] = []
    w = capacity
    for i in range(n, 0, -1):
        if dp[i][w] == dp[i - 1][w]:
            continue
        chosen_idx.append(i - 1)
        w -= weights[i - 1]
        if w < 0:
            break

    chosen_idx.reverse()
    # Keep original score order among selected (highest impact first).
    selected = [candidates[i] for i in chosen_idx]
    selected.sort(key=lambda item: item.opportunity_score, reverse=True)
    return selected


def _opportunity_minutes(item: CommentOpportunity) -> int:
    return max(1, _seconds_to_minutes(item.estimated_time_seconds))


def _seconds_to_minutes(total_seconds: int) -> int:
    return max(1, math.ceil(total_seconds / 60)) if total_seconds > 0 else 0


def _session_impact(items: list[CommentOpportunity]) -> MarketingImpact:
    if not items:
        return "Low"
    # Prefer breakdown-based labels already on each opportunity.
    rank = {"Low": 0, "Medium": 1, "High": 2, "Very High": 3}
    average = sum(rank.get(item.marketing_impact, 1) for item in items) / len(items)
    if average >= 2.5:
        return "Very High"
    if average >= 1.5:
        return "High"
    if average >= 0.75:
        return "Medium"
    return "Low"


def _build_rationale(
    *,
    selected: list[CommentOpportunity],
    available_minutes: int,
    planned_minutes: int,
    buffer_minutes: int,
    total_score: float,
    deferred: int,
) -> str:
    if not selected:
        return (
            f"No active opportunities fit a {available_minutes}-minute session yet. "
            "Run Discovery to build today's queue, then come back to plan."
        )

    top = selected[0]
    density = total_score / max(planned_minutes, 1)
    parts = [
        (
            f"I planned a {planned_minutes}-minute session inside your "
            f"{available_minutes}-minute window "
            f"({buffer_minutes} min buffer), maximising total Opportunity Score "
            f"({total_score:.0f}) rather than taking the first cards in order."
        ),
        (
            f"Selected {len(selected)} actions with the best score-per-minute mix "
            f"(~{density:.1f} points/min). "
            f"Lead action: {top.creator_name} "
            f"(score {top.opportunity_score:.0f}, {top.estimated_time_label}, "
            f"impact {top.marketing_impact})."
        ),
    ]
    if deferred:
        parts.append(
            f"Deferred {deferred} lower-efficiency opportunities so you finish "
            "what matters most today — open them later if you gain extra time."
        )
    else:
        parts.append(
            "Every active opportunity fits today's budget — nice compact queue."
        )
    return " ".join(parts)
