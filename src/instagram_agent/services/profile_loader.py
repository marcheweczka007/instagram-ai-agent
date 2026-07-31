import json
from pathlib import Path

from instagram_agent.domain.models import InstagramProfile


def load_example_profile() -> InstagramProfile:
    """Load a sample Instagram profile from a JSON file."""

    file_path = Path("data/example_profile.json")

    with file_path.open("r") as file:
        data = json.load(file)

    return InstagramProfile(**data)