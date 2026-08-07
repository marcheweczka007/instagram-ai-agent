"""Page modules for the marketing workspace."""

from instagram_agent.ui.pages.creators import render_creators_page
from instagram_agent.ui.pages.discover import render_discover_page
from instagram_agent.ui.pages.opportunities import render_opportunities_page
from instagram_agent.ui.pages.reports import render_reports_page
from instagram_agent.ui.pages.settings import render_settings_page

__all__ = [
    "render_creators_page",
    "render_discover_page",
    "render_opportunities_page",
    "render_reports_page",
    "render_settings_page",
]
