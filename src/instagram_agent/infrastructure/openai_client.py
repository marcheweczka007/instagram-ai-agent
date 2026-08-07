"""Shared OpenAI client factory."""

from __future__ import annotations

from functools import lru_cache

from openai import OpenAI

from instagram_agent.config import get_settings


@lru_cache(maxsize=1)
def create_client() -> OpenAI:
    """Return a process-wide OpenAI client instance."""
    return OpenAI(api_key=get_settings().openai_api_key)
