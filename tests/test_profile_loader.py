from instagram_agent.services.profile_loader import load_example_profile


def test_load_example_profile() -> None:
    profile = load_example_profile()
    assert profile.name
    assert "instagram.com" in profile.profile_url
    assert profile.followers > 0
