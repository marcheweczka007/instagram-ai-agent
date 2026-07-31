"""Production-ready Instagram profile scraper using Browser Use."""

from __future__ import annotations

import logging
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
    InstagramScraperError,
    InstagramSessionLostError,
    InstagramStructuredOutputError,
)
from instagram_agent.domain.models import InstagramProfile

logger = logging.getLogger(__name__)

_SESSION_LOST_MARKERS: tuple[str, ...] = (
    "browser not connected",
    "target detached",
    "no tabs remain",
    "session closed",
    "session lost",
    "disconnected",
)

_LOGIN_URL_MARKERS: tuple[str, ...] = (
    "/accounts/login",
    "/accounts/signup",
    "/accounts/emailsignup",
)

_LOGIN_TEXT_MARKERS: tuple[str, ...] = (
    "login_required",
)

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

    def __init__(self, model: str = "gpt-5", max_steps: int = 40) -> None:
        prompt_path = (
            Path(__file__).parent.parent / "prompts" / "scraper.md"
        )
        self._system_prompt: str = prompt_path.read_text(encoding="utf-8")
        self._llm = ChatOpenAI(model=model)
        self._max_steps = max_steps

    async def scrape(self, url: str) -> InstagramProfile:
        """Scrape an Instagram profile URL and return structured data."""
        cleaned_url = self._normalize_url(url)
        logger.info("Starting Instagram scrape for %s", cleaned_url)

        try:
            return await self._scrape_with_retry(cleaned_url)
        except InstagramScraperError:
            raise
        except Exception as exc:
            logger.exception("Unexpected failure while scraping %s", cleaned_url)
            raise InstagramScraperError(
                f"Failed to scrape Instagram profile at {cleaned_url}: {exc}"
            ) from exc

    async def _scrape_with_retry(self, url: str) -> InstagramProfile:
        try:
            return await self._scrape_once(url)
        except InstagramSessionLostError:
            logger.warning(
                "Browser session lost while scraping %s; retrying once",
                url,
            )
            return await self._scrape_once(url)

    async def _scrape_once(self, url: str) -> InstagramProfile:
        task = self._build_task(url)
        history = await self._run_agent(task)

        # Hard failures first: login redirect or explicit agent stop signals.
        self._raise_for_login_redirect(history, url)
        self._raise_for_explicit_stop_signals(history, url)

        profile = self._extract_structured_output(history, url)
        if profile is not None:
            return self._validate_profile(profile, url)

        # No structured output: classify the failure precisely.
        self._raise_for_page_conditions(history, url)

        if self._is_session_lost(history):
            raise InstagramSessionLostError(
                f"Browser session was lost while scraping {url}"
            )

        final = history.final_result()
        detail = f" Final agent result: {final}" if final else ""
        raise InstagramStructuredOutputError(
            "Browser Use did not return a structured InstagramProfile "
            f"for {url}.{detail}"
        )

    def _build_task(self, url: str) -> str:
        return f"""
{self._system_prompt}

Open this Instagram profile URL:

{url}

Reliability rules:
1. After navigating, wait until the page has fully finished loading before extracting data.
2. Dismiss cookie / signup modals only when they block profile content.
3. If Instagram redirects to a login or signup page, stop immediately and report LOGIN_REQUIRED.
4. If the profile does not exist (page isn't available), stop immediately and report PROFILE_NOT_FOUND.
5. If the account is private, stop immediately and report PRIVATE_PROFILE.
6. Otherwise extract the public profile fields into the required structured output.
""".strip()

    async def _run_agent(self, task: str) -> AgentHistoryList[Any]:
        logger.debug("Creating Browser Use agent")
        agent = Agent(
            task=task,
            llm=self._llm,
            output_model_schema=InstagramProfile,
            max_failures=3,
            directly_open_url=True,
        )

        try:
            history = await agent.run(max_steps=self._max_steps)
        except Exception as exc:
            if self._text_has_markers(str(exc), _SESSION_LOST_MARKERS):
                raise InstagramSessionLostError(
                    f"Browser session lost during scrape: {exc}"
                ) from exc
            raise

        logger.info(
            "Browser Use finished in %s steps (success=%s)",
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

        logger.info(
            "Scraped profile '%s' (%s followers)",
            profile.name,
            profile.followers,
        )
        return profile

    def _extract_structured_output(
        self,
        history: AgentHistoryList[Any],
        url: str,
    ) -> InstagramProfile | None:
        try:
            profile = history.structured_output
        except ValidationError as exc:
            raise InstagramStructuredOutputError(
                "Browser Use returned structured output that could not be "
                f"parsed as InstagramProfile for {url}: {exc}"
            ) from exc

        if profile is None:
            return None

        if not isinstance(profile, InstagramProfile):
            raise InstagramStructuredOutputError(
                "Browser Use returned structured output of unexpected type "
                f"{type(profile).__name__} for {url}"
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

    def _is_session_lost(self, history: AgentHistoryList[Any]) -> bool:
        last_url = self._last_url(history)
        if last_url and last_url.rstrip("/").endswith("about:blank"):
            return True

        # Only inspect the most recent errors so earlier recovered failures
        # do not trigger a false session-lost retry.
        recent_errors = [
            error.lower()
            for error in history.errors()[-3:]
            if error
        ]
        return any(
            self._text_has_markers(error, _SESSION_LOST_MARKERS)
            for error in recent_errors
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
