"""Shared Browser Use LLM helpers."""

from __future__ import annotations

from browser_use import ChatOpenAI

from instagram_agent.config import Settings, get_settings


def build_chat_openai(
    *,
    model: str | None = None,
    extraction: bool = False,
    settings: Settings | None = None,
) -> ChatOpenAI:
    """Create a ChatOpenAI client using project settings."""
    cfg = settings or get_settings()
    if extraction:
        return ChatOpenAI(
            model=model or cfg.extraction_model,
            temperature=0.0,
            reasoning_effort="minimal",
            max_retries=1,
            max_completion_tokens=1024,
            timeout=cfg.extraction_http_timeout_seconds,
        )
    return ChatOpenAI(
        model=model or cfg.openai_model,
        temperature=0.0,
        reasoning_effort="minimal",
        max_retries=1,
        max_completion_tokens=2048,
        timeout=cfg.llm_http_timeout_seconds,
    )
