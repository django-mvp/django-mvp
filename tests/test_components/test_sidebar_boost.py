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
    """Turn the opt-in boost on for the duration of one test.

    ``MVP_CONFIG`` is built once at import and read by the templates through
    the context processor, and ``live_server`` runs in this same process, so
    setting the key here reaches the pages the browser fetches.
    """
    monkeypatch.setitem(MVP_CONFIG["layout"]["sidebar"], "boost", True)


def _mark_document(page):
    """Tag the current document so a later check can tell a boosted swap from
    a full page load — the marker only survives if the document did."""
    page.evaluate("() => { window.__sameDocument = true }")


def _document_survived(page):
    return page.evaluate("() => window.__sameDocument === true")


def _layout_link(page):
    """The sidebar's own link to the demo's /layout/ page."""
    return page.locator("aside.mvp-sidebar a[href='/layout/']").first


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
    """A boosted sidebar link swaps the page instead of reloading it."""

    def test_a_sidebar_link_navigates_without_a_document_load(
        self, page, live_server, boosted
    ):
        page.set_viewport_size(DESKTOP)
        page.goto(f"{live_server.url}/")
        _mark_document(page)

        _layout_link(page).click()
        page.wait_for_url(f"{live_server.url}/layout/")

        assert _document_survived(page), (
            "the sidebar link triggered a full document load — hx-boost was "
            "not applied, or htmx is not running on the page"
        )

    def test_an_unboosted_sidebar_link_still_loads_the_document(
        self, page, live_server
    ):
        """The true-negative control for the test above.

        Without it, a marker that never survives anything would report a
        working boost forever, and a marker that always survives would report
        one on a page that never had htmx at all.
        """
        page.set_viewport_size(DESKTOP)
        page.goto(f"{live_server.url}/")
        _mark_document(page)

        _layout_link(page).click()
        page.wait_for_url(f"{live_server.url}/layout/")

        assert not _document_survived(page), (
            "with boost off a sidebar link must perform an ordinary "
            "navigation, so the marker cannot survive it"
        )


@pytest.mark.django_db
class TestBoostedNavigationClosesTheDrawer:
    """The gotcha the issue raised: an overlay drawer left open over the page
    it just navigated to.

    Below the sidebar breakpoint the sidebar is a full-height overlay. A
    normal navigation disposes of it along with the document. A boosted one
    does not navigate, so the drawer only closes if the swap replaces the
    element holding it open.
    """

    def _open_the_drawer(self, page):
        page.locator("label[for='mvp-app-toggle'][aria-label='Open sidebar']").click()
        expect(page.locator("#mvp-app-toggle")).to_be_checked()

    def test_the_overlay_drawer_closes_after_a_boosted_click(
        self, page, live_server, boosted
    ):
        page.set_viewport_size(MOBILE)
        page.goto(f"{live_server.url}/")
        self._open_the_drawer(page)
        _mark_document(page)

        _layout_link(page).click()
        page.wait_for_url(f"{live_server.url}/layout/")

        assert _document_survived(page), "precondition: the click was boosted"
        expect(page.locator("#mvp-app-toggle")).not_to_be_checked()

    def test_the_desktop_sidebar_stays_open_after_a_boosted_click(
        self, page, live_server, boosted
    ):
        """The mirror of the test above, and the reason it cannot simply be
        "close the drawer on every boosted navigation": at desktop widths the
        sidebar is persistent and its open state is remembered. Boosting must
        not collapse it on every click.
        """
        page.set_viewport_size(DESKTOP)
        page.goto(f"{live_server.url}/")
        expect(page.locator("#mvp-app-toggle")).to_be_checked()
        _mark_document(page)

        _layout_link(page).click()
        page.wait_for_url(f"{live_server.url}/layout/")

        assert _document_survived(page), "precondition: the click was boosted"
        expect(page.locator("#mvp-app-toggle")).to_be_checked()


@pytest.mark.django_db
class TestControlsStillWorkAfterABoostedSwap:
    """What a body swap costs, and what the package has to pay back.

    Anything bound by a script that runs once at page load — ``themeChange()``
    is the package's own example — loses its bindings when the elements it
    bound to are swapped out. Nothing reports this: the control renders
    perfectly and simply stops responding.
    """

    def test_the_theme_toggle_still_works_after_a_boosted_navigation(
        self, page, live_server, boosted
    ):
        page.set_viewport_size(DESKTOP)
        page.goto(f"{live_server.url}/")
        _mark_document(page)

        _layout_link(page).click()
        page.wait_for_url(f"{live_server.url}/layout/")
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
        """The cost of rebinding, and why it is conditional.

        theme-change adds a fresh listener to every control each time it runs.
        Rebinding after a swap that left the controls in place would give each
        one two listeners, and two toggles per click land back on the theme
        they started from — a control that looks alive and does nothing.

        The swap is dispatched directly rather than driven through a page,
        because what matters is the shape of the event, not which view
        produced it.
        """
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
        """A true-positive control for the test above.

        It forces the double-bind the guard exists to prevent — a body-target
        settle on a page where nothing was actually swapped — and asserts the
        toggle then stops working. Without it, a theme control that changed on
        one click under every condition would report a working guard forever.
        """
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
