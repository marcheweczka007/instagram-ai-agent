"""Abstract search channel contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ChannelSearchResult:
    """URLs returned by one search channel for one query."""

    channel: str
    query: str
    profile_urls: list[str] = field(default_factory=list)


class SearchChannel(ABC):
    """Future-proof search backend (Google, Instagram, TikTok, …)."""

    name: str

    @abstractmethod
    async def search(self, query: str) -> ChannelSearchResult:
        """Execute ``query`` on this channel and return profile URLs."""
