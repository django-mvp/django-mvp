"""Tests for ``mvp.pwa.colors.ThemeColors``, which reads the committed stylesheet."""

import re
from pathlib import Path

import pytest

from mvp.pwa.colors import ThemeColors

STYLESHEET = Path(__file__).parents[2] / "mvp" / "static" / "css" / "django-mvp.css"
HEX = re.compile(r"^#[0-9a-f]{6}$")


class TestThemeColors:
    def test_every_theme_in_the_stylesheet_resolves_to_a_hex_colour(self):
        names = set(re.findall(r"\[data-theme=([\w-]+)\]", STYLESHEET.read_text()))

        assert len(names) == 35
        for name in sorted(names):
            assert HEX.match(ThemeColors.for_theme(name) or ""), name

    @pytest.mark.parametrize(
        ("theme", "expected"),
        [
            # Converted independently of the code under test, with the
            # published OKLab matrices; they match daisyUI's long-standing hex
            # values for these themes. Never regenerate them from the code.
            ("light", "#ffffff"),
            ("dark", "#1d232a"),
            ("cupcake", "#faf7f5"),
        ],
    )
    def test_known_themes_match_their_reference_colour(self, theme, expected):
        assert ThemeColors.for_theme(theme) == expected

    @pytest.mark.parametrize(
        ("declaration", "expected"),
        [
            ("oklch(100% 0 0)", "#ffffff"),
            ("oklch(1 0 0)", "#ffffff"),
            ("oklch(25.33% .016 252.42)", "#1d232a"),
            ("oklch(.2533 .016 252.42)", "#1d232a"),
        ],
    )
    def test_lightness_parses_as_a_percentage_or_a_number(
        self, declaration, expected, tmp_path, monkeypatch
    ):
        # A minifier may write the lightness either way; both mean the same colour.
        stylesheet = tmp_path / "django-mvp.css"
        stylesheet.write_text(
            "[data-theme=probe]{color-scheme:light;--color-base-100:%s}" % declaration
        )
        monkeypatch.setattr("mvp.pwa.colors.STYLESHEET", stylesheet)
        ThemeColors.table.cache_clear()
        try:
            assert ThemeColors.for_theme("probe") == expected
        finally:
            ThemeColors.table.cache_clear()

    def test_an_unknown_theme_has_no_colour(self):
        assert ThemeColors.for_theme("not-a-shipped-theme") is None
