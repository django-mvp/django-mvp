"""Tests for LayoutConfig, the layout resolver (mvp/layout.py).

Normalisation — what "never"/"none" mean, and what an unrecognised
breakpoint name falls back to — lives in this one class and nowhere else.
These tests pin that behaviour directly against the class, independent of
any template tag that reads it.
"""

import pytest

from mvp.layout import LayoutConfig


class TestLayoutConfigBreakpoint:
    """Breakpoint normalisation and the pixel width it resolves to."""

    @pytest.mark.parametrize(
        ("bp", "px"),
        [
            ("sm", 640),
            ("md", 768),
            ("lg", 1024),
            ("xl", 1280),
            ("2xl", 1536),
        ],
    )
    def test_supported_breakpoints_resolve_their_own_width(self, bp, px):
        config = LayoutConfig(bp, "offcanvas", True, False)
        assert config.breakpoint == bp
        assert config.breakpoint_px == px
        assert config.persistent is True

    @pytest.mark.parametrize(
        "value", ["never", "NEVER", "Never", "none", "NONE", "None"]
    )
    def test_never_and_none_in_any_case_disable_the_persistent_sidebar(self, value):
        config = LayoutConfig(value, "offcanvas", True, False)
        assert config.breakpoint == "never"
        assert config.persistent is False
        assert config.breakpoint_px is None

    def test_an_unrecognised_breakpoint_falls_back_to_lg(self):
        config = LayoutConfig("bogus", "offcanvas", True, False)
        assert config.breakpoint == "lg"
        assert config.breakpoint_px == 1024
        assert config.persistent is True

    def test_a_missing_breakpoint_falls_back_to_lg(self):
        config = LayoutConfig(None, "offcanvas", True, False)
        assert config.breakpoint == "lg"
        assert config.breakpoint_px == 1024


class TestLayoutConfigAsDict:
    """The client payload's exact shape: grouped by component, camelCase —
    the same document the client store groups its own state into (T018)."""

    def test_as_dict_carries_exactly_the_documented_keys(self):
        config = LayoutConfig("md", "icons", False, True)
        assert config.as_dict() == {
            "sidebar": {
                "breakpoint": "md",
                "persistent": True,
                "breakpointPx": 768,
                "collapse": "icons",
                "boost": True,
            },
            "header": {
                "sticky": False,
            },
        }

    def test_as_dict_reflects_a_disabled_breakpoint(self):
        config = LayoutConfig("never", "offcanvas", True, False)
        assert config.as_dict() == {
            "sidebar": {
                "breakpoint": "never",
                "persistent": False,
                "breakpointPx": None,
                "collapse": "offcanvas",
                "boost": False,
            },
            "header": {
                "sticky": True,
            },
        }
