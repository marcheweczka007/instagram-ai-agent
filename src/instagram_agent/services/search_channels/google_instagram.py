"""Google site:instagram.com search channel (Browser Use)."""

from __future__ import annotations

import logging

from instagram_agent.agents.discovery import DiscoveryAgent
from instagram_agent.services.search_channels.base import (
    ChannelSearchResult,
    SearchChannel,
)

logger = logging.getLogger(__name__)


class GoogleInstagramSearchChannel(SearchChannel):
    """Run one Google discovery query via the existing DiscoveryAgent."""

    name = "google_instagram"

    def __init__(self, discovery: DiscoveryAgent | None = None) -> None:
        self._discovery = discovery or DiscoveryAgent()

    async def search(self, query: str) -> ChannelSearchResult:
        logger.info("Google Instagram channel searching %r", query)
        result = await self._discovery.discover(query)
        return ChannelSearchResult(
            channel=self.name,
            query=query,
            profile_urls=list(result.profile_urls),
        )
