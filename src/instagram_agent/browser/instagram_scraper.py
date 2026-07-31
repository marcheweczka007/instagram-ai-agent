"""Instagram profile scraper using Browser Use (fail-fast)."""

from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from typing import Any

from browser_use import Agent, ChatOpenAI
from browser_use.agent.views import AgentHistoryList
from pydantic import ValidationError

from instagram_agent.browser.exceptions import (
    InstagramInvalidProfileError,
    InstagramLoginRequiredError,
    InstagramPrivateProfileError,
    InstagramProfileNotFoundError,
)
from instagram_agent.domain.models import InstagramProfile

logger = logging.getLogger(__name__)

_SPEED_PROMPT = """
Be concise. Prefer extract + done over exploration.
Dismiss blocking modals only if needed, then extract visible profile fields.
Do not open posts. Do not browse related accounts.
""".strip()

_LOGIN_URL_MARKERS: tuple[str, ...] = (
    "/accounts/login",
    "/accounts/signup",
    "/accounts/emailsignup",
)

_LOGIN_TEXT_MARKERS: tuple[str, ...] = ("login_required",)

_NOT_FOUND_MARKERS: tuple[str, ...] = (
    "profile_not_found",
    "sorry, this page isn't available",
    "the link you followed may be broken",
)

_PRIVATE_MARKERS: tuple[str, ...] = (
    "private_profile",
    "this account is private",
)


class InstagramScraper:
    """Scrape a public Instagram profile into an ``InstagramProfile``."""

    def __init__(
        self,
        model: str = "gpt-5",
        extraction_model: str = "gpt-5-mini",
        max_steps: int = 8,
        timeout_seconds: float = 60,
    ) -> None:
        prompt_path = Path(__file__).parent.parent / "prompts" / "scraper.md"
        self._system_prompt: str = prompt_path.read_text(encoding="utf-8")
        # Low reasoning + few retries: LLM waits were the timeout bottleneck.
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

    async def scrape(self, url: str) -> InstagramProfile:
        """Scrape an Instagram profile URL and return structured data."""
        cleaned_url = self._normalize_url(url)
        scrape_started = time.perf_counter()
        logger.info("scrape() started for %s", cleaned_url)

        try:
            profile = await self._scrape_once(cleaned_url)
        except Exception as exc:
            elapsed = time.perf_counter() - scrape_started
            logger.exception(
                "Instagram scrape failed for %s after %.2fs: %s: %s",
                cleaned_url,
                elapsed,
                type(exc).__name__,
                exc,
            )
            raise

        elapsed = time.perf_counter() - scrape_started
        logger.info(
            "scrape() completed successfully for %s in %.2fs",
            cleaned_url,
            elapsed,
        )
        return profile

    async def _scrape_once(self, url: str) -> InstagramProfile:
        logger.info("_scrape_once() entered for %s", url)

        task = self._build_task(url)
        logger.info("task built for %s (length=%s)", url, len(task))

        history = await self._run_agent(task, url)

        self._raise_for_login_redirect(history, url)
        self._raise_for_explicit_stop_signals(history, url)
        logger.info("login checks passed for %s", url)

        self._raise_for_page_conditions(history, url)
        logger.info("page condition checks passed for %s", url)

        profile = self._extract_structured_output(history)
        if profile is None:
            raise RuntimeError(
                "Browser Use did not return an InstagramProfile."
            )
        logger.info("structured output extracted for %s", url)

        validated = self._validate_profile(profile, url)
        logger.info("profile validation passed for %s", url)
        return validated

    def _build_task(self, url: str) -> str:
        return f"""
{self._system_prompt}

Profile URL (already opening): {url}

Goal: extract the structured InstagramProfile from the loaded page and finish.
""".strip()

    async def _run_agent(
        self,
        task: str,
        url: str,
    ) -> AgentHistoryList[Any]:
        agent = Agent(
            task=task,
            llm=self._llm,
            page_extraction_llm=self._extraction_llm,
            output_model_schema=InstagramProfile,
            # Navigate before any LLM step to save one slow reasoning call.
            initial_actions=[
                {"navigate": {"url": url, "new_tab": False}},
                {"wait": {"seconds": 2}},
            ],
            # Fast extraction path recommended by Browser Use docs.
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
            "Browser Use about to start (max_steps=%s, timeout=%ss, flash_mode=True)",
            self._max_steps,
            self._timeout_seconds,
        )
        agent_started = time.perf_counter()

        try:
            history = await asyncio.wait_for(
                agent.run(max_steps=self._max_steps),
                timeout=self._timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            elapsed = time.perf_counter() - agent_started
            logger.error(
                "Browser Use timed out after %.2fs: %s: %s",
                elapsed,
                type(exc).__name__,
                exc,
            )
            raise RuntimeError("Instagram scraping timed out.") from exc
        except RuntimeError as exc:
            elapsed = time.perf_counter() - agent_started
            logger.error(
                "Browser Use raised RuntimeError after %.2fs: %s: %s",
                elapsed,
                type(exc).__name__,
                exc,
            )
            raise
        except Exception as exc:
            elapsed = time.perf_counter() - agent_started
            logger.error(
                "Browser Use failed after %.2fs: %s: %s",
                elapsed,
                type(exc).__name__,
                exc,
            )
            raise RuntimeError(
                f"Browser Use failed while scraping Instagram: {exc}"
            ) from exc

        elapsed = time.perf_counter() - agent_started
        logger.info(
            "Browser Use finished in %.2fs (%s steps, success=%s)",
            elapsed,
            history.number_of_steps(),
            history.is_successful(),
        )
        return history

    def _validate_profile(
        self,
        profile: InstagramProfile,
        url: str,
    ) -> InstagramProfile:
        errors: list[str] = []

        if not profile.name or not profile.name.strip():
            errors.append("name is empty")
        if profile.followers < 0:
            errors.append("followers must be >= 0")
        if profile.following < 0:
            errors.append("following must be >= 0")
        if not profile.profile_url or "instagram.com" not in profile.profile_url:
            errors.append("profile_url is missing or not an Instagram URL")
        if profile.recent_posts is None:
            errors.append("recent_posts is missing")

        if errors:
            raise InstagramInvalidProfileError(
                f"Scraped profile for {url} failed validation: {', '.join(errors)}"
            )

        return profile

    def _extract_structured_output(
        self,
        history: AgentHistoryList[Any],
    ) -> InstagramProfile | None:
        try:
            profile = history.structured_output
        except ValidationError as exc:
            raise RuntimeError(
                "Browser Use did not return an InstagramProfile."
            ) from exc

        if profile is None:
            return None

        if not isinstance(profile, InstagramProfile):
            raise RuntimeError(
                "Browser Use did not return an InstagramProfile."
            )

        return profile

    def _raise_for_login_redirect(
        self,
        history: AgentHistoryList[Any],
        url: str,
    ) -> None:
        final_url = self._last_url(history)
        if final_url and self._text_has_markers(final_url, _LOGIN_URL_MARKERS):
            raise InstagramLoginRequiredError(
                f"Instagram redirected to login while opening {url} "
                f"(final URL: {final_url})"
            )

    def _raise_for_explicit_stop_signals(
        self,
        history: AgentHistoryList[Any],
        url: str,
    ) -> None:
        final_text = (history.final_result() or "").lower()

        if self._text_has_markers(final_text, _LOGIN_TEXT_MARKERS):
            raise InstagramLoginRequiredError(
                f"Instagram requires login to view profile: {url}"
            )
        if "profile_not_found" in final_text:
            raise InstagramProfileNotFoundError(
                f"Instagram profile does not exist: {url}"
            )
        if "private_profile" in final_text:
            raise InstagramPrivateProfileError(
                f"Instagram profile is private: {url}"
            )

    def _raise_for_page_conditions(
        self,
        history: AgentHistoryList[Any],
        url: str,
    ) -> None:
        history_text = self._history_text(history)

        if self._text_has_markers(history_text, _NOT_FOUND_MARKERS):
            raise InstagramProfileNotFoundError(
                f"Instagram profile does not exist: {url}"
            )

        if self._text_has_markers(history_text, _PRIVATE_MARKERS):
            raise InstagramPrivateProfileError(
                f"Instagram profile is private: {url}"
            )

    @staticmethod
    def _normalize_url(url: str) -> str:
        if not isinstance(url, str) or not url.strip():
            raise ValueError("url must be a non-empty Instagram profile URL")

        cleaned = url.strip()
        if "instagram.com" not in cleaned.lower():
            raise ValueError(
                f"url must be an Instagram profile URL, got: {cleaned!r}"
            )
        return cleaned

    @staticmethod
    def _last_url(history: AgentHistoryList[Any]) -> str | None:
        urls = [url for url in history.urls() if url]
        return urls[-1] if urls else None

    @staticmethod
    def _history_text(history: AgentHistoryList[Any]) -> str:
        parts: list[str] = []

        final = history.final_result()
        if final:
            parts.append(final)

        for item in history.extracted_content():
            if item:
                parts.append(item)

        for error in history.errors():
            if error:
                parts.append(error)

        return "\n".join(parts).lower()

    @staticmethod
    def _text_has_markers(text: str, markers: tuple[str, ...]) -> bool:
        lowered = text.lower()
        return any(marker in lowered for marker in markers)
