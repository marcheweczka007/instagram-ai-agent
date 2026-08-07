import pytest

from instagram_agent.browser.instagram_scraper import InstagramScraper


def test_normalize_url_requires_instagram() -> None:
    with pytest.raises(ValueError):
        InstagramScraper._normalize_url("https://example.com/x")


def test_normalize_url_accepts_profile() -> None:
    assert (
        InstagramScraper._normalize_url(" https://www.instagram.com/patagonia/ ")
        == "https://www.instagram.com/patagonia/"
    )
