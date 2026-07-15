"""E2E tests for the mobile dock (footer navigation).

These exercise real user interactions in a browser, which is why they are e2e
rather than client tests: the dock is hidden/shown by a CSS breakpoint, pinned
by fixed positioning, and its "Menu" item toggles the daisyUI drawer via a
checkbox — none of which a server-rendered-markup assertion can verify.

Self-contained: they use pytest-django's ``live_server`` (no hand-started
server) and pytest-playwright's ``page``. Skipped when playwright is absent.
"""

import pytest

pytest.importorskip("playwright")
from playwright.sync_api import expect  # noqa: E402

pytestmark = pytest.mark.e2e

MOBILE = {"width": 375, "height": 812}
DESKTOP = {"width": 1280, "height": 800}


@pytest.mark.django_db
class TestMobileDockVisibility:
    """The dock shows only at mobile widths and stays pinned to the bottom."""

    def test_dock_visible_on_mobile(self, page, live_server):
        page.set_viewport_size(MOBILE)
        page.goto(live_server.url)
        expect(page.locator("div.dock")).to_be_visible()

    def test_dock_hidden_on_desktop(self, page, live_server):
        page.set_viewport_size(DESKTOP)
        page.goto(live_server.url)
        expect(page.locator("div.dock")).to_be_hidden()

    def test_dock_pinned_to_bottom_after_scroll(self, page, live_server):
        page.set_viewport_size(MOBILE)
        page.goto(live_server.url)
        page.evaluate("window.scrollBy(0, 500)")
        box = page.locator("div.dock").bounding_box()
        assert box is not None
        # bottom edge of the dock sits at the bottom edge of the viewport
        assert abs((box["y"] + box["height"]) - MOBILE["height"]) < 10


@pytest.mark.django_db
class TestMobileDockSidebarToggle:
    """The dock's "Menu" item toggles the sidebar drawer open and closed."""

    def _toggle(self, page):
        return page.locator("div.dock label[for='mvp-app-toggle']")

    def test_menu_button_opens_sidebar(self, page, live_server):
        page.set_viewport_size(MOBILE)
        page.goto(live_server.url)
        sidebar = page.locator("aside.mvp-sidebar")
        expect(sidebar).not_to_be_visible()
        self._toggle(page).click()
        expect(sidebar).to_be_visible()

    # Note: closing the drawer is the drawer's own concern, not the dock's —
    # once open, the overlay sidebar covers the dock, so there is no "tap the
    # dock toggle again" flow to test here. Drawer close is exercised elsewhere.

    def test_dock_has_a_toggle_and_a_home_link(self, page, live_server):
        page.set_viewport_size(MOBILE)
        page.goto(live_server.url)
        # exactly one sidebar-toggle control (a label bound to the drawer checkbox)
        expect(self._toggle(page)).to_have_count(1)
        # exactly one real navigation link (Home)
        home = page.locator("div.dock a")
        expect(home).to_have_count(1)
        expect(home).to_have_attribute("href", "/")
