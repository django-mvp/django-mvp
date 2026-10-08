"""A theme colours the header, the dock and the sidebar (#515, FS-026 US-4).

Each region paints itself from daisyUI's theme properties, so a theme recolours
one by giving those properties other values inside it. Whether that works is a
question about the cascade: which rule wins on the region, and what the
components drawn inside it resolve their colours to. A rendered-HTML test can
only say which classes are present, so these run in a browser and read computed
styles.

The colours are arbitrary values no shipped theme uses. A test passes only if
the value it wrote arrived where the contract says it should.
"""

import pytest

from mvp.config import MVP_CONFIG
from tests.conftest import requires_browser

pytestmark = [pytest.mark.e2e, requires_browser]

DESKTOP = {"width": 1280, "height": 800}
MOBILE = {"width": 390, "height": 844}

GROUND = "rgb(1, 2, 3)"
INK = "rgb(250, 240, 230)"


def _open(page, live_server, viewport, theme_css):
    """Load the home page with ``theme_css`` added as a project stylesheet would be."""
    page.set_viewport_size(viewport)
    page.goto(live_server.url)
    page.add_style_tag(content=theme_css)


def _computed(page, selector, prop):
    return page.evaluate(
        """([selector, prop]) => {
          const el = document.querySelector(selector);
          return el ? getComputedStyle(el)[prop] : null;
        }""",
        [selector, prop],
    )


@pytest.mark.django_db
class TestTheHeaderAndDockFollowThePage:
    def test_the_header_takes_the_pages_background(self, page, live_server):
        _open(page, live_server, DESKTOP, f"[data-theme] {{ --root-bg: {GROUND}; }}")

        assert _computed(page, "html", "backgroundColor") == GROUND
        assert _computed(page, ".mvp-header", "backgroundColor") == GROUND

    def test_the_dock_takes_the_pages_background(self, page, live_server):
        _open(page, live_server, MOBILE, f"[data-theme] {{ --root-bg: {GROUND}; }}")

        assert _computed(page, ".mvp-dock", "backgroundColor") == GROUND


@pytest.mark.django_db
class TestAThemeColoursOneRegion:
    def test_the_header_alone_takes_a_colour_set_inside_it(self, page, live_server):
        _open(
            page,
            live_server,
            DESKTOP,
            f"[data-theme] .mvp-header {{ --root-bg: {GROUND}; }}",
        )

        assert _computed(page, ".mvp-header", "backgroundColor") == GROUND
        assert _computed(page, "html", "backgroundColor") != GROUND

    def test_text_and_ghost_buttons_in_the_header_take_its_text_colour(
        self, page, live_server
    ):
        _open(
            page,
            live_server,
            DESKTOP,
            f"[data-theme] .mvp-header {{ --color-base-content: {INK}; }}",
        )

        assert _computed(page, ".mvp-header", "color") == INK
        assert _computed(page, ".mvp-header .btn-ghost", "color") == INK
        assert _computed(page, "main", "color") != INK

    def test_the_dock_alone_takes_a_colour_set_inside_it(self, page, live_server):
        _open(
            page,
            live_server,
            MOBILE,
            f"[data-theme] .mvp-dock {{ --root-bg: {GROUND};"
            f" --color-base-content: {INK}; }}",
        )

        assert _computed(page, ".mvp-dock", "backgroundColor") == GROUND
        assert _computed(page, ".mvp-dock", "color") == INK

    def test_the_whole_sidebar_takes_a_colour_set_inside_it(self, page, live_server):
        _open(
            page,
            live_server,
            DESKTOP,
            f"[data-theme] .mvp-sidebar {{ --color-base-200: {GROUND};"
            f" --color-base-content: {INK}; }}",
        )

        for part in (".mvp-sidebar", ".mvp-sidebar-header", ".mvp-sidebar-footer"):
            assert _computed(page, part, "backgroundColor") == GROUND, part
        assert _computed(page, ".mvp-sidebar", "color") == INK
        assert _computed(page, ".mvp-sidebar .menu a:not(.menu-active)", "color") == INK


@pytest.mark.django_db
class TestAPanelOpenedFromARegion:
    def test_a_dropdown_panel_is_drawn_in_the_surface_and_text_pair(
        self, page, live_server, monkeypatch
    ):
        """A panel's text is read from the same place as its base-100 surface, so
        a region that re-sets the pair gets a panel drawn in it."""
        # With choices set, the header's theme control is a dropdown.
        monkeypatch.setitem(MVP_CONFIG["theme"], "choices", ["light", "dark"])
        _open(
            page,
            live_server,
            DESKTOP,
            f"[data-theme] .mvp-header {{ --color-base-100: {GROUND};"
            f" --color-base-content: {INK}; }}",
        )

        panel = ".mvp-header .dropdown-content"
        assert _computed(page, panel, "backgroundColor") == GROUND
        assert _computed(page, panel, "color") == INK
