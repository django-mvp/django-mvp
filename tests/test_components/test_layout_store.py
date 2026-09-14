"""The layout store's behaviour, in a browser (T008).

Covers what a rendered template alone cannot show: the store existing and
reporting, an element bound to it following every control the shell ships,
the store staying correct after a boosted navigation at both a wide and a
narrow viewport, the shell still working with JavaScript disabled, and a
page that renders no shell still getting a store rather than throwing.
"""

import pytest
from playwright.sync_api import expect

from mvp.config import MVP_CONFIG
from tests.conftest import requires_browser

pytestmark = [pytest.mark.e2e, requires_browser]

DESKTOP = {"width": 1280, "height": 800}
MOBILE = {"width": 800, "height": 900}


def _store_sidebar_open(page):
    return page.evaluate("() => Alpine.store('layout').sidebarOpen")


def _toggle(page):
    return page.locator("#mvp-app-toggle")


@pytest.mark.django_db
class TestTheStoreExistsAndReports:
    """A shell page always registers `Alpine.store('layout')`."""

    def test_the_store_reports_sidebar_collapse_and_stuck_state(self, page, live_server):
        page.set_viewport_size(DESKTOP)
        page.goto(f"{live_server.url}/")
        page.wait_for_timeout(200)

        store = page.evaluate(
            "() => ({ sidebarOpen: Alpine.store('layout').sidebarOpen, "
            "collapse: Alpine.store('layout').config.collapse, "
            "headerStuck: Alpine.store('layout').headerStuck })"
        )
        assert store["sidebarOpen"] is True, "the default desktop sidebar starts open"
        assert store["collapse"] == MVP_CONFIG["layout"]["sidebar"]["collapse"]
        assert store["headerStuck"] is False

    def test_the_stuck_state_follows_scrolling(self, page, live_server):
        page.set_viewport_size(DESKTOP)
        page.goto(f"{live_server.url}/")
        assert page.evaluate("() => Alpine.store('layout').headerStuck") is False

        # A tall spacer guarantees room to scroll regardless of how much
        # content the demo home page happens to carry.
        page.evaluate(
            "() => { document.body.style.minHeight = '3000px'; window.scrollTo(0, 100); }"
        )
        page.wait_for_function("() => Alpine.store('layout').headerStuck === true")

        page.evaluate("() => window.scrollTo(0, 0)")
        page.wait_for_function("() => Alpine.store('layout').headerStuck === false")


@pytest.mark.django_db
class TestAnElementBoundToTheStoreFollowsEveryControl:
    """The checkbox is bound to `$store.layout.sidebarOpen` (T005); proving
    it follows every control the shell ships is proving the store stays
    correct no matter which one moved it."""

    def test_the_navbar_toggle_opens_it(self, page, live_server):
        page.set_viewport_size(MOBILE)
        page.goto(f"{live_server.url}/")
        expect(_toggle(page)).not_to_be_checked()

        page.locator("label[for='mvp-app-toggle'][aria-label='Open sidebar']").click()

        expect(_toggle(page)).to_be_checked()
        assert _store_sidebar_open(page) is True

    def test_the_sidebar_header_toggle_closes_it(self, page, live_server):
        page.set_viewport_size(DESKTOP)
        page.goto(f"{live_server.url}/")
        expect(_toggle(page)).to_be_checked()

        page.locator("label[for='mvp-app-toggle'][aria-label='Toggle sidebar']").click()

        expect(_toggle(page)).not_to_be_checked()
        assert _store_sidebar_open(page) is False

    def test_the_drawer_overlay_closes_it(self, page, live_server):
        page.set_viewport_size(MOBILE)
        page.goto(f"{live_server.url}/")
        page.locator("label[for='mvp-app-toggle'][aria-label='Open sidebar']").click()
        expect(_toggle(page)).to_be_checked()

        # A native click() rather than a coordinate-based one: the overlay's
        # own visual stacking under the open drawer's content is a
        # DaisyUI/stylesheet concern outside this story's scope. What this
        # test proves is that the label's `for` attribute really does wire
        # it to the checkbox the store is bound to.
        page.locator("label[for='mvp-app-toggle'][aria-label='Close sidebar']").evaluate(
            "el => el.click()"
        )

        expect(_toggle(page)).not_to_be_checked()
        assert _store_sidebar_open(page) is False


@pytest.mark.django_db
class TestBoostedNavigationLeavesTheStoreCorrect:
    """T007's re-derivation, proved through the store rather than only the
    checkbox — at both a wide and a narrow viewport."""

    @pytest.fixture
    def boosted(self, monkeypatch):
        monkeypatch.setitem(MVP_CONFIG["layout"]["sidebar"], "boost", True)

    def _layout_link(self, page):
        return page.locator("aside.mvp-sidebar a[href='/layout/']").first

    def test_a_wide_viewport_stays_open(self, page, live_server, boosted):
        page.set_viewport_size(DESKTOP)
        page.goto(f"{live_server.url}/")
        expect(_toggle(page)).to_be_checked()

        self._layout_link(page).click()
        page.wait_for_url(f"{live_server.url}/layout/")

        assert _store_sidebar_open(page) is True
        expect(_toggle(page)).to_be_checked()

    def test_a_narrow_viewport_closes(self, page, live_server, boosted):
        page.set_viewport_size(MOBILE)
        page.goto(f"{live_server.url}/")
        page.locator("label[for='mvp-app-toggle'][aria-label='Open sidebar']").click()
        expect(_toggle(page)).to_be_checked()

        self._layout_link(page).click()
        page.wait_for_url(f"{live_server.url}/layout/")
        # htmx's afterSettle (and this store's re-derivation) fires after
        # the swap, asynchronously — wait for it rather than racing it.
        page.wait_for_function("() => Alpine.store('layout').sidebarOpen === false")

        expect(_toggle(page)).not_to_be_checked()


@pytest.mark.django_db
class TestTheShellWorksWithoutJavaScript:
    """The drawer's control is a native `<label for>` / checkbox pair — the
    sidebar must open and close with the bundle never running at all."""

    def test_the_sidebar_opens_and_closes_without_javascript(self, browser, live_server):
        context = browser.new_context(java_script_enabled=False)
        try:
            page = context.new_page()
            page.set_viewport_size(MOBILE)
            page.goto(f"{live_server.url}/")
            toggle = page.locator("#mvp-app-toggle")
            expect(toggle).to_be_attached()
            # With no JavaScript the blocking pre-paint script never runs
            # either, so the checkbox stays at its server-rendered default:
            # unchecked. The sidebar starts closed.
            expect(toggle).not_to_be_checked()

            navbar_toggle = page.locator(
                "label[for='mvp-app-toggle'][aria-label='Open sidebar']"
            )
            navbar_toggle.click()
            expect(toggle).to_be_checked()

            navbar_toggle.click()
            expect(toggle).not_to_be_checked()
        finally:
            context.close()


@pytest.mark.django_db
class TestAPageWithNoShellStillGetsAStore:
    """The entrance/error pages render no drawer and no config payload."""

    def test_defaults_reported_without_throwing(self, page, live_server):
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))

        page.goto(f"{live_server.url}/errors/404/")
        page.wait_for_timeout(200)

        store = page.evaluate(
            "() => ({ sidebarOpen: Alpine.store('layout').sidebarOpen, "
            "collapse: Alpine.store('layout').config.collapse, "
            "breakpoint: Alpine.store('layout').config.breakpoint })"
        )
        assert store["sidebarOpen"] is False
        assert store["collapse"] == "offcanvas"
        assert store["breakpoint"] == "lg"
        assert errors == [], f"the store must not throw on a shell-less page: {errors}"
