"""Full-page content fills the app shell, in a real browser (issue #247).

A rendered-HTML test can only assert which classes are on which element. The
claim this feature makes is about *computed layout* — that a page's content is
given the shell's height and the window stops scrolling — and only a browser
can settle that.

Every case runs at both viewports, and that is the point rather than a detail.
The two sizes fail for different reasons and an earlier version of this feature
worked at one and silently broke at the other: at desktop widths
``.drawer-side`` is ``100dvh`` and shares grid row 1, so ``.drawer-content``
stretches to match it and inherits a height for free. Below the sidebar
breakpoint ``.drawer-side`` is ``position: fixed``, out of flow, and
contributes nothing — so the same page rendered its content into zero height.
Anything asserted at one size here is asserted at the other.
"""

import pytest

from tests.conftest import requires_browser

pytestmark = [pytest.mark.e2e, requires_browser]

FILL_PAGE = "/layout/full-page/"
ORDINARY_PAGE = "/layout/store/"

VIEWPORTS = {
    "desktop": {"width": 1440, "height": 900},
    "mobile": {"width": 390, "height": 844},
}

# Both sizes, by name, so a failure report says which one broke.
at_every_viewport = pytest.mark.parametrize(
    "viewport", VIEWPORTS.values(), ids=list(VIEWPORTS)
)


def _layout(page, url, viewport):
    """Load a page at a viewport and report what the browser computed."""
    page.set_viewport_size(viewport)
    page.goto(url)
    return page.evaluate("""
        () => {
          const box = sel => {
            const el = document.querySelector(sel);
            if (!el) return null;
            const rect = el.getBoundingClientRect();
            return {
              top: Math.round(rect.top),
              bottom: Math.round(rect.bottom),
              height: Math.round(rect.height),
            };
          };
          const height = sel => (box(sel) || {}).height ?? null;
          const style = getComputedStyle(document.querySelector('.drawer-content'));
          const dock = document.querySelector('.dock');
          return {
            viewport: window.innerHeight,
            documentHeight: document.documentElement.scrollHeight,
            display: style.display,
            flexDirection: style.flexDirection,
            minHeight: style.minHeight,
            drawerContentHeight: height('.drawer-content'),
            mainHeight: height('main'),
            mapHeight: height('#map'),
            map: box('#map'),
            dock: box('.dock'),
            dockPosition: dock ? getComputedStyle(dock).position : null,
            // Not offsetParent: that is null for any position:fixed element,
            // so it reports the fixed dock we are comparing against as absent.
            dockIsVisible: dock ? dock.checkVisibility() : false,
            footerCount: document.querySelectorAll('footer').length,
          };
        }
    """)


class TestFullPageContentFillsTheShell:
    @at_every_viewport
    def test_the_shell_becomes_a_flex_column_with_a_height(
        self, page, live_server, viewport
    ):
        layout = _layout(page, f"{live_server.url}{FILL_PAGE}", viewport)

        assert layout["display"] == "flex"
        assert layout["flexDirection"] == "column"
        assert layout["minHeight"] == f"{layout['viewport']}px"

    @at_every_viewport
    def test_the_container_never_computes_to_zero_height(
        self, page, live_server, viewport
    ):
        layout = _layout(page, f"{live_server.url}{FILL_PAGE}", viewport)

        assert layout["mapHeight"] > 0, (
            "h-full resolved to zero — the height is not reaching the content"
        )

    @at_every_viewport
    def test_the_map_fills_the_space_below_the_header(
        self, page, live_server, viewport
    ):
        layout = _layout(page, f"{live_server.url}{FILL_PAGE}", viewport)

        # The map gets main's full height, and main is what the header and
        # footer leave behind.
        assert layout["mapHeight"] == layout["mainHeight"]
        assert layout["mapHeight"] > layout["viewport"] * 0.8, (
            f"map is {layout['mapHeight']}px in a {layout['viewport']}px "
            "viewport — the shell's height is not reaching it"
        )

    @at_every_viewport
    def test_the_window_does_not_scroll(self, page, live_server, viewport):
        layout = _layout(page, f"{live_server.url}{FILL_PAGE}", viewport)

        assert layout["documentHeight"] == layout["viewport"]


class TestTheDockJoinsTheColumn:
    def test_the_dock_is_in_the_flow(self, page, live_server):
        layout = _layout(page, f"{live_server.url}{FILL_PAGE}", VIEWPORTS["mobile"])

        assert layout["dockIsVisible"], "no dock rendered — this proves nothing"
        assert layout["dockPosition"] == "relative"

    def test_the_dock_does_not_cover_the_content(self, page, live_server):
        layout = _layout(page, f"{live_server.url}{FILL_PAGE}", VIEWPORTS["mobile"])

        overlap = layout["map"]["bottom"] - layout["dock"]["top"]
        assert overlap <= 0, (
            f"the dock covers the bottom {overlap}px of the map — content "
            "under a fixed dock on a page that cannot scroll is unreachable"
        )

    def test_the_dock_still_reaches_the_bottom_of_the_viewport(self, page, live_server):
        layout = _layout(page, f"{live_server.url}{FILL_PAGE}", VIEWPORTS["mobile"])

        assert layout["dock"]["bottom"] == layout["viewport"]

    def test_an_ordinary_page_keeps_its_fixed_dock(self, page, live_server):
        layout = _layout(page, f"{live_server.url}{ORDINARY_PAGE}", VIEWPORTS["mobile"])

        assert layout["dockIsVisible"]
        assert layout["dockPosition"] == "fixed"


class TestTheDemoPageDropsTheFooter:
    @at_every_viewport
    def test_no_footer_renders(self, page, live_server, viewport):
        layout = _layout(page, f"{live_server.url}{FILL_PAGE}", viewport)

        assert layout["footerCount"] == 0

    @at_every_viewport
    def test_an_ordinary_page_still_has_one(self, page, live_server, viewport):
        layout = _layout(page, f"{live_server.url}{ORDINARY_PAGE}", viewport)

        assert layout["footerCount"] == 1


class TestOrdinaryPagesAreUntouched:
    @at_every_viewport
    def test_the_shell_keeps_its_original_layout(self, page, live_server, viewport):
        layout = _layout(page, f"{live_server.url}{ORDINARY_PAGE}", viewport)

        assert layout["display"] == "block"
        assert layout["minHeight"] == "auto"

    @at_every_viewport
    def test_no_scrollbar_is_introduced(self, page, live_server, viewport):
        layout = _layout(page, f"{live_server.url}{ORDINARY_PAGE}", viewport)

        assert layout["documentHeight"] <= layout["viewport"]
