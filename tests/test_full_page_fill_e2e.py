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
ORDINARY_PAGE = "/layout/"

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
          const height = sel => {
            const el = document.querySelector(sel);
            return el ? Math.round(el.getBoundingClientRect().height) : null;
          };
          const style = getComputedStyle(document.querySelector('.drawer-content'));
          return {
            viewport: window.innerHeight,
            documentHeight: document.documentElement.scrollHeight,
            display: style.display,
            flexDirection: style.flexDirection,
            minHeight: style.minHeight,
            drawerContentHeight: height('.drawer-content'),
            mainHeight: height('main'),
            mapHeight: height('#map'),
          };
        }
    """)


class TestFullPageContentFillsTheShell:
    """The feature, on the demo page that exists to demonstrate it."""

    @at_every_viewport
    def test_the_shell_becomes_a_flex_column_with_a_height(
        self, page, live_server, viewport
    ):
        """Both halves of the fix. The flex column is what makes
        <c-app.main>'s flex-1 mean anything; the min-height is the floor it
        grows into where the sidebar is not supplying one."""
        layout = _layout(page, f"{live_server.url}{FILL_PAGE}", viewport)

        assert layout["display"] == "flex"
        assert layout["flexDirection"] == "column"
        assert layout["minHeight"] == f"{layout['viewport']}px"

    @at_every_viewport
    def test_the_container_never_computes_to_zero_height(
        self, page, live_server, viewport
    ):
        """The failure mode issue #247 describes.

        A library that measures its container once at construction renders
        into nothing if that container computes to zero — which is what
        ``h-full`` did before, with no error to show for it. ``#map`` carries
        ``h-full w-full``, so this is the end of the chain being checked, and
        it is CSS only: no CDN and no tile server, so it holds in CI whether
        or not Leaflet itself loaded.
        """
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
        """The point of filling is that the content owns its scrolling, so the
        document must not have grown past the viewport."""
        layout = _layout(page, f"{live_server.url}{FILL_PAGE}", viewport)

        assert layout["documentHeight"] == layout["viewport"]


class TestOrdinaryPagesAreUntouched:
    """The regression question issue #247 asked to have investigated.

    The rule is scoped with ``:has(.mvp-page-fill)``, so a page that does not
    opt in is not merely unchanged in effect — the declarations never apply to
    it at all. That is checkable directly, which is a stronger claim than
    comparing measurements.
    """

    @at_every_viewport
    def test_the_shell_keeps_its_original_layout(self, page, live_server, viewport):
        layout = _layout(page, f"{live_server.url}{ORDINARY_PAGE}", viewport)

        assert layout["display"] == "block"
        assert layout["minHeight"] == "auto"

    @at_every_viewport
    def test_no_scrollbar_is_introduced(self, page, live_server, viewport):
        layout = _layout(page, f"{live_server.url}{ORDINARY_PAGE}", viewport)

        assert layout["documentHeight"] <= layout["viewport"]
