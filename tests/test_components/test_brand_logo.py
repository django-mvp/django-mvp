"""The markup of ``<c-mvp.brand.icon>`` and ``<c-mvp.brand.logo>``.

The server can't know the visitor's theme, so a project with a dark asset
gets both images and the browser hides one. Which one stays visible is in
``test_brand_logo_e2e.py``.
"""

import pytest

from mvp.config import MVP_CONFIG

COMPONENTS = [("icon", "icon_resolver"), ("logo", "logo_resolver")]


def two_assets(request, height, theme):
    return f"/{theme}.svg"


def one_asset(request, height, theme):
    return "/only.svg"


def no_dark_answer(request, height, theme):
    return "/only.svg" if theme == "light" else None


def use_resolver(monkeypatch, key, name):
    monkeypatch.setitem(
        MVP_CONFIG["brand"], key, f"tests.test_components.test_brand_logo.{name}"
    )


@pytest.mark.parametrize(("component", "key"), COMPONENTS)
class TestBrandImages:
    def test_a_dark_asset_adds_a_second_image(
        self, component, key, monkeypatch, cotton_render_string_soup
    ):
        use_resolver(monkeypatch, key, "two_assets")

        soup = cotton_render_string_soup(f"<c-mvp.brand.{component} />")
        light, dark = soup.find_all("img")

        assert light["src"] == "/light.svg"
        assert "hide-on-dark-theme" in light["class"]
        assert dark["src"] == "/dark.svg"
        assert "hide-on-light-theme" in dark["class"]

    def test_only_the_first_image_is_announced(
        self, component, key, monkeypatch, cotton_render_string_soup
    ):
        use_resolver(monkeypatch, key, "two_assets")

        soup = cotton_render_string_soup(f"<c-mvp.brand.{component} />")
        light, dark = soup.find_all("img")

        assert light["alt"]
        assert dark["alt"] == ""

    def test_both_images_take_the_callers_attributes(
        self, component, key, monkeypatch, cotton_render_string_soup
    ):
        use_resolver(monkeypatch, key, "two_assets")

        soup = cotton_render_string_soup(
            f'<c-mvp.brand.{component} class="size-9" data-role="mark" />'
        )

        for image in soup.find_all("img"):
            assert "size-9" in image["class"]
            assert image["data-role"] == "mark"

    @pytest.mark.parametrize("resolver", ["one_asset", "no_dark_answer"])
    def test_no_dark_asset_renders_one_image(
        self, component, key, resolver, monkeypatch, cotton_render_string_soup
    ):
        use_resolver(monkeypatch, key, resolver)

        soup = cotton_render_string_soup(f"<c-mvp.brand.{component} />")
        images = soup.find_all("img")

        assert len(images) == 1
        assert images[0]["src"] == "/only.svg"
        assert "hide-on-dark-theme" not in images[0].get("class", [])
