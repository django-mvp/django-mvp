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
    return page.evaluate("() => Alpine.store('mvp').sidebar.open")


def _toggle(page):
    return page.locator("#mvp-app-toggle")


def _wait_for_store(page):
    """Block until the layout store is registered.

    The bundle is deferred and Alpine registers its stores during start(), so a
    page that has finished loading has not necessarily finished booting. A
    fixed sleep would be a flake waiting for a slower machine; this waits for
    the thing the assertion actually needs.
    """
    page.wait_for_function("() => window.Alpine && Alpine.store('mvp')")


@pytest.mark.django_db
class TestTheStoreExistsAndReports:
    """A shell page always registers `Alpine.store('mvp')`."""

    def test_the_store_reports_sidebar_collapse_and_stuck_state(
        self, page, live_server
    ):
        page.set_viewport_size(DESKTOP)
        page.goto(f"{live_server.url}/")
        _wait_for_store(page)

        store = page.evaluate(
            "() => ({ sidebarOpen: Alpine.store('mvp').sidebar.open, "
            "collapse: Alpine.store('mvp').sidebar.collapse, "
            "headerStuck: Alpine.store('mvp').header.stuck })"
        )
        assert store["sidebarOpen"] is True, "the default desktop sidebar starts open"
        assert store["collapse"] == MVP_CONFIG["layout"]["sidebar"]["collapse"]
        assert store["headerStuck"] is False

    def test_the_stuck_state_follows_scrolling(self, page, live_server):
        page.set_viewport_size(DESKTOP)
        page.goto(f"{live_server.url}/")
        _wait_for_store(page)
        assert page.evaluate("() => Alpine.store('mvp').header.stuck") is False

        # A tall spacer guarantees room to scroll regardless of how much
        # content the demo home page happens to carry.
        page.evaluate(
            "() => { document.body.style.minHeight = '3000px'; window.scrollTo(0, 100); }"
        )
        page.wait_for_function("() => Alpine.store('mvp').header.stuck === true")

        page.evaluate("() => window.scrollTo(0, 0)")
        page.wait_for_function("() => Alpine.store('mvp').header.stuck === false")


@pytest.mark.django_db
class TestAnElementBoundToTheStoreFollowsEveryControl:
    """The checkbox is bound to `$store.mvp.sidebar.open` (T005); proving
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
        page.locator(
            "label[for='mvp-app-toggle'][aria-label='Close sidebar']"
        ).evaluate("el => el.click()")

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

    def test_the_header_stuck_state_is_re_derived(self, page, live_server, boosted):
        """The swapped-in page starts at the top, and the header's handler
        only writes on the next scroll — so a stale `true` would outlive the
        navigation and leave the shadow on a page nobody has scrolled."""
        page.set_viewport_size(DESKTOP)
        page.goto(f"{live_server.url}/")
        _wait_for_store(page)
        page.evaluate(
            "() => { document.body.style.minHeight = '3000px'; window.scrollTo(0, 100); }"
        )
        page.wait_for_function("() => Alpine.store('mvp').header.stuck === true")

        self._layout_link(page).click()
        page.wait_for_url(f"{live_server.url}/layout/")
        page.wait_for_function("() => Alpine.store('mvp').header.stuck === false")

    def test_a_narrow_viewport_closes(self, page, live_server, boosted):
        page.set_viewport_size(MOBILE)
        page.goto(f"{live_server.url}/")
        page.locator("label[for='mvp-app-toggle'][aria-label='Open sidebar']").click()
        expect(_toggle(page)).to_be_checked()

        self._layout_link(page).click()
        page.wait_for_url(f"{live_server.url}/layout/")
        # htmx's afterSettle (and this store's re-derivation) fires after
        # the swap, asynchronously — wait for it rather than racing it.
        page.wait_for_function("() => Alpine.store('mvp').sidebar.open === false")

        expect(_toggle(page)).not_to_be_checked()


@pytest.mark.django_db
class TestTheShellWorksWithoutJavaScript:
    """The drawer's control is a native `<label for>` / checkbox pair — the
    sidebar must open and close with the bundle never running at all."""

    def test_the_sidebar_opens_and_closes_without_javascript(
        self, browser, live_server
    ):
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

            page.locator(
                "label[for='mvp-app-toggle'][aria-label='Open sidebar']"
            ).click()
            expect(toggle).to_be_checked()

            # Closing goes through the overlay, not back through the navbar
            # control: at this width an open drawer lays its overlay across the
            # header, so the navbar control is genuinely not the thing a person
            # can reach. Clicking it anyway is a race against the drawer's
            # transition, and it is the race that made this test intermittent.
            # The overlay is the documented way out of an open mobile drawer,
            # and it is a plain label wired to the same checkbox.
            page.locator(
                "label[for='mvp-app-toggle'][aria-label='Close sidebar']"
            ).evaluate("el => el.click()")
            expect(toggle).not_to_be_checked()
        finally:
            context.close()


@pytest.mark.django_db
class TestConfigReportsThePerPageOverride:
    """The store's `sidebar` reflects a per-page breakpoint override rather
    than the project default (T010/T011)."""

    def test_a_page_override_beats_the_project_default(self, page, live_server):
        page.goto(f"{live_server.url}/layout/store/?breakpoint=xl")
        _wait_for_store(page)

        config = page.evaluate("() => ({ ...Alpine.store('mvp').sidebar })")
        assert config["breakpoint"] == "xl"
        assert config["breakpointPx"] == 1280
        assert config["persistent"] is True


@pytest.mark.django_db
class TestTheViewportFlagFollowsTheWindow:
    """`isWide` tracks the resolved breakpoint via `matchMedia`, in both
    directions, without a reload (T010/T011)."""

    def test_isWide_flips_both_directions_across_the_breakpoint(
        self, page, live_server
    ):
        page.set_viewport_size(MOBILE)
        page.goto(f"{live_server.url}/")
        assert page.evaluate("() => Alpine.store('mvp').isWide") is False

        page.set_viewport_size(DESKTOP)
        page.wait_for_function("() => Alpine.store('mvp').isWide === true")

        page.set_viewport_size(MOBILE)
        page.wait_for_function("() => Alpine.store('mvp').isWide === false")


@pytest.mark.django_db
class TestTheNeverPersistentCaseReportsCorrectly:
    """`breakpoint="never"` means no pixel width to report and a viewport
    flag that never goes true, rather than a width that means nothing
    (T010/T011)."""

    def test_never_reports_no_width_and_a_flag_that_stays_false(
        self, page, live_server
    ):
        page.goto(f"{live_server.url}/layout/store/?breakpoint=never")
        _wait_for_store(page)

        config = page.evaluate("() => ({ ...Alpine.store('mvp').sidebar })")
        assert config["persistent"] is False
        assert config["breakpointPx"] is None
        assert page.evaluate("() => Alpine.store('mvp').isWide") is False

        # Widen to a viewport that would make a normally-configured shell
        # report wide, and wait for the browser to agree the resize landed
        # before asserting the flag stayed put. Without that wait the assertion
        # could pass on a resize that had not happened yet, proving nothing.
        page.set_viewport_size(DESKTOP)
        page.wait_for_function("() => window.matchMedia('(min-width: 1024px)').matches")
        assert page.evaluate("() => Alpine.store('mvp').isWide") is False


@pytest.mark.django_db
class TestAPageWithNoShellStillGetsAStore:
    """The entrance/error pages render no drawer and no config payload."""

    def test_defaults_reported_without_throwing(self, page, live_server):
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))

        page.goto(f"{live_server.url}/errors/404/")
        _wait_for_store(page)

        store = page.evaluate("() => ({ ...Alpine.store('mvp').sidebar })")
        assert store["collapse"] == "offcanvas"
        assert store["breakpoint"] == "lg"
        # The reported defaults have to be a state the server could actually
        # produce. `lg` is a persistent breakpoint and carries a width, so a
        # project reading `sidebar.persistent` on a shell-less page gets the
        # same answer the documentation promises rather than a combination
        # LayoutConfig can never return.
        assert store["persistent"] is True
        assert store["breakpointPx"] == 1024

        assert page.evaluate("() => Alpine.store('mvp').sidebar.open") is False
        assert errors == [], f"the store must not throw on a shell-less page: {errors}"

    def test_no_storage_entry_is_seeded_without_a_persistent_drawer(
        self, page, live_server
    ):
        """No drawer means nothing to remember. Writing an entry under a
        persistent drawer's key from a page that has none would leave the
        shell's own state resolved by a page that never rendered it."""
        page.goto(f"{live_server.url}/errors/404/")
        _wait_for_store(page)

        stored = page.evaluate("() => localStorage.getItem('mvp-app-drawer-open')")
        assert stored is None
