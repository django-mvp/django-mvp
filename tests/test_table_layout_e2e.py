"""The table area owns its own scrolling, in a real browser (issue #254).

A rendered-HTML test can only assert which classes are on which element.
The claim this feature makes is about *computed layout and scroll
behaviour* — that the window never scrolls, that the heading and footer
rows stay pinned against the scroll container as it scrolls, and that the
pagination bar stays reachable without scrolling the window — and only a
browser can settle that.

Both viewports run, and that is the point rather than a detail, following
tests/test_full_page_fill_e2e.py: at desktop widths the shell's height
comes from `.drawer-side` sharing the sidebar's grid row, and below the
sidebar breakpoint it comes from the `100dvh` floor instead, since
`.drawer-side` is `position: fixed` there and contributes nothing
(specs/027-table-layout-and-column-styling/research.md R5). A regression
in either mechanism only shows up at the viewport that depends on it.
"""

import pytest

from tests.conftest import requires_browser
from tests.factories import ProductFactory

pytestmark = [pytest.mark.e2e, requires_browser]

TABLE_PAGE = "/django-tables2/"

VIEWPORTS = {
    "desktop": {"width": 1440, "height": 900},
    "mobile": {"width": 390, "height": 844},
}

at_every_viewport = pytest.mark.parametrize(
    "viewport", VIEWPORTS.values(), ids=list(VIEWPORTS)
)

# More than one page (paginate_by=25 on DataTablesView), so the page has
# enough rows to overflow the table area at both viewports and pagination
# has a second page to link to.
PRODUCT_COUNT = 30


def _scroll_and_measure(page, url, viewport):
    """Load the table page, scroll its rows end to end, and report what the
    browser computed."""
    page.set_viewport_size(viewport)
    page.goto(url)
    return page.evaluate("""
        () => {
          const region = document.querySelector('[role="region"]');
          // The row, not the section. DaisyUI pins `thead tr` and `tfoot tr`
          // — the <thead> and <tfoot> boxes themselves stay with the table
          // and travel off-screen with it, so measuring those reports a
          // heading that scrolled away even while the visible one is pinned.
          const thead = region.querySelector('thead tr');
          const tfoot = region.querySelector('tfoot tr');
          const pagination = document.querySelector(
            'nav[aria-label="Navigation page results"]'
          );

          const before = window.scrollY;
          region.scrollTop = region.scrollHeight;

          const regionRect = region.getBoundingClientRect();
          const theadRect = thead.getBoundingClientRect();
          const tfootRect = tfoot ? tfoot.getBoundingClientRect() : null;
          const paginationRect = pagination
            ? pagination.getBoundingClientRect()
            : null;

          return {
            viewportHeight: window.innerHeight,
            documentHeight: document.documentElement.scrollHeight,
            scrollYBefore: before,
            scrollYAfter: window.scrollY,
            regionScrolled: Math.round(region.scrollTop),
            regionTop: Math.round(regionRect.top),
            regionBottom: Math.round(regionRect.bottom),
            theadTop: Math.round(theadRect.top),
            theadBottom: Math.round(theadRect.bottom),
            tfootTop: tfootRect ? Math.round(tfootRect.top) : null,
            tfootBottom: tfootRect ? Math.round(tfootRect.bottom) : null,
            paginationTop: paginationRect ? Math.round(paginationRect.top) : null,
            paginationBottom: paginationRect
              ? Math.round(paginationRect.bottom)
              : null,
          };
        }
    """)


class TestTheTableAreaOwnsItsScrolling:
    """FR-002, FR-003, FR-004, FR-005: the table area scrolls, the window
    does not, and the heading/footer rows stay pinned against it."""

    @pytest.mark.django_db
    @at_every_viewport
    def test_the_window_does_not_scroll(self, page, live_server, viewport):
        ProductFactory.create_batch(PRODUCT_COUNT)
        layout = _scroll_and_measure(
            page, f"{live_server.url}{TABLE_PAGE}", viewport
        )

        assert layout["scrollYBefore"] == 0
        assert layout["scrollYAfter"] == 0
        assert layout["documentHeight"] == layout["viewportHeight"]

    @pytest.mark.django_db
    @at_every_viewport
    def test_the_heading_row_stays_inside_the_table_area_after_scrolling(
        self, page, live_server, viewport
    ):
        ProductFactory.create_batch(PRODUCT_COUNT)
        layout = _scroll_and_measure(
            page, f"{live_server.url}{TABLE_PAGE}", viewport
        )

        # Nothing below this means anything if the rows never moved. An
        # earlier version of the layout let the window scroll instead, so
        # `scrollTop = scrollHeight` was a no-op and every pinning assertion
        # passed against an unscrolled table.
        assert layout["regionScrolled"] > 0, (
            "the table area did not scroll — pinning is untested"
        )
        # Sticky to the container's own top, not merely "somewhere on
        # screen" — a heading that scrolled off with the rows would still
        # be "on screen" by a looser check right up until it wasn't.
        assert layout["theadTop"] == layout["regionTop"]
        assert layout["theadBottom"] <= layout["regionBottom"]

    @pytest.mark.django_db
    @at_every_viewport
    def test_the_footer_row_stays_inside_the_table_area_after_scrolling(
        self, page, live_server, viewport
    ):
        ProductFactory.create_batch(PRODUCT_COUNT)
        layout = _scroll_and_measure(
            page, f"{live_server.url}{TABLE_PAGE}", viewport
        )

        assert layout["regionScrolled"] > 0, (
            "the table area did not scroll — pinning is untested"
        )
        assert layout["tfootBottom"] is not None, (
            "no footer rendered — this proves nothing"
        )
        assert layout["tfootBottom"] == layout["regionBottom"]
        assert layout["tfootTop"] >= layout["regionTop"]

    @pytest.mark.django_db
    @at_every_viewport
    def test_the_scrollbar_spans_the_full_height_of_the_table_area(
        self, page, live_server, viewport
    ):
        """FR-005: the container is what scrolls, top to bottom — not a
        separately-scrolling tbody starting below a static heading."""
        ProductFactory.create_batch(PRODUCT_COUNT)
        layout = _scroll_and_measure(
            page, f"{live_server.url}{TABLE_PAGE}", viewport
        )

        assert layout["regionScrolled"] > 0, (
            "the table area did not scroll — pinning is untested"
        )
        assert layout["regionTop"] == layout["theadTop"]
        assert layout["regionBottom"] == layout["tfootBottom"]


class TestPaginationStaysReachable:
    """FR-008: the pagination bar sits below the table area and is visible
    without scrolling the window, whatever the row's scroll position."""

    @pytest.mark.django_db
    @at_every_viewport
    def test_pagination_controls_are_visible_without_scrolling(
        self, page, live_server, viewport
    ):
        ProductFactory.create_batch(PRODUCT_COUNT)
        layout = _scroll_and_measure(
            page, f"{live_server.url}{TABLE_PAGE}", viewport
        )

        assert layout["paginationTop"] is not None, (
            "no pagination rendered — this proves nothing"
        )
        assert layout["paginationTop"] >= 0
        assert layout["paginationBottom"] <= layout["viewportHeight"]


class TestTheBarsSpanTheTable:
    """FR-006, FR-008: the title bar and the pagination bar are as wide as
    the table, so the actions and the pagination sit at the trailing edge
    rather than bunched against the title and the row count.

    Only a browser settles this. Every wrapper involved carries `w-full`,
    and `w-full` inside a shrink-to-fit parent still comes out the width of
    the content — which is what a <c-toolbar> around either bar produces,
    and what the rendered-HTML tests cannot see.
    """

    @pytest.mark.django_db
    def test_the_title_and_pagination_bars_are_as_wide_as_the_table(
        self, page, live_server
    ):
        ProductFactory.create_batch(PRODUCT_COUNT)
        page.set_viewport_size(VIEWPORTS["desktop"])
        page.goto(f"{live_server.url}{TABLE_PAGE}")
        widths = page.evaluate("""
            () => {
              const w = el => el ? Math.round(el.getBoundingClientRect().width) : null;
              const region = document.querySelector('[role="region"]');
              const title = document.querySelector('.page-title');
              return {
                region: w(region),
                bar: w(title.parentElement),
                title: w(title),
                actions: w(title.lastElementChild),
                actionsRight: Math.round(
                  title.lastElementChild.getBoundingClientRect().right
                ),
                titleRight: Math.round(title.getBoundingClientRect().right),
              };
            }
        """)

        assert widths["region"] > 0
        # The bar spans the table. Its *content* is inset by the bar's own
        # padding, which the table deliberately does not carry: the table
        # reaches the edges of the space the shell gives it so its scrollbar
        # hugs that edge (Sam, 2026-08-17 — padding belongs on the bars, not
        # on the table). So the row is table-width and the content inside it
        # is narrower, rather than the two being equal as they were before
        # the bars gained padding.
        assert widths["bar"] == widths["region"], (
            "the bar is narrower than the table it sits over"
        )
        assert widths["title"] < widths["bar"], (
            "the bar's content is not inset — the padding is missing"
        )
        # And the actions really are at the trailing edge of that bar, not
        # merely inside a bar that happens to be wide.
        assert widths["actionsRight"] == widths["titleRight"]
        assert widths["actions"] < widths["title"]
