"""Tests for mvp.email.brand: the colours and logos an email is drawn in (FS-044)."""

import math

import pytest
from coloraide import Color

from mvp.config import MVP_CONFIG
from mvp.email.brand import EmailBrand

# The packaged daisyUI themes, as mvp/static/css/django-mvp.css writes them.
LIGHT = {
    "base-100": "oklch(100% 0 0)",
    "base-200": "oklch(98% 0 0)",
    "base-300": "oklch(95% 0 0)",
    "base-content": "oklch(21% .006 285.885)",
    "primary": "oklch(45% .24 277.023)",
    "primary-content": "oklch(93% .034 272.788)",
}
DARK = {
    "base-100": "oklch(25.33% .016 252.42)",
    "base-200": "oklch(23.26% .014 253.1)",
    "base-300": "oklch(21.15% .012 254.09)",
    "base-content": "oklch(97.807% .029 256.847)",
    "primary": "oklch(58% .233 277.117)",
    "primary-content": "oklch(96% .018 272.314)",
}

# A complete theme a project could write, in hex so a test can recognise a value.
BRANDX = (
    "--color-base-100:#111111;--color-base-200:#222222;--color-base-300:#333333;"
    "--color-base-content:#eeeeee;--color-primary:#ff8800;--color-primary-content:#000000;"
)


def hex_of(colour: str) -> str:
    """The sRGB hex of a CSS colour, converted by coloraide in the test itself."""
    return Color(colour).convert("srgb").fit().to_string(hex=True)


def seventy_percent_over(top: str, bottom: str) -> str:
    """``top`` laid over ``bottom`` at 70% opacity, channel by channel, rounding halves up."""
    channels = [
        math.floor(int(top[i : i + 2], 16) * 0.7 + int(bottom[i : i + 2], 16) * 0.3 + 0.5) for i in (1, 3, 5)
    ]
    return "#" + "".join(f"{c:02x}" for c in channels)


@pytest.fixture(autouse=True)
def fresh_brand():
    """Each test reads the stylesheets afresh, and leaves nothing cached behind."""
    EmailBrand.current.cache_clear()
    yield
    EmailBrand.current.cache_clear()


@pytest.fixture
def project_css(tmp_path, settings):
    """Write a project stylesheet into a ``STATICFILES_DIRS`` entry, found before the package's."""
    settings.STATICFILES_DIRS = [tmp_path]

    def write(text, name="project.css"):
        (tmp_path / "css").mkdir(exist_ok=True)
        (tmp_path / "css" / name).write_text(text)

    return write


@pytest.fixture
def brandx_theme(monkeypatch):
    """Make the light theme a project theme named ``brandx``."""
    monkeypatch.setitem(MVP_CONFIG["theme"], "default", "brandx")


class TestEmailBrandPackagedThemes:
    def test_light_palette_is_read_from_the_packaged_theme(self):
        expected = {
            "page": hex_of(LIGHT["base-200"]),
            "surface": hex_of(LIGHT["base-100"]),
            "border": hex_of(LIGHT["base-300"]),
            "text": hex_of(LIGHT["base-content"]),
            "muted": seventy_percent_over(hex_of(LIGHT["base-content"]), hex_of(LIGHT["base-100"])),
            "primary": hex_of(LIGHT["primary"]),
            "primary_content": hex_of(LIGHT["primary-content"]),
        }

        light = EmailBrand.current().light

        assert {name: getattr(light, name) for name in expected} == expected

    def test_dark_palette_is_read_from_the_packaged_theme(self):
        expected = {
            "page": hex_of(DARK["base-200"]),
            "surface": hex_of(DARK["base-100"]),
            "border": hex_of(DARK["base-300"]),
            "text": hex_of(DARK["base-content"]),
            "muted": seventy_percent_over(hex_of(DARK["base-content"]), hex_of(DARK["base-100"])),
            "primary": hex_of(DARK["primary"]),
            "primary_content": hex_of(DARK["primary-content"]),
        }

        dark = EmailBrand.current().dark

        assert {name: getattr(dark, name) for name in expected} == expected

    def test_dark_palette_follows_the_configured_dark_theme(self, monkeypatch):
        monkeypatch.setitem(MVP_CONFIG["theme"], "dark", "nord")

        surface = EmailBrand.current().dark.surface

        assert surface == hex_of("oklch(95.127% .007 260.731)")


class TestEmailBrandProjectStylesheets:
    def test_project_values_win_over_the_packaged_theme_of_the_same_name(self, project_css):
        project_css("[data-theme=light]{--color-base-100:#112233;--color-primary:#445566}")

        light = EmailBrand.current().light

        assert (light.surface, light.primary) == ("#112233", "#445566")
        assert light.page == hex_of(LIGHT["base-200"])

    def test_a_theme_only_the_project_defines_is_read(self, project_css, brandx_theme):
        project_css(f"[data-theme=brandx]{{{BRANDX}}}")

        light = EmailBrand.current().light

        assert (light.page, light.surface, light.border) == ("#222222", "#111111", "#333333")
        assert (light.text, light.primary, light.primary_content) == ("#eeeeee", "#ff8800", "#000000")

    def test_the_first_value_found_for_a_property_wins(self, project_css, brandx_theme):
        project_css(f"[data-theme=brandx]{{{BRANDX}}}[data-theme=brandx]{{--color-base-100:#abcdef}}")

        assert EmailBrand.current().light.surface == "#111111"

    def test_a_theme_inside_a_layer_is_read(self, project_css, brandx_theme):
        project_css(f"@layer base{{@layer inner{{[data-theme=brandx]{{{BRANDX}}}}}}}")

        assert EmailBrand.current().light.surface == "#111111"

    def test_a_var_value_is_skipped(self, project_css, brandx_theme):
        project_css(f"[data-theme=brandx]{{--color-base-100:var(--elsewhere)}}[data-theme=brandx]{{{BRANDX}}}")

        assert EmailBrand.current().light.surface == "#111111"

    @pytest.mark.parametrize(
        "selector",
        [
            "[data-theme=brandx]",
            '[data-theme="brandx"]',
            "[data-theme='brandx']",
            ":root[data-theme=brandx]",
            "[data-theme=brandx]:root",
            ":root:has(input.theme-controller[value=brandx]:checked),[data-theme=brandx]",
            ":where(:root),[data-theme=brandx]",
            "[data-theme=brandx],.card [data-theme=other]",
        ],
    )
    def test_a_selector_that_is_the_theme_on_its_own_contributes(self, project_css, brandx_theme, selector):
        project_css(f"{selector}{{--color-base-100:#ff0000}}[data-theme=brandx]{{{BRANDX}}}")

        assert EmailBrand.current().light.surface == "#ff0000"

    @pytest.mark.parametrize(
        "selector",
        [
            "[data-theme=brandx] .mvp-sidebar",
            "[data-theme=brandx]>a",
            ".card[data-theme=brandx]",
            "[data-theme=brandxy]",
        ],
    )
    def test_a_selector_that_is_not_the_theme_on_its_own_does_not_contribute(
        self, project_css, brandx_theme, selector
    ):
        project_css(f"{selector}{{--color-base-100:#ff0000}}[data-theme=brandx]{{{BRANDX}}}")

        assert EmailBrand.current().light.surface == "#111111"


class TestEmailBrandLogos:
    def test_both_packaged_logos_are_given_as_static_urls(self):
        brand = EmailBrand.current()

        assert (brand.logo, brand.logo_dark) == ("/static/brand/email/logo.png", "/static/brand/email/logo_dark.png")

    def test_the_dark_logo_is_given_only_when_the_file_exists(self, tmp_path, project_css, monkeypatch, settings):
        project_css(f"[data-theme=brandx]{{{BRANDX}}}")
        (tmp_path / "brand" / "email").mkdir(parents=True)
        (tmp_path / "brand" / "email" / "logo.png").write_bytes(b"")
        settings.STATICFILES_FINDERS = ["django.contrib.staticfiles.finders.FileSystemFinder"]
        monkeypatch.setitem(MVP_CONFIG["theme"], "default", "brandx")
        monkeypatch.setitem(MVP_CONFIG["theme"], "dark", "brandx")

        brand = EmailBrand.current()

        assert (brand.logo, brand.logo_dark) == ("/static/brand/email/logo.png", None)


class TestEmailBrandCache:
    def test_current_is_cached_until_cleared(self, project_css, brandx_theme):
        project_css(f"[data-theme=brandx]{{{BRANDX}}}")
        first = EmailBrand.current()

        project_css(f"[data-theme=brandx]{{{BRANDX.replace('#111111', '#999999')}}}")

        assert EmailBrand.current() is first
        EmailBrand.current.cache_clear()
        assert EmailBrand.current().light.surface == "#999999"
