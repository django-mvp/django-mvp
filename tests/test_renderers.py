"""Tests for the mobile dock (footer navigation) and its renderer.

The browser tests exercise real user interactions, which is why they are e2e
rather than client tests: the dock is hidden/shown by a CSS breakpoint, pinned
by fixed positioning, and its "Menu" item toggles the daisyUI drawer via a
checkbox — none of which a server-rendered-markup assertion can verify. They
use pytest-django's ``live_server`` (no hand-started server) and
pytest-playwright's ``page``. Skipped locally when no browser is installed; in
CI the workflow installs one, so a missing browser is an error.

The markup the renderer draws is asserted on the rendered menu, with no browser.
"""

import pytest
from bs4 import BeautifulSoup
from django.test import RequestFactory
from flex_menu import Menu, MenuItem
from playwright.sync_api import expect

from mvp.config import MVP_CONFIG
from mvp.renderers import MobileFooterNavRenderer
from tests.conftest import requires_browser

MOBILE = {"width": 375, "height": 812}
DESKTOP = {"width": 1280, "height": 800}


class TestMobileFooterNavRenderer:
    @pytest.fixture
    def dock(self):
        menu = Menu(
            "DockMarkupTestMenu",
            children=[
                MenuItem(
                    name="sidebar_toggle",
                    extra_context={
                        "label": "Open the sidebar",
                        "icon": "menu",
                        "toggle": "mvp-app-toggle",
                    },
                ),
                MenuItem(
                    name="home",
                    url="/",
                    extra_context={"label": "Home page", "icon": "home"},
                ),
                MenuItem(
                    name="other",
                    url="/other/",
                    extra_context={"label": "Other page", "icon": "list"},
                ),
            ],
        )
        request = RequestFactory().get("/")
        html = MobileFooterNavRenderer().render(menu.process(request))
        return BeautifulSoup(html, "html.parser").select_one("nav.dock")

    def test_the_dock_is_a_navigation_landmark_with_a_name(self, dock):
        assert dock is not None
        assert dock["aria-label"].strip()

    def test_the_sidebar_toggle_has_an_accessible_name(self, dock):
        toggle = dock.select_one("label[for='mvp-app-toggle']")

        assert toggle is not None
        assert toggle["aria-label"].strip()

    def test_the_current_pages_item_is_marked_as_current(self, dock):
        current = dock.select("[aria-current='page']")

        assert len(current) == 1
        assert current[0]["href"] == "/"


@pytest.mark.e2e
@requires_browser
@pytest.mark.django_db
class TestMobileDockVisibility:
    def test_dock_visible_on_mobile(self, page, live_server):
        page.set_viewport_size(MOBILE)
        page.goto(live_server.url)
        expect(page.locator("nav.dock")).to_be_visible()

    def test_dock_hidden_on_desktop(self, page, live_server):
        page.set_viewport_size(DESKTOP)
        page.goto(live_server.url)
        expect(page.locator("nav.dock")).to_be_hidden()

    def test_dock_visible_below_the_configured_sidebar_breakpoint(
        self, page, live_server
    ):
        page.set_viewport_size({"width": 900, "height": 800})
        page.goto(live_server.url)
        expect(page.locator("nav.dock")).to_be_visible()

    def test_dock_visible_at_every_width_when_the_sidebar_breakpoint_is_never(
        self, page, live_server, monkeypatch
    ):
        monkeypatch.setitem(MVP_CONFIG["layout"]["sidebar"], "breakpoint", "never")
        page.set_viewport_size(DESKTOP)
        page.goto(live_server.url)
        expect(page.locator("nav.dock")).to_be_visible()

    def test_dock_pinned_to_bottom_after_scroll(self, page, live_server):
        page.set_viewport_size(MOBILE)
        page.goto(live_server.url)
        page.evaluate("window.scrollBy(0, 500)")
        box = page.locator("nav.dock").bounding_box()
        assert box is not None
        # bottom edge of the dock sits at the bottom edge of the viewport
        assert abs((box["y"] + box["height"]) - MOBILE["height"]) < 10


@pytest.mark.e2e
@requires_browser
@pytest.mark.django_db
class TestMobileDockSidebarToggle:
    def _toggle(self, page):
        return page.locator("nav.dock label[for='mvp-app-toggle']")

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
        home = page.locator("nav.dock a")
        expect(home).to_have_count(1)
        expect(home).to_have_attribute("href", "/")
