"""Abstract CRM exporter interface for Notion / HubSpot / Airtable / Sheets."""

from __future__ import annotations

from abc import ABC, abstractmethod

from instagram_agent.domain.models import BrandResearchResult


class CrmExporter(ABC):
    """Common interface for creator CRM destinations.

    Pipelines depend on this abstraction so future HubSpot / Airtable /
    Google Sheets CRM adapters can plug in without pipeline changes.
    """

    @abstractmethod
    def connect(self) -> None:
        """Authenticate and validate the destination is reachable."""

    @abstractmethod
    def upsert_creator(self, result: BrandResearchResult) -> None:
        """Create or update one creator immediately after analysis."""
