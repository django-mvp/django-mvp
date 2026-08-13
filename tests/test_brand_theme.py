"""Tests for the packaged brand: the `mvp` and `mvp-dark` themes and the SVG
assets the brand template tags resolve to.

Source: mvp/tailwind/base.css, mvp/static/brand/*.svg, mvp/config.py,
mvp/static/css/django-mvp.css (built artifact).

The subject here is a Tailwind build input, a set of static files and a built
stylesheet, none of which has a Python module behind it — so this module is
declared under `non-mirror-paths` in pyproject.toml for the same reason as
tests/test_frontend_runtime.py.

The contrast assertions are the point of the file. django-mvp asks a developer
to hand over their UI decisions, and a palette that fails WCAG AA on a form
error is the specific way that promise has already been broken once (#136,
against the prebuilt `light` theme). Ratios are computed from the theme source
rather than transcribed from the design document, so a later edit to a hex value
is checked rather than trusted.
"""

import re
from pathlib import Path

import pytest

from mvp.config import MVP_CONFIG

PACKAGE_DIR = Path(__file__).resolve().parent.parent / "mvp"
PRESET = PACKAGE_DIR / "tailwind" / "base.css"
BRAND_DIR = PACKAGE_DIR / "static" / "brand"
BUILT_CSS = PACKAGE_DIR / "static" / "css" / "django-mvp.css"

THEME_NAMES = ("mvp", "mvp-dark")

# WCAG 2.1 body-text floor. Every colour pairing asserted against it below
# carries words somewhere in the component set, so none of them qualifies for
# the looser large-text allowance.
AA_TEXT = 4.5


def _relative_luminance(hex_colour: str) -> float:
    """WCAG relative luminance of an #rrggbb string."""
    channels = []
    for start in (1, 3, 5):
        srgb = int(hex_colour[start : start + 2], 16) / 255
        channels.append(
            srgb / 12.92 if srgb <= 0.04045 else ((srgb + 0.055) / 1.055) ** 2.4
        )
    red, green, blue = channels
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _contrast(foreground: str, background: str) -> float:
    lighter, darker = sorted(
        (_relative_luminance(foreground), _relative_luminance(background)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


def _selectors_for(name: str) -> list[str]:
    """Every `[data-theme=<name>]` selector in the built stylesheet.

    The shipped build is minified, so the attribute value loses its quotes.
    Matching the quoted form alone finds nothing; matching the bare string
    `[data-theme=mvp]` also matches inside `[data-theme=mvp-dark]`. Hence a
    regex with the closing bracket in it rather than a substring count.
    """
    css = BUILT_CSS.read_text(encoding="utf-8")
    return re.findall(rf'\[data-theme=("{name}"|{re.escape(name)})\]', css)


def _theme_properties(name: str) -> dict[str, str]:
    """Custom properties declared in the preset's theme block called *name*.

    Parses each `@plugin "daisyui/theme"` block separately. A whole-file scan
    would let the last block's values overwrite the first, which reads as a
    clean pass over a theme nobody checked.
    """
    source = PRESET.read_text(encoding="utf-8")
    blocks = re.findall(
        r'@plugin\s+"daisyui/theme"\s*\{(.*?)\n\}', source, flags=re.DOTALL
    )
    for block in blocks:
        declared = dict(re.findall(r"^\s*([\w-]+):\s*([^;]+);", block, flags=re.M))
        if declared.get("name", "").strip('"') == name:
            return {k: v.strip() for k, v in declared.items()}
    raise AssertionError(f"the preset declares no theme named {name!r}")


@pytest.fixture(scope="module", params=THEME_NAMES)
def theme(request):
    return request.param, _theme_properties(request.param)


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


class TestPackagedThemesAreDeclared:
    """Both themes exist where every build can see them."""

    @pytest.mark.parametrize("name", THEME_NAMES)
    def test_declared_in_the_shared_preset_not_this_repo_s_entry(self, name):
        """A theme declared only in assets/tailwind.css would ship in the
        prebuilt stylesheet and be missing from every consumer's own build."""
        assert _theme_properties(name)["name"].strip('"') == name

    @pytest.mark.parametrize("name", THEME_NAMES)
    def test_defined_exactly_once_in_the_built_stylesheet(self, name):
        """Two blocks for one name is correct-by-emission-order, which is a
        thing that quietly stops being true when an import moves."""
        assert len(_selectors_for(name)) == 1

    @pytest.mark.parametrize("prebuilt", ["light", "dark", "dracula", "synthwave"])
    def test_no_prebuilt_theme_was_replaced(self, prebuilt):
        """The package adds its themes; it does not curate DaisyUI's set
        (docs/adr/0010-every-prebuilt-theme-ships-in-the-package.md)."""
        assert _selectors_for(prebuilt)


class TestPackagedThemeContrast:
    """Every pairing that carries text clears WCAG AA in both themes."""

    def test_body_text_on_the_page(self, theme):
        name, props = theme
        ratio = _contrast(props["--color-base-content"], props["--color-base-100"])

        assert ratio >= AA_TEXT, f"{name}: base-content on base-100 is {ratio:.2f}:1"

    @pytest.mark.parametrize(
        "role", ["primary", "secondary", "accent", "neutral", "info", "success", "warning", "error"]
    )
    def test_content_colour_on_its_own_fill(self, theme, role):
        """What a filled button, badge or alert renders as."""
        name, props = theme
        ratio = _contrast(props[f"--color-{role}-content"], props[f"--color-{role}"])

        assert ratio >= AA_TEXT, f"{name}: {role}-content on {role} is {ratio:.2f}:1"

    @pytest.mark.parametrize("role", ["primary", "accent", "info", "success", "warning", "error"])
    def test_role_colour_as_text_on_the_page(self, theme, role):
        """What `text-error` on a form field renders as — the shape of #136.

        A role colour is a foreground as well as a fill: DaisyUI emits
        `text-<role>` and `link-<role>` utilities from the same variable, and
        the packaged form field uses `text-error` for a validation message.
        """
        name, props = theme
        ratio = _contrast(props[f"--color-{role}"], props["--color-base-100"])

        assert ratio >= AA_TEXT, (
            f"{name}: text-{role} on base-100 is {ratio:.2f}:1 — this is the "
            "pairing a form validation message is rendered in"
        )

    def test_muted_text_on_the_page(self, theme):
        """`secondary` is the muted role, so it is held to the same floor as
        anything else carrying words rather than to the large-text one."""
        name, props = theme
        ratio = _contrast(props["--color-secondary"], props["--color-base-100"])

        assert ratio >= AA_TEXT, f"{name}: secondary on base-100 is {ratio:.2f}:1"

    def test_borders_and_dividers_are_perceivable(self, theme):
        """base-300 draws borders, dividers and table rules against the page.

        Deliberately not the 3:1 user-interface floor. That floor is for a
        control's boundary, where the boundary is what tells you the control is
        there; these are separators between two surfaces, and a palette built on
        restraint would have to shout to clear 3:1. What is worth catching is a
        separator that has become invisible, so the floor here is low and its
        only job is to fail when the two colours have converged.
        """
        name, props = theme
        ratio = _contrast(props["--color-base-300"], props["--color-base-100"])

        assert ratio >= 1.3, (
            f"{name}: base-300 against base-100 is {ratio:.2f}:1, so a border "
            "drawn in it is invisible against the page"
        )

    def test_the_contrast_helper_rejects_a_failing_pair(self):
        """The gate above is only worth having if it can fail.

        Grey on white at 2.3:1 is roughly what the prebuilt `light` theme
        rendered a form error at, which is the defect this file exists to keep
        out. Asserting the helper flags it proves the floor is doing work.
        """
        assert _contrast("#8a8a8a", "#ffffff") < AA_TEXT
        assert _contrast("#000000", "#ffffff") == pytest.approx(21.0, abs=0.01)


class TestPackagedThemeIsTheDefault:
    """Zero configuration renders the brand, and the toggle stays on it."""

    def test_default_theme_is_the_packaged_light_one(self):
        assert MVP_CONFIG["theme"]["default"] == "mvp"

    def test_toggle_partner_is_the_packaged_dark_one(self):
        assert MVP_CONFIG["theme"]["dark"] == "mvp-dark"

    def test_shape_tokens_are_identical_in_both_themes(self, theme):
        """Switching theme changes colour, never geometry. A radius that moves
        with the toggle reads as the layout shifting rather than the palette."""
        _, props = theme
        shape = {
            "--radius-selector": "0.25rem",
            "--radius-field": "0.25rem",
            "--radius-box": "0.5rem",
            "--border": "1px",
            "--depth": "0",
            "--noise": "0",
        }

        assert {key: props[key] for key in shape} == shape
