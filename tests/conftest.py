import os

import pytest

os.environ.setdefault("OPENAI_API_KEY", "test-key-for-unit-tests")


@pytest.fixture(autouse=True)
def _clear_caches() -> None:
    from instagram_agent.config import get_settings
    from instagram_agent.infrastructure.openai_client import create_client

    get_settings.cache_clear()
    create_client.cache_clear()
    yield
    get_settings.cache_clear()
    create_client.cache_clear()
