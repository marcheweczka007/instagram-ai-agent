"""Marketing session orchestration for the owner UI.

Keeps business logic out of Streamlit: the UI only configures and displays.
"""

from __future__ import annotations

import logging
import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from instagram_agent.agents.research import ResearchAgent
from instagram_agent.agents.scorer import ScorerAgent
from instagram_agent.browser.instagram_scraper import InstagramScraper
from instagram_agent.config import get_settings
from instagram_agent.domain.models import (
    BrandProfile,
    BrandResearchResult,
    CommentOpportunity,
    ResearchAnalysis,
)
from instagram_agent.fixtures import build_jollyzu_brand
from instagram_agent.logging_utils import (
    default_csv_path,
    default_json_path,
    default_report_path,
    setup_logging,
)
from instagram_agent.pipelines.analyse_profile import analyse_profile
from instagram_agent.services.csv_exporter import CsvExporter
from instagram_agent.services.discovery_orchestrator import DiscoveryOrchestrator
from instagram_agent.services.json_exporter import JsonExporter
from instagram_agent.services.notion_exporter import NotionExporter
from instagram_agent.services.opportunities import OpportunityService
from instagram_agent.services.report_generator import ReportGenerator, save_markdown

logger = logging.getLogger(__name__)

ProgressCallback = Callable[["SessionProgress"], None]

_SECONDS_PER_CREATOR = 120.0


@dataclass(frozen=True)
class SessionOptions:
    """Owner-selected workflow toggles for one marketing session."""

    brand_instagram_url: str
    discover: bool = True
    research: bool = True
    generate_comments: bool = True
    generate_outreach: bool = True
    export_notion: bool = True
    export_markdown: bool = True
    export_csv: bool = True
    duration_minutes: int = 30


@dataclass
class SessionProgress:
    """Live progress snapshot consumed by the Streamlit UI."""

    current_task: str = "Idle"
    analysed: int = 0
    total: int = 0
    estimated_remaining_seconds: float | None = None
    logs: list[str] = field(default_factory=list)
    notion_saved_names: list[str] = field(default_factory=list)
    results: list[BrandResearchResult] = field(default_factory=list)
    is_running: bool = False
    is_complete: bool = False
    error: str | None = None


@dataclass
class MarketingTask:
    """One actionable follow-up after a session finishes."""

    rank: int
    action: str
    creator_name: str
    detail: str
    estimated_minutes: float


@dataclass
class SessionOutcome:
    """Final artifacts from a completed marketing session."""

    brand: BrandProfile
    results: list[BrandResearchResult]
    progress: SessionProgress
    csv_path: Path | None = None
    report_path: Path | None = None
    json_path: Path | None = None
    notion_enabled: bool = False
    notion_url: str | None = None
    tasks: list[MarketingTask] = field(default_factory=list)
    tasks_estimated_minutes: float = 0.0
    opportunities: list[CommentOpportunity] = field(default_factory=list)


def priority_from_brand_fit(brand_fit: int) -> str:
    if brand_fit >= 9:
        return "High"
    if brand_fit >= 7:
        return "Medium"
    return "Low"


def build_ai_notes(research: ResearchAnalysis) -> str:
    sentences = [
        _as_sentence(research.value_alignment),
        _as_sentence(research.aesthetic_match),
        _as_sentence(research.audience_match),
        _as_sentence(research.collaboration_potential),
    ]
    notes = [sentence for sentence in sentences if sentence]
    if not notes and research.overall_summary.strip():
        notes = [_as_sentence(research.overall_summary)]
    return "\n".join(notes)


def extract_instagram_username(url: str) -> str:
    cleaned = (url or "").strip()
    if not cleaned:
        return ""
    if "://" not in cleaned:
        cleaned = "https://" + cleaned
    path = urlparse(cleaned).path.strip("/")
    if not path:
        return ""
    return path.split("/")[0].lstrip("@")


def resolve_brand_and_query(brand_instagram_url: str) -> tuple[BrandProfile, str]:
    """Map a brand Instagram URL to a BrandProfile + discovery query."""
    username = extract_instagram_username(brand_instagram_url).lower()
    if not username:
        raise ValueError("Brand Instagram URL is required.")

    if re.search(r"jollyzu|upcycle\.lab", username):
        return build_jollyzu_brand(), "upcycled bags"

    brand = BrandProfile(
        name=username,
        description=f"Brand Instagram account @{username} ({brand_instagram_url})",
        target_audience=[f"Audience overlapping with @{username}"],
        values=["Authenticity", "Brand collaboration"],
        products=[f"Products promoted by @{username}"],
        tone_of_voice="Authentic and brand-aligned",
    )
    query = f"{username.replace('.', ' ')} creators collaboration"
    return brand, query


def creator_cap_for_duration(duration_minutes: int) -> int:
    """Soft cap on creators analysed during discovery for a timed session."""
    minutes = max(5, min(60, int(duration_minutes)))
    return max(3, minutes // 3)


def build_marketing_tasks(results: list[BrandResearchResult]) -> list[MarketingTask]:
    """Build a short post-session action list for the owner."""
    ranked = sorted(results, key=lambda item: item.research.brand_fit, reverse=True)
    tasks: list[MarketingTask] = []
    if not ranked:
        return tasks

    top = ranked[0]
    tasks.append(
        MarketingTask(
            rank=1,
            action="Comment",
            creator_name=top.profile.name,
            detail=top.analysis.comment.strip() or "Leave a thoughtful comment",
            estimated_minutes=3.0,
        )
    )
    if len(ranked) >= 2:
        second = ranked[1]
        tasks.append(
            MarketingTask(
                rank=2,
                action="Send DM",
                creator_name=second.profile.name,
                detail=(
                    second.research.first_outreach_angle.strip()
                    or "Send a short collaboration DM"
                ),
                estimated_minutes=5.0,
            )
        )
    if len(ranked) >= 3:
        third = ranked[2]
        tasks.append(
            MarketingTask(
                rank=3,
                action="Research",
                creator_name=third.profile.name,
                detail="Review recent posts and refine outreach angle",
                estimated_minutes=7.0,
            )
        )
    return tasks


def session_stats(results: list[BrandResearchResult]) -> dict[str, float | int]:
    if not results:
        return {
            "creators_analysed": 0,
            "average_brand_fit": 0.0,
            "high_priority": 0,
            "new_creators": 0,
        }
    fits = [item.research.brand_fit for item in results]
    high = sum(1 for fit in fits if priority_from_brand_fit(fit) == "High")
    return {
        "creators_analysed": len(results),
        "average_brand_fit": round(sum(fits) / len(fits), 1),
        "high_priority": high,
        "new_creators": len(results),
    }


class MarketingSessionService:
    """Run a timed marketing workflow using existing agents and exporters."""

    def __init__(self) -> None:
        setup_logging()

    async def run(
        self,
        options: SessionOptions,
        on_progress: ProgressCallback | None = None,
    ) -> SessionOutcome:
        progress = SessionProgress(is_running=True)
        started = time.perf_counter()
        deadline = started + (options.duration_minutes * 60)

        def emit(task: str, **updates: object) -> None:
            progress.current_task = task
            for key, value in updates.items():
                setattr(progress, key, value)
            if on_progress is not None:
                on_progress(progress)

        def log(message: str) -> None:
            logger.info(message)
            progress.logs = [*progress.logs, message]
            if on_progress is not None:
                on_progress(progress)

        try:
            brand, query = resolve_brand_and_query(options.brand_instagram_url)
            settings = get_settings()
            notion_configured = settings.notion_enabled and bool(
                settings.notion_token and settings.notion_database_id
            )
            notion_url = (
                f"https://www.notion.so/{settings.notion_database_id.replace('-', '')}"
                if notion_configured
                else None
            )

            emit("Preparing session", total=0, analysed=0)
            log(f"Brand resolved: {brand.name}")
            log(f"Seed topic (planner input): {query}")
            log(f"Session budget: {options.duration_minutes} minutes")

            profile_urls: list[str] = []
            query_sources: dict[str, list[str]] = {}
            orchestrator: DiscoveryOrchestrator | None = None
            if options.discover:
                emit("Planning + discovering creators")
                log("Starting AI search planner + multi-query discovery…")
                orchestrator = DiscoveryOrchestrator()
                discovery = await orchestrator.discover_for_brand(
                    brand,
                    deadline=deadline,
                    on_progress=log,
                )
                profile_urls = list(discovery.profile_urls)
                query_sources = dict(discovery.query_sources)
                log(
                    f"Discovered {len(profile_urls)} profiles "
                    f"(ran {len(discovery.queries_run)} queries, "
                    f"skipped {len(discovery.queries_skipped)})"
                )
            else:
                log("Discovery skipped")

            cap = creator_cap_for_duration(options.duration_minutes)
            if profile_urls and len(profile_urls) > cap:
                log(
                    f"Limiting to {cap} creators for the {options.duration_minutes}m session"
                )
                profile_urls = profile_urls[:cap]

            emit(
                "Analysing creators" if profile_urls else "No creators to analyse",
                total=len(profile_urls),
                analysed=0,
                estimated_remaining_seconds=len(profile_urls) * _SECONDS_PER_CREATOR,
            )

            results: list[BrandResearchResult] = []
            notion_exporter: NotionExporter | None = None
            if options.export_notion and notion_configured:
                notion_exporter = NotionExporter(settings=settings)
                try:
                    notion_exporter.connect()
                except Exception as exc:  # noqa: BLE001
                    log(
                        f"Notion connect failed — will retry per creator / CSV fallback: {exc}"
                    )

            if profile_urls and (options.research or options.generate_comments):
                scraper = InstagramScraper()
                scorer = ScorerAgent()
                for index, url in enumerate(profile_urls, start=1):
                    if time.perf_counter() >= deadline:
                        log("Session time budget reached — stopping analysis")
                        break
                    emit(
                        f"Analysing {url}",
                        analysed=len(results),
                        total=len(profile_urls),
                        estimated_remaining_seconds=_estimate_remaining(
                            started, index - 1, len(profile_urls)
                        ),
                    )
                    try:
                        analysis = await analyse_profile(
                            url, scraper=scraper, scorer=scorer
                        )
                        log(f"Analysed {analysis.profile.name}")
                    except Exception as exc:  # noqa: BLE001
                        log(f"Failed analysing {url}: {exc}")
                        continue

                    if options.research or options.generate_outreach:
                        emit(f"Researching {analysis.profile.name}")
                        research = ResearchAgent().research(
                            brand=brand,
                            profile=analysis.profile,
                            analysis=analysis.analysis,
                        )
                    else:
                        research = _placeholder_research(analysis.analysis.score)

                    if not options.generate_comments:
                        analysis.analysis.comment = ""
                    if not options.generate_outreach:
                        research.first_outreach_angle = ""

                    result = BrandResearchResult(
                        profile=analysis.profile,
                        analysis=analysis.analysis,
                        research=research,
                    )
                    results.append(result)
                    progress.results = list(results)

                    if notion_exporter is not None:
                        emit(f"Saving {result.profile.name} to Notion")
                        try:
                            notion_exporter.upsert_creator(result)
                            progress.notion_saved_names = [
                                *progress.notion_saved_names,
                                result.profile.name,
                            ]
                            log(f"Saved to Notion: {result.profile.name}")
                        except Exception as exc:  # noqa: BLE001
                            log(
                                f"Notion export failed for {result.profile.name}: {exc}"
                            )

                    emit(
                        f"Completed {result.profile.name}",
                        analysed=len(results),
                        estimated_remaining_seconds=_estimate_remaining(
                            started, index, len(profile_urls)
                        ),
                    )
            elif profile_urls:
                # Discovery-only path: still surface URLs as lightweight stubs.
                log("Research/comments disabled — discovery results only")
            elif not options.discover:
                log("Nothing to run: enable Discover and/or Research")

            results = sorted(
                results,
                key=lambda item: item.research.brand_fit,
                reverse=True,
            )
            progress.results = list(results)

            stem = brand.name.lower().replace(" ", "_")
            csv_path: Path | None = None
            report_path: Path | None = None
            json_path: Path | None = None

            if results and options.export_csv:
                emit("Exporting CSV")
                csv_path = default_csv_path(f"{stem}_research")
                CsvExporter().export(results, str(csv_path))
                log(f"CSV exported → {csv_path}")

            if results and options.export_markdown:
                emit("Exporting Markdown report")
                report_path = default_report_path(f"{stem}_report")
                report = ReportGenerator().generate(brand, results)
                save_markdown(report, str(report_path))
                json_path = default_json_path(f"{stem}_summary")
                JsonExporter().export(brand, results, str(json_path))
                log(f"Markdown report exported → {report_path}")

            tasks = build_marketing_tasks(results)
            emit("Building today's comment opportunities")
            opportunities = OpportunityService().build_from_results(brand, results)
            log(f"Ranked {len(opportunities)} comment opportunities")

            if orchestrator is not None and query_sources:
                orchestrator.history.record_outcomes(
                    query_sources=query_sources,
                    results=results,
                    opportunities=opportunities,
                )
                log("Updated search strategy weights from outcomes")

            outcome = SessionOutcome(
                brand=brand,
                results=results,
                progress=progress,
                csv_path=csv_path,
                report_path=report_path,
                json_path=json_path,
                notion_enabled=notion_configured and options.export_notion,
                notion_url=notion_url,
                tasks=tasks,
                tasks_estimated_minutes=sum(task.estimated_minutes for task in tasks),
                opportunities=opportunities,
            )
            progress.is_running = False
            progress.is_complete = True
            progress.current_task = "Session complete"
            progress.estimated_remaining_seconds = 0
            emit(
                "Session complete",
                analysed=len(results),
                total=max(progress.total, len(results)),
            )
            log(f"Session finished with {len(results)} creators")
            return outcome
        except Exception as exc:
            progress.is_running = False
            progress.is_complete = True
            progress.error = f"{type(exc).__name__}: {exc}"
            progress.current_task = "Session failed"
            log(progress.error)
            if on_progress is not None:
                on_progress(progress)
            raise


def _estimate_remaining(started: float, completed: int, total: int) -> float:
    remaining_count = max(total - completed, 0)
    if completed <= 0:
        return remaining_count * _SECONDS_PER_CREATOR
    elapsed = max(time.perf_counter() - started, 1.0)
    avg = elapsed / completed
    return remaining_count * avg


def _as_sentence(text: str) -> str:
    cleaned = " ".join(text.split()).strip()
    if not cleaned:
        return ""
    if cleaned[-1] not in ".!?":
        cleaned += "."
    return cleaned[0].upper() + cleaned[1:]


def _placeholder_research(score: int) -> ResearchAnalysis:
    fit = max(1, min(10, score))
    return ResearchAnalysis(
        brand_fit=fit,
        confidence=5,
        audience_match="Not researched in this session",
        aesthetic_match="Not researched in this session",
        value_alignment="Not researched in this session",
        collaboration_potential="Not researched in this session",
        overall_summary="Research step was disabled for this session.",
        strengths=[],
        weaknesses=[],
        collaboration_ideas=[],
        first_outreach_angle="",
    )
