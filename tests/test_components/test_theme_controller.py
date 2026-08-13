"""Tests for the theme controller: the pre-paint guard in ``mvp/base.html``
that sets ``data-theme`` before first paint (FS-026 US1), and — later, T005
onward — the fall-through behaviour and the themed switcher component.

Assertions target rendered markup (Article XIII): the pre-paint guard cannot
be exercised with a real browser's ``localStorage`` from the Django test
client, so what's checked is the emitted script's source, which is the
guard's actual contract.
"""

import re

import pytest

from mvp.config import MVP_CONFIG


def _guard_script(html):
    """The first ``<script>...</script>`` block inside ``<head>`` — the
    pre-paint guard must be it (FR-005: first thing in ``<head>``, before
    any stylesheet link)."""
    match = re.search(r"<head>.*?<script>(.*?)</script>", html, re.S)
    return match.group(1) if match else None


class TestPrePaintThemeGuardPosition:
    """The guard stays inline and first in ``<head>`` (FR-005)."""

    @pytest.mark.django_db
    def test_guard_is_first_thing_in_head_before_any_stylesheet_link(self, client):
        content = client.get("/").content.decode()
        head_start = content.find("<head>")
        script_pos = content.find("<script>", head_start)
        stylesheet_pos = content.find('rel="stylesheet"', head_start)
        assert head_start != -1
        assert script_pos != -1
        assert stylesheet_pos != -1
        assert head_start < script_pos < stylesheet_pos


class TestPrePaintThemeGuardDefault:
    """The guard's stored-value-or-fallback expression (SC-006, FR-003)."""

    @pytest.mark.django_db
    def test_matches_v0_18_0_behaviour_with_nothing_configured(self, client):
        """With the package's own default (``theme.default == "light"``, no
        project override), the guard's expression is exactly what v0.18.0
        hardcoded: the stored value if present, otherwise ``'light'``."""
        assert MVP_CONFIG["theme"]["default"] == "light"
        script = _guard_script(client.get("/").content.decode())
        assert script is not None
        assert "localStorage.getItem('theme')" in script
        assert '"light"' in script

    @pytest.mark.django_db
    def test_configured_default_is_used_when_nothing_is_stored(self, client, monkeypatch):
        """With ``theme.default`` set, the guard falls back to the
        configured theme rather than the hardcoded ``'light'``."""
        monkeypatch.setitem(MVP_CONFIG["theme"], "default", "dracula")
        script = _guard_script(client.get("/").content.decode())
        assert script is not None
        assert '"dracula"' in script
        assert "'light'" not in script


class TestPrePaintThemeGuardEscaping:
    """The configured theme reaches the script as an escaped literal, not
    raw interpolation into the script body (Article V)."""

    @pytest.mark.django_db
    def test_configured_default_cannot_break_out_of_the_script(self, client, monkeypatch):
        """A theme name containing a quote and a closing script tag must not
        be able to terminate the string, close the script element early, or
        open a second one."""
        malicious = '"; alert(1); //</script><script>alert(2)</script>'
        monkeypatch.setitem(MVP_CONFIG["theme"], "default", malicious)
        content = client.get("/").content.decode()

        assert malicious not in content
        assert "</script><script>alert(2)</script>" not in content

        head_start = content.find("<head>")
        stylesheet_pos = content.find('rel="stylesheet"', head_start)
        head_before_styles = content[head_start:stylesheet_pos]
        assert head_before_styles.count("<script") == 1, (
            "an unescaped payload must not be able to inject an additional "
            "<script> element ahead of the stylesheet link"
        )
