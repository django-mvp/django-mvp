"""Keeps docs/theming.md's variable table honest against the installed
daisyUI version, so an upgrade that adds a theme variable fails a test
instead of silently ageing the documentation (SC-007).
"""

import re
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent

# node_modules is gitignored and the Python CI job never runs npm ci, so
# discovery must skip explicitly rather than fail when the front-end
# toolchain isn't installed — the same convention tests/test_smoke.py uses
# for the shipped-theme completeness check.
_DAISYUI_THEME_DIR = BASE_DIR / "node_modules" / "daisyui" / "theme"
_CUSTOM_PROPERTY_RE = re.compile(r"--[a-zA-Z0-9-]+")


def _extract_custom_properties(css: str) -> set[str]:
    return set(_CUSTOM_PROPERTY_RE.findall(css))


class TestThemingDocVariableCoverage:
    """Every custom property a shipped theme defines appears in
    docs/theming.md's variable table (FR-015, SC-007)."""

    THEMING_DOC = BASE_DIR / "docs" / "theming.md"
    SHIPPED_THEME_FILE = _DAISYUI_THEME_DIR / "light.css"

    def test_shipped_theme_source_is_discoverable(self):
        """Guards discovery before the next test reads from it. Skips
        explicitly when node_modules/daisyui/theme is absent, so the suite
        still runs for a contributor who hasn't installed the front-end
        toolchain."""
        if not _DAISYUI_THEME_DIR.is_dir():
            pytest.skip(
                "node_modules/daisyui/theme not installed — front-end "
                "toolchain not present in this environment"
            )
        assert self.SHIPPED_THEME_FILE.is_file(), (
            "node_modules/daisyui/theme is present but light.css is missing from it"
        )

    @pytest.mark.skipif(
        not _DAISYUI_THEME_DIR.is_dir(),
        reason="node_modules/daisyui/theme not installed",
    )
    def test_every_shipped_custom_property_is_documented(self):
        """Every --custom-property name a shipped theme defines is named in
        docs/theming.md, checked mechanically rather than by hand (SC-007)."""
        theme_css = self.SHIPPED_THEME_FILE.read_text(encoding="utf-8")
        properties = _extract_custom_properties(theme_css)
        assert properties, (
            "no --custom-property names were extracted from "
            f"{self.SHIPPED_THEME_FILE} — the extraction pattern itself "
            "may be broken, not the documentation"
        )

        doc = self.THEMING_DOC.read_text(encoding="utf-8")
        missing = sorted(prop for prop in properties if prop not in doc)
        assert not missing, (
            f"docs/theming.md is missing these theme variables: {missing}"
        )
