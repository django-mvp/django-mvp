"""Tests for LayoutConfig, the layout resolver (mvp/layout.py).

Normalisation — what "never"/"none" mean, and what an unrecognised
breakpoint name falls back to — lives in this one class and nowhere else.
These tests pin that behaviour directly against the class, independent of
any template tag that reads it.
"""

import re

import pytest

from mvp.layout import LayoutConfig
from tests.conftest import requires_browser
from tests.factories import ProductFactory


class TestLayoutConfigBreakpoint:
    @pytest.mark.parametrize(
        ("bp", "px"),
        [
            ("sm", 640),
            ("md", 768),
            ("lg", 1024),
            ("xl", 1280),
            ("2xl", 1536),
        ],
    )
    def test_supported_breakpoints_resolve_their_own_width(self, bp, px):
        config = LayoutConfig(bp, "offcanvas", True, False)
        assert config.breakpoint == bp
        assert config.breakpoint_px == px
        assert config.persistent is True

    @pytest.mark.parametrize(
        "value", ["never", "NEVER", "Never", "none", "NONE", "None"]
    )
    def test_never_and_none_in_any_case_disable_the_persistent_sidebar(self, value):
        config = LayoutConfig(value, "offcanvas", True, False)
        assert config.breakpoint == "never"
        assert config.persistent is False
        assert config.breakpoint_px is None

    def test_an_unrecognised_breakpoint_falls_back_to_lg(self):
        config = LayoutConfig("bogus", "offcanvas", True, False)
        assert config.breakpoint == "lg"
        assert config.breakpoint_px == 1024
        assert config.persistent is True

    def test_a_missing_breakpoint_falls_back_to_lg(self):
        config = LayoutConfig(None, "offcanvas", True, False)
        assert config.breakpoint == "lg"
        assert config.breakpoint_px == 1024


class TestLayoutConfigAsDict:
    def test_as_dict_carries_exactly_the_documented_keys(self):
        config = LayoutConfig("md", "icons", False, True)
        assert config.as_dict() == {
            "sidebar": {
                "breakpoint": "md",
                "persistent": True,
                "breakpointPx": 768,
                "collapse": "icons",
                "boost": True,
            },
            "header": {
                "sticky": False,
            },
        }

    def test_as_dict_reflects_a_disabled_breakpoint(self):
        config = LayoutConfig("never", "offcanvas", True, False)
        assert config.as_dict() == {
            "sidebar": {
                "breakpoint": "never",
                "persistent": False,
                "breakpointPx": None,
                "collapse": "offcanvas",
                "boost": False,
            },
            "header": {
                "sticky": True,
            },
        }


PRINT_PAGE = "/layout/store/"

PRINT_WIDTHS = {"desktop": 1440, "a4": 794}

TABLE_PAGE = "/django-tables2/"
BARE_TABLE_PAGE = "/django-tables2/bare/"
MAP_PAGE = "/layout/full-page/"

at_every_print_width = pytest.mark.parametrize("width", PRINT_WIDTHS.values(), ids=list(PRINT_WIDTHS))


def _printed(page, url, width):
    """Load a page on screen, switch to print and report what was computed."""
    page.set_viewport_size({"width": width, "height": 900})
    page.goto(url)
    page.emulate_media(media="print")
    return page.evaluate("""
        () => {
          const shown = sel => {
            const el = document.querySelector(sel);
            return el ? el.checkVisibility() : false;
          };
          const main = document.querySelector('main').getBoundingClientRect();
          return {
            sidebar: shown('.mvp-sidebar'),
            dock: shown('.dock'),
            mainLeft: Math.round(main.left),
            mainWidth: Math.round(main.width),
            pageWidth: document.documentElement.clientWidth,
          };
        }
    """)


def _sheets(page, url, width):
    """Load a page on screen, print it to A4 and count the sheets."""
    page.set_viewport_size({"width": width, "height": 900})
    page.goto(url)
    return len(re.findall(rb"/Type\s*/Page\b", page.pdf(format="A4")))


@pytest.mark.e2e
@requires_browser
class TestPrintingAPage:
    """Paper is narrower than the sidebar breakpoint, and the open state restored
    on a wide window outlives that change, so a desktop window and an A4 width are
    both asserted, each loaded on screen first and only then switched to print."""

    @at_every_print_width
    def test_the_sidebar_and_dock_are_left_off(self, page, live_server, width):
        printed = _printed(page, f"{live_server.url}{PRINT_PAGE}", width)

        assert not printed["sidebar"]
        assert not printed["dock"]

    @at_every_print_width
    def test_the_content_takes_the_whole_page_width(self, page, live_server, width):
        printed = _printed(page, f"{live_server.url}{PRINT_PAGE}", width)

        assert printed["mainLeft"] == 0
        assert printed["mainWidth"] == printed["pageWidth"]

    def test_a_page_opened_wide_is_not_locked_when_it_reaches_paper_width(
        self, page, live_server
    ):
        page.set_viewport_size({"width": 1440, "height": 900})
        page.goto(f"{live_server.url}{PRINT_PAGE}")
        page.emulate_media(media="print")
        page.set_viewport_size({"width": 794, "height": 1123})

        root = page.evaluate("""
            () => {
              const style = getComputedStyle(document.documentElement);
              return {
                toggled: document.querySelector('.drawer-toggle').checked,
                overflow: style.overflow,
                background: style.backgroundColor,
                pageWidth: document.documentElement.clientWidth,
                mainWidth: document.querySelector('main').getBoundingClientRect().width,
              };
            }
        """)

        assert root["toggled"]
        assert root["overflow"] == "visible"
        assert root["background"] == "rgb(255, 255, 255)"
        assert root["mainWidth"] == root["pageWidth"] == 794

    @at_every_print_width
    @pytest.mark.parametrize(
        "path", [TABLE_PAGE, BARE_TABLE_PAGE], ids=["toolbar", "bare"]
    )
    def test_every_row_of_a_table_page_is_in_the_printed_flow(
        self, page, live_server, width, path
    ):
        ProductFactory.create_batch(30)
        page.set_viewport_size({"width": width, "height": 900})
        page.goto(f"{live_server.url}{path}")
        page.emulate_media(media="print")

        printed = page.evaluate("""
            () => {
              const region = document.querySelector('.mvp-table-region');
              const rows = region.querySelectorAll('tbody tr:not(.mvp-table-filler)');
              const last = rows[rows.length - 1].getBoundingClientRect();
              return {
                rows: rows.length,
                hidden: region.scrollHeight - region.clientHeight,
                lastRowBottom: last.bottom + window.scrollY,
                pageBottom: document.documentElement.scrollHeight,
              };
            }
        """)

        assert printed["rows"] >= 25
        assert printed["hidden"] == 0
        assert printed["lastRowBottom"] <= printed["pageBottom"]

    @at_every_print_width
    def test_a_long_table_runs_on_to_more_sheets(self, page, live_server, width):
        ProductFactory.create_batch(60)

        assert _sheets(page, f"{live_server.url}{BARE_TABLE_PAGE}", width) > 1

    @at_every_print_width
    def test_a_filled_page_with_nothing_to_flow_prints_at_its_bounded_height(
        self, page, live_server, width
    ):
        assert _sheets(page, f"{live_server.url}{MAP_PAGE}", width) == 1

        page.emulate_media(media="print")
        assert (
            page.evaluate(
                "document.querySelector('#map').getBoundingClientRect().height"
            )
            > 0
        )

    def test_a_dark_theme_prints_dark_text_on_white(self, page, live_server):
        page.goto(f"{live_server.url}{PRINT_PAGE}")
        page.evaluate("document.documentElement.setAttribute('data-theme', 'dark')")
        page.emulate_media(media="print")

        colours = page.evaluate("""
            () => ({
              page: getComputedStyle(document.documentElement).backgroundColor,
              text: getComputedStyle(document.querySelector('main')).color,
            })
        """)

        assert colours == {"page": "rgb(255, 255, 255)", "text": "rgb(0, 0, 0)"}
