from types import SimpleNamespace
from unittest.mock import MagicMock

from instagram_agent.agents.scorer import ScorerAgent
from instagram_agent.domain.models import InstagramProfile, ProfileAnalysis


def test_scorer_returns_parsed_analysis() -> None:
    expected = ProfileAnalysis(
        score=8,
        follow=True,
        reason="Strong handmade fit",
        comment="Love this upcycling story",
    )
    client = MagicMock()
    client.chat.completions.parse.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(parsed=expected))]
    )

    agent = ScorerAgent(client=client)
    profile = InstagramProfile(
        name="EcoMaker",
        profile_url="https://www.instagram.com/ecomaker/",
        bio="Upcycled bags",
        followers=1000,
        following=100,
        recent_posts=["post"],
    )

    result = agent.score(profile)
    assert result.score == 8
    assert result.follow is True
    client.chat.completions.parse.assert_called_once()
