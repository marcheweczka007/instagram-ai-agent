"""Discover Instagram profile URLs for a search topic via Google."""

from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, urlparse

from browser_use import Agent, ChatOpenAI
from browser_use.agent.views import AgentHistoryList
from pydantic import ValidationError

from instagram_agent.domain.models import DiscoveryResult

logger = logging.getLogger(__name__)

_PROFILE_PATH_RE = re.compile(r"^/([A-Za-z0-9._]+)/?$")
_NON_PROFILE_SEGMENTS = frozenset(
    {
        "p",
        "reel",
        "reels",
        "tv",
        "stories",
        "explore",
        "tags",
        "accounts",
        "direct",
        "share",
        "about",
        "developer",
        "legal",
        "privacy",
        "nametag",
    }
)
_SPEED_PROMPT = """
Be concise. Stay on the Google results page.
Extract Instagram profile links only, then finish.
Do not open Instagram profiles.
""".strip()


class DiscoveryAgent:
    """Find Instagram profile URLs relevant to a search query."""

    def __init__(
        self,
        model: str = "gpt-5",
        extraction_model: str = "gpt-5-mini",
        max_steps: int = 8,
        timeout_seconds: float = 90,
        max_results: int = 20,
    ) -> None:
        prompt_path = Path(__file__).parent.parent / "prompts" / "discovery.md"
        self._system_prompt = prompt_path.read_text(encoding="utf-8")
        self._llm = ChatOpenAI(
            model=model,
            temperature=0.0,
            reasoning_effort="minimal",
            max_retries=1,
            max_completion_tokens=2048,
            timeout=40,
        )
        self._extraction_llm = ChatOpenAI(
            model=extraction_model,
            temperature=0.0,
            reasoning_effort="minimal",
            max_retries=1,
            max_completion_tokens=1024,
            timeout=30,
        )
        self._max_steps = max_steps
        self._timeout_seconds = timeout_seconds
        self._max_results = max_results

    async def discover(self, query: str) -> DiscoveryResult:
        """Discover Instagram profile URLs for ``query``."""
        cleaned_query = self._normalize_query(query)
        search_url = self._build_google_search_url(cleaned_query)
        logger.info("Discovery started for query=%r", cleaned_query)

        task = self._build_task(cleaned_query, search_url)
        history = await self._run_agent(task, search_url)
        raw = self._extract_structured_output(history)
        profile_urls = self._normalize_urls(raw.profile_urls)

        result = DiscoveryResult(profile_urls=profile_urls)
        logger.info(
            "Discovery finished for query=%r (%s URLs)",
            cleaned_query,
            len(result.profile_urls),
        )
        return result

    def _build_task(self, query: str, search_url: str) -> str:
        return f"""
{self._system_prompt}

Search query: {query}
Google search URL (already opening): {search_url}
Google query string: site:instagram.com {query}

Extract Instagram profile URLs from the first results page into DiscoveryResult.
""".strip()

    async def _run_agent(
        self,
        task: str,
        search_url: str,
    ) -> AgentHistoryList[Any]:
        agent = Agent(
            task=task,
            llm=self._llm,
            page_extraction_llm=self._extraction_llm,
            output_model_schema=DiscoveryResult,
            initial_actions=[
                {"navigate": {"url": search_url, "new_tab": False}},
                {"wait": {"seconds": 2}},
            ],
            flash_mode=True,
            use_thinking=False,
            use_judge=False,
            enable_planning=False,
            use_vision=False,
            max_failures=1,
            max_actions_per_step=3,
            final_response_after_failure=True,
            directly_open_url=False,
            llm_timeout=40,
            step_timeout=50,
            extend_system_message=_SPEED_PROMPT,
        )

        logger.info(
            "Browser Use discovery starting (max_steps=%s, timeout=%ss)",
            self._max_steps,
            self._timeout_seconds,
        )
        try:
            return await asyncio.wait_for(
                agent.run(max_steps=self._max_steps),
                timeout=self._timeout_seconds,
            )
        except TimeoutError as exc:
            raise RuntimeError("Instagram discovery timed out.") from exc
        except Exception as exc:
            logger.exception("Browser Use discovery failed")
            raise RuntimeError(
                f"Browser Use failed while discovering Instagram profiles: {exc}"
            ) from exc

    def _extract_structured_output(
        self,
        history: AgentHistoryList[Any],
    ) -> DiscoveryResult:
        try:
            result = history.structured_output
        except ValidationError as exc:
            raise RuntimeError("Browser Use did not return a DiscoveryResult.") from exc

        if result is None:
            raise RuntimeError("Browser Use did not return a DiscoveryResult.")

        if not isinstance(result, DiscoveryResult):
            raise TypeError(
                "Browser Use returned structured output of unexpected type "
                f"{type(result).__name__}"
            )

        return result

    def _normalize_urls(self, urls: list[str]) -> list[str]:
        unique: list[str] = []
        seen: set[str] = set()

        for url in urls:
            normalized = self._normalize_profile_url(url)
            if normalized is None:
                continue
            key = normalized.rstrip("/").lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append(normalized)
            if len(unique) >= self._max_results:
                break

        return unique

    @staticmethod
    def _normalize_query(query: str) -> str:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")
        return query.strip()

    @staticmethod
    def _build_google_search_url(query: str) -> str:
        return "https://www.google.com/search?q=" + quote_plus(
            f"site:instagram.com {query}"
        )

    @staticmethod
    def _normalize_profile_url(url: str) -> str | None:
        if not isinstance(url, str) or not url.strip():
            return None

        candidate = url.strip()
        if not candidate.startswith(("http://", "https://")):
            candidate = "https://" + candidate.lstrip("/")

        parsed = urlparse(candidate)
        host = (parsed.netloc or "").lower().removeprefix("www.")
        if host != "instagram.com":
            return None

        match = _PROFILE_PATH_RE.match(parsed.path or "")
        if match is None:
            return None

        username = match.group(1)
        if username.lower() in _NON_PROFILE_SEGMENTS:
            return None

        return f"https://www.instagram.com/{username}/"
