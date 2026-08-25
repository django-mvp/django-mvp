"""Contrast gate on the demo site's own two themes, `mvp` and `mvp-dark`.

Source: demo/static/css/themes.css, demo/settings.py, demo/templates/base.html.

These carry django-mvp's branding and are loaded only by the demo, so nothing
here is a claim about the package (docs/adr/0016). It is still worth gating.
The demo is the page a developer judges the package on, and a validation message
they cannot read is the specific way that judgement has already gone badly once
(#136, against the prebuilt `light` theme). Ratios are computed from the CSS
rather than transcribed from a design note, so a later edit to a hex value is
checked rather than trusted.
"""

import re
from pathlib import Path

import pytest

from demo.settings import MVP_CONFIG as DEMO_MVP_CONFIG

# The suite runs under tests.settings, which pins a bare MVP_CONFIG so visual
# tweaks to the demo don't ripple into tests. The demo's own module is therefore
# read directly, as tests/test_demo/test_theme_customization.py already does.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
THEME_CSS = REPO_ROOT / "demo" / "static" / "css" / "themes.css"

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


def _theme_properties(name: str) -> dict[str, str]:
    """Custom properties declared in the block scoped to *name*.

    Parses each `[data-theme=...]` block separately. A whole-file scan would let
    the last block's values overwrite the first, which reads as a clean pass
    over a theme nobody checked.
    """
    source = THEME_CSS.read_text(encoding="utf-8")
    blocks = re.findall(
        r'\[data-theme="([\w-]+)"\]\s*\{(.*?)\n\}', source, flags=re.DOTALL
    )
    for declared_name, block in blocks:
        if declared_name == name:
            found = dict(re.findall(r"^\s*([\w-]+):\s*([^;]+);", block, flags=re.M))
            return {key: value.strip() for key, value in found.items()}
    raise AssertionError(f"{THEME_CSS.name} declares no theme named {name!r}")


@pytest.fixture(scope="module", params=THEME_NAMES)
def theme(request):
    return request.param, _theme_properties(request.param)


class TestDemoThemesAreWiredUp:
    """The stylesheet, the settings and the template have to agree, and none of
    them raises when they don't — a theme name matches a block or it silently
    falls back (ADR 0011)."""

    @pytest.mark.parametrize("name", THEME_NAMES)
    def test_the_theme_is_defined(self, name):
        assert _theme_properties(name)

    @pytest.mark.parametrize("name", THEME_NAMES)
    def test_the_theme_is_defined_exactly_once(self, name):
        """Two blocks for one name is correct-by-source-order, which is a thing
        that quietly stops being true when someone edits the wrong one. The
        browser would take the last; every assertion below reads the first.
        """
        source = THEME_CSS.read_text(encoding="utf-8")

        assert source.count(f'[data-theme="{name}"]') == 1

    def test_the_site_opens_in_the_brand(self):
        assert DEMO_MVP_CONFIG["theme"]["default"] == "mvp"
        assert DEMO_MVP_CONFIG["theme"]["dark"] == "mvp-dark"

    def test_the_pair_leads_the_picker(self):
        assert DEMO_MVP_CONFIG["theme"]["choices"][:2] == list(THEME_NAMES)

    def test_the_base_template_loads_the_stylesheet(self):
        """Without the `<link>` the site names two themes nothing defines, and
        every page renders in the fallback with no error anywhere."""
        base = (REPO_ROOT / "demo" / "templates" / "base.html").read_text(encoding="utf-8")

        assert "css/themes.css" in base
        assert "block.super" in base, (
            "a styles block without block.super drops the packaged stylesheet, "
            "which is a blank site rather than a wrong theme"
        )


class TestDemoThemeContrast:
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
        renders a form error at, which is the defect this file exists to keep
        out of the demo. Asserting the helper flags it proves the floor works.
        """
        assert _contrast("#8a8a8a", "#ffffff") < AA_TEXT
        assert _contrast("#000000", "#ffffff") == pytest.approx(21.0, abs=0.01)

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
