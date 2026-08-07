"""Load sample profiles for local demos."""

from __future__ import annotations

import json

from instagram_agent.config import PROJECT_ROOT
from instagram_agent.domain.models import InstagramProfile


def load_example_profile() -> InstagramProfile:
    """Load the bundled sample Instagram profile from ``data/``."""
    file_path = PROJECT_ROOT / "data" / "example_profile.json"
    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return InstagramProfile(**data)
