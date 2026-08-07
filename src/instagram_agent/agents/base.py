"""Shared agent base class."""

from __future__ import annotations

from openai import OpenAI

from instagram_agent.infrastructure.openai_client import create_client


class BaseAgent:
    """Base class for OpenAI-backed agents."""

    def __init__(self, client: OpenAI | None = None) -> None:
        self.client = client or create_client()
