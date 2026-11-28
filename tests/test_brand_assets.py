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

from mvp.config import MVP_CONFIG

PACKAGE_DIR = Path(__file__).resolve().parent.parent / "mvp"
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
    def test_every_asset_the_default_resolver_returns_is_an_svg(self):
        problems = [
            filename
            for filename in ("logo.svg", "logo_dark.svg", "icon.svg", "icon_dark.svg")
            if not (BRAND_DIR / filename).is_file()
            or not (BRAND_DIR / filename)
            .read_text(encoding="utf-8")
            .lstrip()
            .startswith("<svg")
        ]

        assert not problems, (
            f"mvp/utils.py's default resolver returns brand/{problems}, which are "
            "missing or not SVGs, so the zero-config case is a broken image"
        )


class TestNoBrandedThemeIsDistributed:
    def test_the_prebuilt_stylesheet_defines_no_branded_block(self):
        defined = [name for name in BRANDED_THEMES if _selectors_for(name)]

        assert defined == [], (
            f"the shipped stylesheet defines {defined}, so a project installing "
            "the wheel receives this package's branding"
        )


class TestTheAppliedThemeIsPrebuilt:
    def test_the_configured_pair_is_defined_in_the_shipped_stylesheet(self):
        undefined = [
            MVP_CONFIG["theme"][key]
            for key in ("default", "dark")
            if not _selectors_for(MVP_CONFIG["theme"][key])
        ]

        assert undefined == []
