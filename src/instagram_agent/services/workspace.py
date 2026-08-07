"""Workspace helpers for the Streamlit marketing dashboard.

Pure presentation support — no pipeline rewrites. Reuses marketing_session helpers.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from instagram_agent.config import Settings, get_settings
from instagram_agent.domain.models import (
    BrandProfile,
    BrandResearchResult,
    InstagramProfile,
    ProfileAnalysis,
    ResearchAnalysis,
)
from instagram_agent.services.marketing_session import (
    MarketingTask,
    build_marketing_tasks,
    priority_from_brand_fit,
    session_stats,
)

OWNER_NAME = "Zuza"
DEFAULT_WEEKLY_GOAL = 20


@dataclass(frozen=True)
class DashboardSnapshot:
    """Aggregated numbers for the Dashboard page."""

    greeting: str
    creators_analysed: int
    high_priority: int
    comments_ready: int
    dms_ready: int
    weekly_goal: int
    weekly_progress: int
    estimated_work_minutes: float
    tasks: list[MarketingTask]


def greeting_for_now(
    *,
    name: str = OWNER_NAME,
    now: datetime | None = None,
) -> str:
    current = now or datetime.now(ZoneInfo("Europe/London"))
    hour = current.hour
    if hour < 12:
        period = "Good morning"
    elif hour < 18:
        period = "Good afternoon"
    else:
        period = "Good evening"
    return f"{period} {name} 👋"


def workspace_stats(
    results: list[BrandResearchResult],
    *,
    weekly_goal: int = DEFAULT_WEEKLY_GOAL,
) -> dict[str, float | int]:
    base = session_stats(results)
    comments_ready = sum(1 for item in results if item.analysis.comment.strip())
    dms_ready = sum(1 for item in results if item.research.first_outreach_angle.strip())
    tasks = build_marketing_tasks(results)
    return {
        **base,
        "comments_ready": comments_ready,
        "dms_ready": dms_ready,
        "weekly_goal": weekly_goal,
        "weekly_progress": min(len(results), weekly_goal),
        "estimated_work_minutes": sum(task.estimated_minutes for task in tasks),
    }


def build_dashboard_snapshot(
    results: list[BrandResearchResult],
    *,
    weekly_goal: int = DEFAULT_WEEKLY_GOAL,
) -> DashboardSnapshot:
    stats = workspace_stats(results, weekly_goal=weekly_goal)
    tasks = build_marketing_tasks(results)
    return DashboardSnapshot(
        greeting=greeting_for_now(),
        creators_analysed=int(stats["creators_analysed"]),
        high_priority=int(stats["high_priority"]),
        comments_ready=int(stats["comments_ready"]),
        dms_ready=int(stats["dms_ready"]),
        weekly_goal=int(stats["weekly_goal"]),
        weekly_progress=int(stats["weekly_progress"]),
        estimated_work_minutes=float(stats["estimated_work_minutes"]),
        tasks=tasks,
    )


def load_latest_results(reports_dir: Path | None = None) -> list[BrandResearchResult]:
    """Load the newest ``*_summary.json`` export if present."""
    settings = get_settings()
    directory = Path(reports_dir or settings.reports_dir)
    if not directory.exists():
        return []

    summaries = sorted(
        directory.glob("*_summary.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not summaries:
        return []

    payload = json.loads(summaries[0].read_text(encoding="utf-8"))
    results: list[BrandResearchResult] = []
    for row in payload.get("results", []):
        results.append(
            BrandResearchResult(
                profile=InstagramProfile(**row["profile"]),
                analysis=ProfileAnalysis(**row["analysis"]),
                research=ResearchAnalysis(**row["research"]),
            )
        )
    return results


def load_latest_brand(reports_dir: Path | None = None) -> BrandProfile | None:
    settings = get_settings()
    directory = Path(reports_dir or settings.reports_dir)
    if not directory.exists():
        return None
    summaries = sorted(
        directory.glob("*_summary.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not summaries:
        return None
    payload = json.loads(summaries[0].read_text(encoding="utf-8"))
    brand_data = payload.get("brand")
    if not brand_data:
        return None
    return BrandProfile(**brand_data)


def find_latest_artifact(stem_suffix: str, directory: Path) -> Path | None:
    if not directory.exists():
        return None
    matches = sorted(
        directory.glob(f"*{stem_suffix}"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return matches[0] if matches else None


def notion_database_url(settings: Settings | None = None) -> str | None:
    cfg = settings or get_settings()
    if not (cfg.notion_enabled and cfg.notion_database_id):
        return None
    return f"https://www.notion.so/{cfg.notion_database_id.replace('-', '')}"


def dm_subject(result: BrandResearchResult) -> str:
    """Short subject line derived from collaboration potential / brand fit."""
    priority = priority_from_brand_fit(result.research.brand_fit)
    return f"{priority} priority collab — {result.profile.name}"
