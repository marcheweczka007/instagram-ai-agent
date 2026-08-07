from types import SimpleNamespace
from unittest.mock import MagicMock

from instagram_agent.agents.research import ResearchAgent
from instagram_agent.domain.models import (
    InstagramProfile,
    ProfileAnalysis,
    ResearchAnalysis,
)
from instagram_agent.fixtures import build_jollyzu_brand


def test_research_agent_returns_structured_result() -> None:
    expected = ResearchAnalysis(
        brand_fit=9,
        confidence=8,
        audience_match="Eco women",
        aesthetic_match="Colourful craft",
        value_alignment="Strong",
        collaboration_potential="High",
        overall_summary="Excellent handmade sustainability fit.",
        strengths=["Audience overlap"],
        weaknesses=["Limited reach"],
        collaboration_ideas=["Capsule drop"],
        first_outreach_angle="Love your colour stories",
    )
    client = MagicMock()
    client.chat.completions.parse.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(parsed=expected))]
    )

    agent = ResearchAgent(client=client)
    brand = build_jollyzu_brand()
    profile = InstagramProfile(
        name="EcoMaker",
        profile_url="https://www.instagram.com/ecomaker/",
        bio="Upcycled bags",
        followers=1000,
        following=100,
        recent_posts=["post"],
    )
    analysis = ProfileAnalysis(
        score=8,
        follow=True,
        reason="fit",
        comment="nice",
    )

    result = agent.research(brand, profile, analysis)
    assert result.brand_fit == 9
    assert "Capsule" in result.collaboration_ideas[0]
