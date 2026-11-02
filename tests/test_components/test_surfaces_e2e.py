"""The three base colours keep one meaning each, read in a real browser (#626, FS-026 US-4, US-8).

Source: mvp/tailwind/base.css, specs/026-ship-prebuilt-daisyui/spec.md, docs/theming.md

base-100 is raised, base-200 is the page and base-300 is sunk. Whether a page
honours that is a question about the cascade and about what the browser paints,
so these read painted colours off a real page on stock themes, with no CSS added
unless a test is about a theme's own block.
"""

import pytest
from playwright.sync_api import expect

from mvp.config import MVP_CONFIG
from tests.conftest import requires_browser
from tests.factories import ProductFactory

pytestmark = [pytest.mark.e2e, requires_browser, pytest.mark.django_db]

WIDE = {"width": 1440, "height": 900}
LAPTOP = {"width": 1100, "height": 800}
PHONE = {"width": 390, "height": 844}

LIST_PAGE = "/products/"
TABLE_PAGE = "/django-tables2/"
PLACEHOLDER_PAGE = "/components/placeholder/"
PREVIEW_PAGE = "/theme/preview/"

STOCK_THEMES = ("light", "dark", "corporate")

GROUND = "rgb(1, 2, 3)"
LINE = "rgb(200, 10, 20)"
INK = "rgb(250, 240, 230)"

# Painted and read back, because a computed colour keeps the notation its theme
# was written in. A translucent colour is laid over `over` first.
PAINTED = """
  window.painted = (colour, over) => {
    const pixel = document.createElement("canvas").getContext("2d");
    pixel.fillStyle = over ?? "#fff";
    pixel.fillRect(0, 0, 1, 1);
    pixel.fillStyle = colour;
    pixel.fillRect(0, 0, 1, 1);
    const [red, green, blue] = pixel.getImageData(0, 0, 1, 1).data;
    return `rgb(${red}, ${green}, ${blue})`;
  };
  window.fill = (selector) => {
    const element = document.querySelector(selector);
    return element && painted(getComputedStyle(element).backgroundColor);
  };
  window.surface = (name) => {
    const probe = document.createElement("div");
    probe.style.backgroundColor = `var(--color-${name})`;
    document.documentElement.append(probe);
    const colour = painted(getComputedStyle(probe).backgroundColor);
    probe.remove();
    return colour;
  };
"""


def _open(page, live_server, path, viewport, theme=None, css=None):
    page.set_viewport_size(viewport)
    page.goto(f"{live_server.url}{path}")
    page.wait_for_load_state("networkidle")
    page.evaluate(PAINTED)
    if theme:
        page.evaluate(
            "theme => { document.documentElement.dataset.theme = theme }", theme
        )
    if css:
        page.add_style_tag(content=css)


def _fill(page, selector):
    return page.evaluate("selector => fill(selector)", selector)


def _surface(page, name):
    return page.evaluate("name => surface(name)", name)


def _append(page, html, parent="main"):
    """Draw ``html`` in ``parent``, as a project's template would."""
    page.evaluate(
        """([parent, html]) => {
          document.querySelector(parent).insertAdjacentHTML("beforeend", html);
        }""",
        [parent, html],
    )


@pytest.fixture
def products(db):
    return ProductFactory.create_batch(3)


@pytest.mark.parametrize("theme", STOCK_THEMES)
class TestAStockThemeWithNoExtraCss:
    def test_each_base_colour_paints_its_own_surface(self, page, live_server, theme):
        _open(page, live_server, PREVIEW_PAGE, WIDE, theme)

        assert _fill(page, "html") == _surface(page, "base-200")
        assert _fill(page, ".mvp-header") == _surface(page, "base-200")
        assert _fill(page, ".mvp-sidebar") == _surface(page, "base-300")
        assert _fill(page, ".mvp-sidebar-header") == _surface(page, "base-300")
        assert _fill(page, ".mvp-sidebar-footer") == _surface(page, "base-300")
        assert _fill(page, "main .card.bg-base-100") == _surface(page, "base-100")

    def test_the_three_surfaces_are_told_apart(self, page, live_server, theme):
        _open(page, live_server, PREVIEW_PAGE, WIDE, theme)

        painted = {
            _surface(page, slot) for slot in ("base-100", "base-200", "base-300")
        }

        assert len(painted) == 3

    def test_the_dock_is_on_the_page(self, page, live_server, theme):
        _open(page, live_server, PREVIEW_PAGE, PHONE, theme)

        assert _fill(page, ".mvp-dock") == _surface(page, "base-200")

    def test_a_default_button_shows_on_every_surface(self, page, live_server, theme):
        _open(page, live_server, PREVIEW_PAGE, WIDE, theme)
        _append(page, '<button id="on-page" class="btn">Default</button>')

        fill = _fill(page, "#on-page")

        assert fill not in {
            _surface(page, "base-100"),
            _surface(page, "base-200"),
            _surface(page, "base-300"),
        }

    def test_a_default_alert_shows_on_the_page(self, page, live_server, theme):
        _open(page, live_server, PREVIEW_PAGE, WIDE, theme)
        _append(page, '<div id="alert" class="alert">Default</div>')

        assert _fill(page, "#alert") not in {
            _surface(page, "base-100"),
            _surface(page, "base-200"),
            _surface(page, "base-300"),
        }

    def test_a_coloured_alert_keeps_its_colour(self, page, live_server, theme):
        _open(page, live_server, PREVIEW_PAGE, WIDE, theme)

        for variant in ("info", "success", "warning", "error"):
            _append(page, f'<div id="{variant}" class="alert alert-{variant}">x</div>')
            assert _fill(page, f"#{variant}") == _surface(page, variant), variant

    def test_a_coloured_button_keeps_its_colour(self, page, live_server, theme):
        _open(page, live_server, PREVIEW_PAGE, WIDE, theme)

        for variant in ("neutral", "primary", "secondary", "accent", "error"):
            _append(
                page, f'<button id="{variant}" class="btn btn-{variant}">x</button>'
            )
            assert _fill(page, f"#{variant}") == _surface(page, variant), variant

    def test_a_ghost_button_keeps_no_fill_at_rest(self, page, live_server, theme):
        _open(page, live_server, PREVIEW_PAGE, WIDE, theme)
        _append(page, '<button id="ghost" class="btn btn-ghost">x</button>')

        background = page.evaluate(
            "getComputedStyle(document.querySelector('#ghost')).backgroundColor"
        )

        assert page.evaluate(
            "colour => painted(colour, '#000') !== painted(colour, '#fff')", background
        )

    def test_the_placeholder_card_shows_on_the_page_and_on_a_card(
        self, page, live_server, theme
    ):
        _open(page, live_server, PLACEHOLDER_PAGE, WIDE, theme)

        fill = _fill(page, "main .card.bg-base-300")

        assert fill == _surface(page, "base-300")
        assert fill not in {_surface(page, "base-100"), _surface(page, "base-200")}

    def test_the_filter_panel_foot_is_the_page_in_a_column(
        self, page, live_server, products, theme
    ):
        _open(page, live_server, LIST_PAGE, WIDE, theme)

        assert _fill(page, ".mvp-filter-panel-foot") == _surface(page, "base-200")

    def test_the_filter_panel_foot_is_raised_in_a_drawer(
        self, page, live_server, products, theme
    ):
        _open(page, live_server, LIST_PAGE, LAPTOP, theme)
        page.locator(".mvp-page-side-toggle").first.click()
        expect(page.locator(".mvp-page-side-panel")).to_be_visible()

        assert _fill(page, ".mvp-page-side-panel") == _surface(page, "base-100")
        assert _fill(page, ".mvp-filter-panel-foot") == _surface(page, "base-100")

    def test_a_foot_in_a_stacked_panel_is_the_page(self, page, live_server, theme):
        _open(page, live_server, "/layout/side/?collapse=stack", PHONE, theme)
        _append(
            page,
            '<div class="mvp-filter-panel-foot bg-inherit">x</div>',
            ".mvp-page-side-panel",
        )

        assert _fill(page, ".mvp-filter-panel-foot") == _surface(page, "base-200")

    def test_a_table_page_is_on_the_page(self, page, live_server, products, theme):
        _open(page, live_server, TABLE_PAGE, WIDE, theme)

        page_colour = _surface(page, "base-200")

        assert _fill(page, ".mvp-table-toolbar") == page_colour
        assert _fill(page, ".mvp-table-region thead tr") == page_colour

    def test_a_dropdown_and_a_modal_are_raised(self, page, live_server, theme):
        _open(page, live_server, PREVIEW_PAGE, WIDE, theme)
        _append(
            page,
            '<dialog id="raised" class="modal" open><div class="modal-box">x</div></dialog>',
        )
        _append(
            page,
            '<div class="dropdown"><div id="panel" class="dropdown-content bg-base-100">x</div></div>',
        )

        assert _fill(page, "#raised .modal-box") == _surface(page, "base-100")
        assert _fill(page, "#panel") == _surface(page, "base-100")


class TestTheRail:
    def test_a_group_fly_out_is_raised(self, page, live_server, settings, monkeypatch):
        monkeypatch.setitem(MVP_CONFIG["layout"]["sidebar"], "collapse", "icons")
        _open(page, live_server, PREVIEW_PAGE, WIDE, "light")
        page.evaluate("document.querySelector('.drawer-toggle').checked = false")

        colour = page.evaluate(
            """() => {
              const list = document.querySelector(".mvp-sidebar details > ul");
              return painted(getComputedStyle(list).backgroundColor);
            }"""
        )

        assert colour == _surface(page, "base-100")


class TestAThemeOptsOut:
    def test_root_bg_moves_the_page_and_all_that_follows_it(
        self, page, live_server, products
    ):
        _open(
            page,
            live_server,
            LIST_PAGE,
            WIDE,
            "light",
            f"[data-theme] {{ --root-bg: {GROUND}; }}",
        )

        assert _fill(page, "html") == GROUND
        assert _fill(page, ".mvp-header") == GROUND
        assert _fill(page, ".mvp-filter-panel-foot") == GROUND

    def test_the_page_goes_back_on_base_100(self, page, live_server):
        _open(
            page,
            live_server,
            PREVIEW_PAGE,
            WIDE,
            "light",
            "[data-theme] { --root-bg: var(--color-base-100); }",
        )

        assert _fill(page, "html") == _surface(page, "base-100")


class TestAThemesLine:
    def test_it_is_worked_out_from_base_300_when_unset(self, page, live_server):
        _open(
            page,
            live_server,
            PREVIEW_PAGE,
            WIDE,
            "light",
            """[data-theme] {
              --color-base-300: rgb(200, 200, 200);
              --color-base-content: rgb(0, 0, 0);
            }""",
        )
        _append(page, '<button id="on-page" class="btn">x</button>')

        red = page.evaluate("fill('#on-page').match(/\\d+/)[0]")

        # 85% of the way from the text to base-300, in oklab.
        assert 150 < int(red) < 200

    def test_a_theme_sets_it_for_every_reader(self, page, live_server):
        _open(
            page,
            live_server,
            PREVIEW_PAGE,
            WIDE,
            "light",
            f"[data-theme] {{ --color-line: {LINE}; }}",
        )
        _append(page, '<button id="on-page" class="btn">x</button>')
        _append(page, '<hr id="rule" class="border-line">')

        assert _fill(page, "#on-page") == LINE
        assert (
            page.evaluate(
                "painted(getComputedStyle(document.querySelector('#rule')).borderTopColor)"
            )
            == LINE
        )
        assert (
            page.evaluate(
                "painted(getComputedStyle(document.querySelector('.mvp-sidebar')).borderInlineEndColor)"
            )
            == LINE
        )

    def test_a_part_of_the_page_in_another_theme_drops_it(self, page, live_server):
        _open(
            page,
            live_server,
            PREVIEW_PAGE,
            WIDE,
            "light",
            f'[data-theme="light"] {{ --color-line: {LINE}; }}',
        )
        _append(
            page,
            '<div data-theme="dark"><button id="inside" class="btn">x</button></div>',
        )

        assert _fill(page, "#inside") != LINE

    def test_a_region_with_its_own_surfaces_gets_its_own_line(self, page, live_server):
        """A dark sidebar on a light page must not draw the page's pale button."""
        _open(page, live_server, PREVIEW_PAGE, WIDE, "light")
        _append(page, '<button id="on-page" class="btn">x</button>')
        pale = _fill(page, "#on-page")
        page.add_style_tag(
            content=f"""[data-theme] .mvp-sidebar {{
              --color-base-300: {GROUND};
              --color-base-content: {INK};
            }}"""
        )
        _append(page, '<button id="in-region" class="btn">x</button>', ".mvp-sidebar")

        assert _fill(page, ".mvp-sidebar") == GROUND
        assert _fill(page, "#in-region") != pale
