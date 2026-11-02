"""Which brand image shows, in a real browser.

The theme is applied in the browser and a theme's light or dark scheme lives
in its stylesheet, so rendered markup can't show which image stays visible.
These apply a theme and read the visible images back.
"""

import re

import pytest
from playwright.sync_api import expect

from mvp.config import MVP_CONFIG
from tests.conftest import requires_browser

pytestmark = [pytest.mark.e2e, requires_browser]

DESKTOP = {"width": 1280, "height": 800}

LIGHT_IMAGE = "/static/brand/icon.svg"
DARK_IMAGE = "/static/brand/icon_dark.svg"

def single_asset(request, height, theme):
    return LIGHT_IMAGE


# (theme, image), all of them DaisyUI's own. dracula and cupcake are outside
# the configured pair, one of each scheme.
THEMES = [
    ("light", LIGHT_IMAGE),
    ("dark", DARK_IMAGE),
    ("dracula", DARK_IMAGE),
    ("cupcake", LIGHT_IMAGE),
]


def visible_brand_images(page):
    return page.evaluate(
        """() => [...document.querySelectorAll('.mvp-sidebar-brand img')]
            .filter((image) => getComputedStyle(image).display !== 'none')
            .map((image) => new URL(image.src).pathname)"""
    )


def open_home(page, live_server, theme):
    page.set_viewport_size(DESKTOP)
    page.add_init_script(f"localStorage.setItem('theme', '{theme}')")
    page.goto(f"{live_server.url}/")


class TestBrandImageFollowsTheScheme:
    @pytest.mark.parametrize(("theme", "image"), THEMES)
    def test_one_image_shows_under_every_theme(self, page, live_server, theme, image):
        open_home(page, live_server, theme)

        assert visible_brand_images(page) == [image]

    @pytest.mark.parametrize(("theme", "image"), THEMES)
    def test_changing_theme_swaps_the_image(self, page, live_server, theme, image):
        start = "dark" if image == LIGHT_IMAGE else "light"
        open_home(page, live_server, start)

        page.evaluate(
            "(theme) => document.documentElement.setAttribute('data-theme', theme)",
            theme,
        )

        page.wait_for_function(
            "(image) => [...document.querySelectorAll('.mvp-sidebar-brand img')]"
            ".some((el) => getComputedStyle(el).display !== 'none'"
            " && new URL(el.src).pathname === image)",
            arg=image,
        )
        assert visible_brand_images(page) == [image]

    def test_a_dark_default_theme_shows_the_dark_image(
        self, page, live_server, monkeypatch
    ):
        monkeypatch.setitem(MVP_CONFIG["theme"], "default", "dracula")
        monkeypatch.setitem(MVP_CONFIG["theme"], "dark", "black")
        page.set_viewport_size(DESKTOP)

        page.goto(f"{live_server.url}/")

        assert visible_brand_images(page) == [DARK_IMAGE]

    def test_a_theme_that_names_no_scheme_shows_the_light_image(self, page, live_server):
        open_home(page, live_server, "no-such-theme")

        assert visible_brand_images(page) == [LIGHT_IMAGE]

    def test_a_project_with_no_dark_asset_shows_its_one_image(
        self, page, live_server, monkeypatch
    ):
        monkeypatch.setitem(
            MVP_CONFIG["brand"],
            "icon_resolver",
            "tests.test_components.test_brand_logo_e2e.single_asset",
        )

        open_home(page, live_server, "dark")

        assert visible_brand_images(page) == [LIGHT_IMAGE]


class TestTheVisibleImageHasAName:
    """The hidden image leaves the accessibility tree, so its name can't help."""

    @pytest.mark.parametrize(("theme", "image"), THEMES)
    def test_the_sidebar_icon(self, page, live_server, theme, image):
        open_home(page, live_server, theme)

        images = page.locator(".mvp-sidebar-brand").get_by_role("img")

        expect(images).to_have_count(1)
        expect(images).to_have_attribute("src", re.compile(re.escape(image)))
        expect(images).to_have_accessible_name(re.compile(r"\S"))

    @pytest.mark.parametrize("theme", ["light", "dark"])
    def test_the_error_page_logo(self, page, live_server, theme):
        page.add_init_script(f"localStorage.setItem('theme', '{theme}')")
        page.goto(f"{live_server.url}/errors/404/")

        images = page.get_by_role("img")

        expect(images).to_have_count(1)
        expect(images).to_have_accessible_name(re.compile(r"\S"))
