"""Custom exceptions for Instagram browser scraping."""


class InstagramScraperError(Exception):
    """Base error for Instagram scraping failures."""


class InstagramLoginRequiredError(InstagramScraperError):
    """Instagram redirected to a login / signup wall."""


class InstagramProfileNotFoundError(InstagramScraperError):
    """The requested Instagram profile does not exist."""


class InstagramPrivateProfileError(InstagramScraperError):
    """The Instagram profile is private and cannot be scraped."""


class InstagramSessionLostError(InstagramScraperError):
    """The browser session was lost or disconnected."""


class InstagramStructuredOutputError(InstagramScraperError):
    """Browser Use did not return a valid structured InstagramProfile."""


class InstagramInvalidProfileError(InstagramScraperError):
    """Structured output was returned but failed validation."""
