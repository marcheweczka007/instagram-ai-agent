"""Search channel adapters for multi-source creator discovery."""

from instagram_agent.services.search_channels.base import (
    ChannelSearchResult,
    SearchChannel,
)
from instagram_agent.services.search_channels.google_instagram import (
    GoogleInstagramSearchChannel,
)

__all__ = [
    "ChannelSearchResult",
    "GoogleInstagramSearchChannel",
    "SearchChannel",
]
