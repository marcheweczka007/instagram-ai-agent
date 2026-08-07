"""Page modules for the marketing workspace."""

from instagram_agent.ui.pages.comments import render_comments_page
from instagram_agent.ui.pages.creators import render_creators_page
from instagram_agent.ui.pages.dashboard import render_dashboard_page
from instagram_agent.ui.pages.discover import render_discover_page
from instagram_agent.ui.pages.outreach import render_outreach_page
from instagram_agent.ui.pages.reports import render_reports_page
from instagram_agent.ui.pages.settings import render_settings_page

__all__ = [
    "render_comments_page",
    "render_creators_page",
    "render_dashboard_page",
    "render_discover_page",
    "render_outreach_page",
    "render_reports_page",
    "render_settings_page",
]
