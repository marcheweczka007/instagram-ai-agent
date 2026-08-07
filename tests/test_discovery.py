from instagram_agent.agents.discovery import DiscoveryAgent


def test_normalize_profile_url_accepts_profiles() -> None:
    assert (
        DiscoveryAgent._normalize_profile_url("https://www.instagram.com/patagonia/")
        == "https://www.instagram.com/patagonia/"
    )
    assert (
        DiscoveryAgent._normalize_profile_url("instagram.com/upcycle.lab.jollyzu")
        == "https://www.instagram.com/upcycle.lab.jollyzu/"
    )


def test_normalize_profile_url_rejects_non_profiles() -> None:
    assert (
        DiscoveryAgent._normalize_profile_url("https://www.instagram.com/p/abc/")
        is None
    )
    assert (
        DiscoveryAgent._normalize_profile_url("https://www.instagram.com/reel/xyz/")
        is None
    )
    assert DiscoveryAgent._normalize_profile_url("https://www.pinterest.com/x/") is None


def test_normalize_urls_dedupes_and_caps() -> None:
    agent = object.__new__(DiscoveryAgent)
    agent._max_results = 2
    urls = DiscoveryAgent._normalize_urls(
        agent,
        [
            "https://www.instagram.com/a/",
            "https://instagram.com/a",
            "https://www.instagram.com/b/",
            "https://www.instagram.com/c/",
        ],
    )
    assert urls == [
        "https://www.instagram.com/a/",
        "https://www.instagram.com/b/",
    ]
