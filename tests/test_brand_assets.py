"""Tests for what the package ships under its own name: the brand SVGs the
template tags resolve to, and the absence of a theme carrying that brand.

Source: mvp/static/brand/*.svg, mvp/config.py, mvp/tailwind/base.css,
mvp/static/css/django-mvp.css (built artifact).

The subject here is a set of static files, a Tailwind build input and a built
stylesheet, none of which has a Python module behind it — so this module is
declared under `non-mirror-paths` in pyproject.toml for the same reason as
tests/test_frontend_runtime.py.

The mark and the palette part company here. A logo is what a project puts on a
page it has not styled yet, so the resolvers keep a default and the files have
to be real. A theme is the whole surface, and one drawn for this package would
be branding a project never chose — so the wheel carries none, and the two that
exist belong to the demo site (tests/test_demo/test_demo_themes.py).
"""

import re
from pathlib import Path

import pytest

from mvp.config import MVP_CONFIG

PACKAGE_DIR = Path(__file__).resolve().parent.parent / "mvp"
PRESET = PACKAGE_DIR / "tailwind" / "base.css"
BRAND_DIR = PACKAGE_DIR / "static" / "brand"
BUILT_CSS = PACKAGE_DIR / "static" / "css" / "django-mvp.css"

BRANDED_THEMES = ("mvp", "mvp-dark")


def _selectors_for(name: str) -> list[str]:
    """Every `[data-theme=<name>]` selector in the built stylesheet.

    The shipped build is minified, so the attribute value loses its quotes.
    Matching the quoted form alone finds nothing; matching the bare string
    `[data-theme=mvp]` also matches inside `[data-theme=mvp-dark]`. Hence a
    regex with the closing bracket in it rather than a substring count.
    """
    css = BUILT_CSS.read_text(encoding="utf-8")
    return re.findall(rf'\[data-theme=("{name}"|{re.escape(name)})\]', css)


class TestBrandAssets:
    """The four SVGs mvp.utils' default resolvers name."""

    @pytest.mark.parametrize(
        "filename", ["logo.svg", "logo_dark.svg", "icon.svg", "icon_dark.svg"]
    )
    def test_asset_is_present_and_is_an_svg(self, filename):
        asset = BRAND_DIR / filename

        assert asset.is_file(), (
            f"mvp/utils.py's default resolver returns brand/{filename}; a missing "
            "file makes the zero-config case a broken image"
        )
        assert asset.read_text(encoding="utf-8").lstrip().startswith("<svg")

    @pytest.mark.parametrize("pair", [("logo.svg", "logo_dark.svg"), ("icon.svg", "icon_dark.svg")])
    def test_dark_variant_is_not_a_copy_of_the_light_one(self, pair):
        """A dark asset equal to its light sibling is the silent failure here.

        Nothing errors, the resolver returns a URL, and the mark is invisible on
        a dark page. Same file sizes are expected — the two differ only in hex
        fills — so size is no signal and the bytes have to be compared.
        """
        light, dark = (BRAND_DIR / name for name in pair)

        assert light.read_bytes() != dark.read_bytes()

    def test_assets_carry_no_font_dependency(self):
        """The wordmark ships as outlines: a `font-family` would render it in
        whatever the viewer happens to have, which is not the wordmark."""
        for asset in BRAND_DIR.glob("*.svg"):
            assert "font-family" not in asset.read_text(encoding="utf-8"), (
                f"{asset.name} references a font, so it renders differently "
                "on a machine without that font installed"
            )


class TestNoBrandedThemeIsDistributed:
    """The wheel carries no palette of this package's own.

    Both files matter and they fail differently. The preset is imported by every
    consumer build generated with `mvp_tailwind`, so a theme block left there
    reaches a project that never ran this repo's build; the prebuilt stylesheet
    is what a project gets when it runs no build at all. Checking one and not
    the other leaves the branding shipping down the path nobody looked at.
    """

    @pytest.mark.parametrize("name", BRANDED_THEMES)
    def test_the_shared_preset_declares_no_theme(self, name):
        """Both spellings, because either would ship.

        `@plugin "daisyui/theme" { name: "mvp"; ... }` is how the preset
        declared these; a bare `[data-theme="mvp"]` block is the other way to
        write the same output, and docs/theming.md recommends it. Checking only
        the form that was removed would pass a reinstatement written the way the
        documentation teaches.
        """
        source = PRESET.read_text(encoding="utf-8")

        assert f'name: "{name}"' not in source, (
            f"the preset declares a theme called {name!r}, so every consumer "
            "build generated with mvp_tailwind emits this package's branding"
        )
        assert f'[data-theme="{name}"]' not in source, (
            f"the preset defines a block for {name!r}, so every consumer build "
            "generated with mvp_tailwind emits this package's branding"
        )

    @pytest.mark.parametrize("name", BRANDED_THEMES)
    def test_the_prebuilt_stylesheet_defines_no_block(self, name):
        assert _selectors_for(name) == [], (
            f"the shipped stylesheet defines [data-theme={name}], so a project "
            "installing the wheel receives this package's branding"
        )

    @pytest.mark.parametrize("prebuilt", ["light", "dark", "dracula", "synthwave"])
    def test_every_prebuilt_theme_still_ships(self, prebuilt):
        """Removing ours curates nothing of DaisyUI's
        (docs/adr/0010-every-prebuilt-theme-ships-in-the-package.md)."""
        assert _selectors_for(prebuilt)


class TestTheAppliedThemeIsPrebuilt:
    """Zero configuration renders a theme DaisyUI publishes, and so does the
    other half of the toggle — a pair a project replaces together."""

    def test_default_theme_is_prebuilt(self):
        assert MVP_CONFIG["theme"]["default"] == "light"

    def test_toggle_partner_is_prebuilt(self):
        assert MVP_CONFIG["theme"]["dark"] == "dark"

    @pytest.mark.parametrize("key", ["default", "dark"])
    def test_the_configured_pair_is_defined_in_the_shipped_stylesheet(self, key):
        """The names are not validated at runtime (ADR 0011), so a default
        naming a block nothing emits renders as an unstyled fallback and raises
        nothing. That is fine for a project's own theme and not fine for ours."""
        assert _selectors_for(MVP_CONFIG["theme"][key])
