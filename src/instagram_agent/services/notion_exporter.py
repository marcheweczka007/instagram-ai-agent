"""Notion CRM exporter for creator brand-research results."""

from __future__ import annotations

import csv
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from notion_client import Client
from notion_client.errors import APIResponseError

from instagram_agent.config import Settings, get_settings
from instagram_agent.domain.models import BrandResearchResult, ResearchAnalysis
from instagram_agent.logging_utils import default_csv_path
from instagram_agent.services.crm_exporter import CrmExporter

logger = logging.getLogger(__name__)

# Expected Notion database schema: property name → Notion type.
REQUIRED_PROPERTIES: dict[str, str] = {
    "Creator": "title",
    "Instagram URL": "url",
    "Followers": "number",
    "Score": "number",
    "Brand Fit": "number",
    "Confidence": "number",
    "Priority": "select",
    "Status": "status",
    "Suggested Comment": "rich_text",
    "Suggested DM": "rich_text",
    "First Outreach Angle": "rich_text",
    "Collaboration Ideas": "rich_text",
    "Strengths": "rich_text",
    "Weaknesses": "rich_text",
    "AI Notes": "rich_text",
    "Last Analysed": "date",
}

_CSV_HEADERS: tuple[str, ...] = (
    "Creator",
    "Instagram URL",
    "Followers",
    "Score",
    "Brand Fit",
    "Confidence",
    "Priority",
    "Status",
    "Suggested Comment",
    "Suggested DM",
    "First Outreach Angle",
    "Collaboration Ideas",
    "Strengths",
    "Weaknesses",
    "AI Notes",
    "Last Analysed",
)


class NotionExporter(CrmExporter):
    """Upsert creator research into a Notion database (CSV fallback on failure)."""

    def __init__(
        self,
        *,
        token: str | None = None,
        database_id: str | None = None,
        settings: Settings | None = None,
        fallback_csv_path: str | Path | None = None,
    ) -> None:
        cfg = settings or get_settings()
        self._token = (token or cfg.notion_token).strip()
        self._database_id = (database_id or cfg.notion_database_id).strip()
        self._client: Client | None = None
        self._data_source_id: str | None = None
        self._fallback_csv_path = Path(
            fallback_csv_path or default_csv_path("notion_fallback")
        )

    def connect(self) -> None:
        """Create the Notion client and validate database schema."""
        if not self._token:
            raise ValueError("NOTION_TOKEN is not configured. Set it in .env.")
        if not self._database_id:
            raise ValueError("NOTION_DATABASE_ID is not configured. Set it in .env.")

        self._client = Client(auth=self._token)
        self._data_source_id = self._resolve_data_source_id()
        self._validate_schema()
        logger.info(
            "Connected to Notion database %s (data_source=%s)",
            self._database_id,
            self._data_source_id,
        )

    def upsert_creator(self, result: BrandResearchResult) -> None:
        """Create or update a creator page keyed by Instagram URL."""
        try:
            if self._client is None:
                self.connect()

            existing_id = self.creator_exists(result.profile.profile_url)
            if existing_id:
                self.update_creator(existing_id, result)
            else:
                self.create_creator(result)
        except Exception:
            logger.warning(
                "Notion upsert failed for %s; falling back to CSV",
                result.profile.name,
                exc_info=True,
            )
            self._append_csv_fallback(result)

    def creator_exists(self, instagram_url: str) -> str | None:
        """Return Notion page ID if a creator with this Instagram URL exists."""
        client = self._require_client()
        data_source_id = self._require_data_source_id()
        response = client.data_sources.query(
            data_source_id=data_source_id,
            filter={
                "property": "Instagram URL",
                "url": {"equals": instagram_url},
            },
            page_size=1,
        )
        results = response.get("results", [])
        if not results:
            return None
        return results[0]["id"]

    def create_creator(self, result: BrandResearchResult) -> None:
        """Create a new Notion page with Status=New."""
        client = self._require_client()
        data_source_id = self._require_data_source_id()
        properties = self._build_properties(result, include_status=True)
        client.pages.create(
            parent={"type": "data_source_id", "data_source_id": data_source_id},
            properties=properties,
        )
        logger.info("Created Notion creator %s", result.profile.name)

    def update_creator(self, page_id: str, result: BrandResearchResult) -> None:
        """Update an existing Notion page without changing Status."""
        client = self._require_client()
        properties = self._build_properties(result, include_status=False)
        client.pages.update(page_id=page_id, properties=properties)
        logger.info("Updated Notion creator %s", result.profile.name)

    def _resolve_data_source_id(self) -> str:
        client = self._require_client()
        try:
            database = client.databases.retrieve(database_id=self._database_id)
        except APIResponseError as exc:
            raise RuntimeError(
                f"Unable to access Notion database {self._database_id}: {exc}"
            ) from exc

        data_sources = database.get("data_sources") or []
        if not data_sources:
            raise RuntimeError(
                f"Notion database {self._database_id} has no data sources. "
                "Open the database in Notion and confirm the integration is connected."
            )
        return data_sources[0]["id"]

    def _validate_schema(self) -> None:
        client = self._require_client()
        data_source_id = self._require_data_source_id()
        try:
            data_source = client.data_sources.retrieve(data_source_id=data_source_id)
        except APIResponseError as exc:
            raise RuntimeError(
                f"Unable to access Notion data source {data_source_id}: {exc}"
            ) from exc

        properties = data_source.get("properties", {})
        missing: list[str] = []
        wrong_type: list[str] = []

        for name, expected_type in REQUIRED_PROPERTIES.items():
            if name not in properties:
                missing.append(name)
                continue
            actual_type = properties[name].get("type")
            if actual_type != expected_type:
                wrong_type.append(
                    f"{name} (expected {expected_type}, got {actual_type})"
                )

        if missing or wrong_type:
            parts: list[str] = []
            if missing:
                parts.append("Missing properties: " + ", ".join(sorted(missing)))
            if wrong_type:
                parts.append("Wrong property types: " + ", ".join(sorted(wrong_type)))
            raise RuntimeError(
                "Notion database schema is incomplete. " + " ".join(parts)
            )

    def _build_properties(
        self,
        result: BrandResearchResult,
        *,
        include_status: bool,
    ) -> dict[str, Any]:
        research = result.research
        priority = self._priority_from_brand_fit(research.brand_fit)
        properties: dict[str, Any] = {
            "Creator": self._title(result.profile.name),
            "Instagram URL": {"url": result.profile.profile_url},
            "Followers": {"number": result.profile.followers},
            "Score": {"number": result.analysis.score},
            "Brand Fit": {"number": research.brand_fit},
            "Confidence": {"number": research.confidence},
            "Priority": {"select": {"name": priority}},
            "Suggested Comment": self._rich_text(result.analysis.comment),
            "Suggested DM": self._rich_text(research.first_outreach_angle),
            "First Outreach Angle": self._rich_text(research.first_outreach_angle),
            "Collaboration Ideas": self._rich_text(
                self._join_lines(research.collaboration_ideas)
            ),
            "Strengths": self._rich_text(self._join_lines(research.strengths)),
            "Weaknesses": self._rich_text(self._join_lines(research.weaknesses)),
            "AI Notes": self._rich_text(self._build_ai_notes(research)),
            "Last Analysed": {"date": {"start": datetime.now(UTC).date().isoformat()}},
        }
        if include_status:
            properties["Status"] = {"status": {"name": "New"}}
        return properties

    def _append_csv_fallback(self, result: BrandResearchResult) -> None:
        path = self._fallback_csv_path
        path.parent.mkdir(parents=True, exist_ok=True)
        write_header = not path.exists() or path.stat().st_size == 0
        research = result.research
        row = [
            result.profile.name,
            result.profile.profile_url,
            result.profile.followers,
            result.analysis.score,
            research.brand_fit,
            research.confidence,
            self._priority_from_brand_fit(research.brand_fit),
            "New",
            result.analysis.comment,
            research.first_outreach_angle,
            research.first_outreach_angle,
            self._join_lines(research.collaboration_ideas),
            self._join_lines(research.strengths),
            self._join_lines(research.weaknesses),
            self._build_ai_notes(research),
            datetime.now(UTC).date().isoformat(),
        ]
        with path.open("a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if write_header:
                writer.writerow(_CSV_HEADERS)
            writer.writerow(row)
        logger.info("Appended Notion fallback CSV row → %s", path)

    @staticmethod
    def _priority_from_brand_fit(brand_fit: int) -> str:
        if brand_fit >= 9:
            return "High"
        if brand_fit >= 7:
            return "Medium"
        return "Low"

    @staticmethod
    def _build_ai_notes(research: ResearchAnalysis) -> str:
        sentences = [
            NotionExporter._as_sentence(research.value_alignment),
            NotionExporter._as_sentence(research.aesthetic_match),
            NotionExporter._as_sentence(research.audience_match),
            NotionExporter._as_sentence(research.collaboration_potential),
        ]
        notes = [sentence for sentence in sentences if sentence]
        if not notes and research.overall_summary.strip():
            notes = [NotionExporter._as_sentence(research.overall_summary)]
        return "\n".join(notes)

    @staticmethod
    def _as_sentence(text: str) -> str:
        cleaned = " ".join(text.split()).strip()
        if not cleaned:
            return ""
        if cleaned[-1] not in ".!?":
            cleaned += "."
        return cleaned[0].upper() + cleaned[1:]

    @staticmethod
    def _join_lines(items: list[str]) -> str:
        return "\n".join(f"- {item}" for item in items if item.strip())

    @staticmethod
    def _title(content: str) -> dict[str, Any]:
        return {"title": [{"type": "text", "text": {"content": content[:2000]}}]}

    @staticmethod
    def _rich_text(content: str) -> dict[str, Any]:
        return {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": (content or "")[:2000]},
                }
            ]
        }

    def _require_client(self) -> Client:
        if self._client is None:
            raise RuntimeError("Notion is not connected. Call connect() first.")
        return self._client

    def _require_data_source_id(self) -> str:
        if not self._data_source_id:
            raise RuntimeError(
                "Notion data source is not resolved. Call connect() first."
            )
        return self._data_source_id
