"""E2E test for the sidebar footer user-menu dropdown (issue #191).

Real-browser test, not a template-only assertion: the defect is a CSS box
computation (`.dropdown-content`'s `min-w-52` floor against a ~48px icon-rail
trigger) that only a live layout render exposes.
"""

import re

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


def _user_menu_trigger(sidebar, username):
    """The footer's user-menu trigger, scoped by the signed-in user's name.

    The fixed footer (docs/adr/0023) always renders a theme control
    alongside the user menu, and the theme control's own trigger can also
    carry ``role="button"`` — a bare ``[role="button"]`` locator is
    ambiguous. The compact user display always shows the username, so
    filtering on it identifies the user-menu trigger specifically.
    """
    return sidebar.locator('[role="button"]').filter(has_text=username)


@pytest.mark.django_db
class TestSidebarUserMenuIconRail:
    """The footer user-menu dropdown when the sidebar is collapsed to its icon rail."""

    def test_dropdown_panel_stays_within_the_viewport(
        self, page, live_server, monkeypatch
    ):
        """Opening the trigger in icon-rail mode must not push the panel off-screen."""
        monkeypatch.setitem(MVP_CONFIG["layout"]["sidebar"], "collapse", "icons")
        user = get_user_model().objects.create_user(username="railuser", password="pw")
        _login_in_browser(page, live_server, user)

        page.set_viewport_size(DESKTOP)
        page.goto(live_server.url)

        # Collapse the persistent sidebar to its icon rail.
        page.get_by_label("Toggle sidebar").click()
        expect(page.locator("#mvp-app-toggle")).not_to_be_checked()

        sidebar = page.locator("aside.mvp-sidebar")
        trigger = _user_menu_trigger(sidebar, user.username)
        trigger.click()

        panel = sidebar.locator(".dropdown-content")
        expect(panel).to_be_visible()
        box = panel.bounding_box()
        assert box is not None
        assert box["x"] >= 0, (
            f"dropdown panel rendered at x={box['x']}, off-screen to the left"
        )

    def test_dropdown_rows_keep_their_labels(self, page, live_server, monkeypatch):
        """Issue #209: rail mode blanked every row inside the open panel.

        The rail hides labels because the column is too narrow to hold them.
        That rule was scoped to the whole sidebar subtree, and the dropdown
        panel renders inside it — so a user opening the account menu got a
        column of icons with no words. The panel is a popover with its own
        width, so its labels have to survive.
        """
        monkeypatch.setitem(MVP_CONFIG["layout"]["sidebar"], "collapse", "icons")
        user = get_user_model().objects.create_user(username="railuser3", password="pw")
        _login_in_browser(page, live_server, user)

        page.set_viewport_size(DESKTOP)
        page.goto(live_server.url)

        page.get_by_label("Toggle sidebar").click()
        expect(page.locator("#mvp-app-toggle")).not_to_be_checked()

        sidebar = page.locator("aside.mvp-sidebar")
        _user_menu_trigger(sidebar, user.username).click()

        panel = sidebar.locator(".dropdown-content")
        expect(panel).to_be_visible()

        # "Log out" is the one row that renders whatever else a project
        # configures — "Account Center" needs an account-center URL to exist.
        expect(panel.get_by_text("Log out")).to_be_visible()

        labels = panel.locator(":is(a, button) > span")
        assert labels.count() > 0, "the panel rendered no label spans at all"
        for index in range(labels.count()):
            expect(labels.nth(index)).to_be_visible()

    def test_dropdown_panel_still_spans_the_trigger_when_expanded(
        self, page, live_server, monkeypatch
    ):
        """Regression guard: the icon-rail fix must not change the expanded
        layout.

        The footer is now a fixed row shared with the theme and language
        controls (docs/adr/0023), so the compact user-menu trigger can
        render narrower than the panel's own ``min-w-52`` floor — matching
        the panel's width to the trigger's exactly is no longer the
        invariant to hold. What must still hold is that the panel stays
        anchored to the trigger's leading edge and never renders narrower
        than it (which would clip the menu against its own trigger).
        """
        monkeypatch.setitem(MVP_CONFIG["layout"]["sidebar"], "collapse", "icons")
        user = get_user_model().objects.create_user(username="railuser2", password="pw")
        _login_in_browser(page, live_server, user)

        page.set_viewport_size(DESKTOP)
        page.goto(live_server.url)
        # sidebar stays expanded (no toggle click) — persistent open defaults to true

        sidebar = page.locator("aside.mvp-sidebar")
        trigger = _user_menu_trigger(sidebar, user.username)
        trigger.click()

        panel = sidebar.locator(".dropdown-content")
        expect(panel).to_be_visible()
        panel_box = panel.bounding_box()
        trigger_box = trigger.bounding_box()
        assert panel_box is not None and trigger_box is not None
        assert panel_box["x"] == pytest.approx(trigger_box["x"], abs=1)
        assert panel_box["width"] >= trigger_box["width"], (
            "the panel must never render narrower than its own trigger"
        )


@pytest.mark.django_db
class TestSidebarUserMenuLongUsername:
    """[#368] A long username let the trigger grow past its row instead of
    truncating, and the overflow sat on top of the theme and language
    controls beside it — a live click is what actually proves whether a
    control is still reachable, not a class on the markup."""

    def test_theme_control_stays_clickable_with_a_long_username(
        self, page, live_server
    ):
        user = get_user_model().objects.create_user(
            username="a-username-far-too-long-to-fit-in-the-sidebar-footer-row",
            password="pw",
        )
        _login_in_browser(page, live_server, user)

        page.set_viewport_size(DESKTOP)
        page.goto(live_server.url)

        sidebar = page.locator("aside.mvp-sidebar")
        theme_toggle = sidebar.get_by_role("button", name="Toggle dark mode")
        theme_toggle.click()

        expect(theme_toggle).to_have_class(re.compile(r"\bswap-active\b"))

    def test_language_control_stays_clickable_with_a_long_username(
        self, page, live_server
    ):
        user = get_user_model().objects.create_user(
            username="a-username-far-too-long-to-fit-in-the-sidebar-footer-row",
            password="pw",
        )
        _login_in_browser(page, live_server, user)

        page.set_viewport_size(DESKTOP)
        page.goto(live_server.url)

        sidebar = page.locator("aside.mvp-sidebar")
        language_button = sidebar.get_by_role("button", name="Select a language")
        language_button.click()

        expect(page.locator("#languageModal")).to_be_visible()
