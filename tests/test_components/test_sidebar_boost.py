"""Boosted sidebar navigation, in a real browser (issue #188).

``hx-boost`` replaces a full page load with an htmx swap of the body. Whether
that leaves the page in a working state is not visible in the server-rendered
markup: it depends on what survives the swap, what re-initialises afterwards,
and what quietly stops responding. ``test_layout_config.py`` pins the markup
contract; these tests pin the behaviour that markup is supposed to buy.

Three things have to hold, and each has already failed in some project
somewhere:

1. the navigation really is boosted — no document load, the URL still changes;
2. the mobile drawer is not left covering the page it just navigated to;
3. controls outside the swapped-in markup still work afterwards.
"""

import pytest
from playwright.sync_api import expect

from mvp.config import MVP_CONFIG
from tests.conftest import requires_browser

pytestmark = [pytest.mark.e2e, requires_browser]

MOBILE = {"width": 800, "height": 900}
DESKTOP = {"width": 1280, "height": 800}


@pytest.fixture
def boosted(monkeypatch):
    monkeypatch.setitem(MVP_CONFIG["layout"]["sidebar"], "boost", True)


def _mark_document(page):
    """Tag the current document so a later check can tell a boosted swap from
    a full page load — the marker only survives if the document did."""
    page.evaluate("() => { window.__sameDocument = true }")


def _document_survived(page):
    return page.evaluate("() => window.__sameDocument === true")


def _layout_link(page):
    """The sidebar's own link to the demo's /theme/ page."""
    return page.locator("aside.mvp-sidebar a[href='/theme/']").first


def _theme_changes_on_one_click(page):
    """Whether a single click on the theme toggle leaves a different theme.

    False covers both ways the control can be broken: no listener at all, and
    two listeners cancelling each other out.
    """
    before = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
    page.locator("[data-toggle-theme]").first.click()
    page.wait_for_timeout(100)
    after = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
    return after != before


@pytest.mark.django_db
class TestBoostedSidebarNavigation:
    def test_a_sidebar_link_navigates_without_a_document_load(
        self, page, live_server, boosted
    ):
        page.set_viewport_size(DESKTOP)
        page.goto(f"{live_server.url}/")
        _mark_document(page)

        _layout_link(page).click()
        page.wait_for_url(f"{live_server.url}/theme/")

        assert _document_survived(page), (
            "the sidebar link triggered a full document load — hx-boost was "
            "not applied, or htmx is not running on the page"
        )

    def test_an_unboosted_sidebar_link_still_loads_the_document(
        self, page, live_server
    ):
        page.set_viewport_size(DESKTOP)
        page.goto(f"{live_server.url}/")
        _mark_document(page)

        _layout_link(page).click()
        page.wait_for_url(f"{live_server.url}/theme/")

        assert not _document_survived(page), (
            "with boost off a sidebar link must perform an ordinary "
            "navigation, so the marker cannot survive it"
        )


@pytest.mark.django_db
class TestBoostedNavigationClosesTheDrawer:
    def _open_the_drawer(self, page):
        page.locator("label[for='mvp-app-toggle'][aria-label='Open sidebar']").click()
        expect(page.locator("#mvp-app-toggle")).to_be_checked()

    @pytest.mark.usefixtures("mobile_navbar_toggle")
    def test_the_overlay_drawer_closes_after_a_boosted_click(
        self, page, live_server, boosted
    ):
        page.set_viewport_size(MOBILE)
        page.goto(f"{live_server.url}/")
        self._open_the_drawer(page)
        _mark_document(page)

        _layout_link(page).click()
        page.wait_for_url(f"{live_server.url}/theme/")

        assert _document_survived(page), "precondition: the click was boosted"
        expect(page.locator("#mvp-app-toggle")).not_to_be_checked()

    def test_the_desktop_sidebar_stays_open_after_a_boosted_click(
        self, page, live_server, boosted
    ):
        page.set_viewport_size(DESKTOP)
        page.goto(f"{live_server.url}/")
        expect(page.locator("#mvp-app-toggle")).to_be_checked()
        _mark_document(page)

        _layout_link(page).click()
        page.wait_for_url(f"{live_server.url}/theme/")

        assert _document_survived(page), "precondition: the click was boosted"
        expect(page.locator("#mvp-app-toggle")).to_be_checked()


@pytest.mark.django_db
class TestControlsStillWorkAfterABoostedSwap:
    def test_the_theme_toggle_still_works_after_a_boosted_navigation(
        self, page, live_server, boosted
    ):
        page.set_viewport_size(DESKTOP)
        page.goto(f"{live_server.url}/")
        _mark_document(page)

        _layout_link(page).click()
        page.wait_for_url(f"{live_server.url}/theme/")
        assert _document_survived(page), "precondition: the click was boosted"

        toggle = page.locator("[data-toggle-theme]").first
        expect(toggle).to_be_attached()
        before = page.evaluate(
            "() => document.documentElement.getAttribute('data-theme')"
        )
        toggle.click()
        page.wait_for_function(
            "before => document.documentElement.getAttribute('data-theme') !== before",
            arg=before,
        )

        assert (
            page.evaluate("() => document.documentElement.getAttribute('data-theme')")
            != before
        ), (
            "the theme control stopped responding after a boosted swap — its "
            "listener was bound to elements htmx replaced"
        )

    def test_a_partial_swap_does_not_double_bind_the_theme_toggle(
        self, page, live_server
    ):
        page.goto(f"{live_server.url}/")
        page.evaluate(
            """() => {
                const el = document.createElement('div');
                document.body.appendChild(el);
                document.dispatchEvent(new CustomEvent('htmx:afterSettle', {
                    detail: { target: el },
                }));
            }"""
        )

        assert _theme_changes_on_one_click(page), (
            "a partial swap rebound controls it never replaced, so the theme "
            "toggle now fires twice per click and lands where it started"
        )

    def test_double_binding_would_be_caught(self, page, live_server):
        page.goto(f"{live_server.url}/")
        page.evaluate(
            """() => document.dispatchEvent(new CustomEvent('htmx:afterSettle', {
                detail: { target: document.body },
            }))"""
        )

        assert not _theme_changes_on_one_click(page), (
            "double-binding the theme toggle left it working, so the "
            "partial-swap guard above proves nothing"
        )


@pytest.mark.django_db
class TestBoostedSidebarForms:
    def test_the_language_switcher_still_switches_when_boosted(
        self, page, live_server, boosted
    ):
        page.set_viewport_size(DESKTOP)
        page.goto(f"{live_server.url}/")
        _mark_document(page)

        sidebar = page.locator("aside.mvp-sidebar")
        # The switcher's fixed sidebar-footer form (docs/adr/0023) sits
        # behind a modal dialog; open it before the language buttons are
        # reachable.
        sidebar.get_by_label("Select a language").click()
        page.locator("#languageModal button[name='language'][value='de']").click()
        page.wait_for_function("() => document.cookie.includes('django_language=de')")

        assert _document_survived(page), (
            "the boosted language form fell back to a full page load"
        )
        cookies = {c["name"]: c["value"] for c in page.context.cookies()}
        assert cookies.get("django_language") == "de", (
            "the boosted POST to set_language did not set the language cookie"
        )
