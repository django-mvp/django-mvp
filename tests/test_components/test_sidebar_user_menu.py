"""E2E test for the sidebar footer user-menu dropdown (issue #191).

Real-browser test, not a template-only assertion: the defect is a CSS box
computation (`.dropdown-content`'s `min-w-52` floor against a ~48px icon-rail
trigger) that only a live layout render exposes.
"""

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client
from playwright.sync_api import expect

from mvp.config import MVP_CONFIG
from tests.conftest import requires_browser

pytestmark = [pytest.mark.e2e, requires_browser]

DESKTOP = {"width": 1280, "height": 800}


def _login_in_browser(page, live_server, user):
    """Authenticate the Playwright browser context via a Django session cookie."""
    client = Client()
    client.force_login(user)
    session_cookie = client.cookies[settings.SESSION_COOKIE_NAME]
    page.context.add_cookies(
        [
            {
                "name": settings.SESSION_COOKIE_NAME,
                "value": session_cookie.value,
                "url": live_server.url,
            }
        ]
    )


@pytest.mark.django_db
class TestSidebarUserMenuIconRail:
    """The footer user-menu dropdown when the sidebar is collapsed to its icon rail."""

    def test_dropdown_panel_stays_within_the_viewport(
        self, page, live_server, monkeypatch
    ):
        """Opening the trigger in icon-rail mode must not push the panel off-screen."""
        monkeypatch.setitem(MVP_CONFIG["layout"]["sidebar"], "collapse", "icons")
        monkeypatch.setitem(
            MVP_CONFIG["layout"]["sidebar"], "footer", ["user.sidebar-menu"]
        )
        user = get_user_model().objects.create_user(username="railuser", password="pw")
        _login_in_browser(page, live_server, user)

        page.set_viewport_size(DESKTOP)
        page.goto(live_server.url)

        # Collapse the persistent sidebar to its icon rail.
        page.get_by_label("Toggle sidebar").click()
        expect(page.locator("#mvp-app-toggle")).not_to_be_checked()

        sidebar = page.locator("aside.mvp-sidebar")
        trigger = sidebar.locator('[role="button"]')
        trigger.click()

        panel = sidebar.locator(".dropdown-content")
        expect(panel).to_be_visible()
        box = panel.bounding_box()
        assert box is not None
        assert box["x"] >= 0, (
            f"dropdown panel rendered at x={box['x']}, off-screen to the left"
        )

    def test_dropdown_panel_still_spans_the_trigger_when_expanded(
        self, page, live_server, monkeypatch
    ):
        """Regression guard: the icon-rail fix must not change the expanded layout,
        where the panel already matched the trigger's full width."""
        monkeypatch.setitem(MVP_CONFIG["layout"]["sidebar"], "collapse", "icons")
        monkeypatch.setitem(
            MVP_CONFIG["layout"]["sidebar"], "footer", ["user.sidebar-menu"]
        )
        user = get_user_model().objects.create_user(username="railuser2", password="pw")
        _login_in_browser(page, live_server, user)

        page.set_viewport_size(DESKTOP)
        page.goto(live_server.url)
        # sidebar stays expanded (no toggle click) — persistent open defaults to true

        sidebar = page.locator("aside.mvp-sidebar")
        trigger = sidebar.locator('[role="button"]')
        trigger.click()

        panel = sidebar.locator(".dropdown-content")
        expect(panel).to_be_visible()
        panel_box = panel.bounding_box()
        trigger_box = trigger.bounding_box()
        assert panel_box is not None and trigger_box is not None
        assert panel_box["x"] == pytest.approx(trigger_box["x"], abs=1)
        assert panel_box["width"] == pytest.approx(trigger_box["width"], abs=1)
