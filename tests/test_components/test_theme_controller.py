"""Tests for the theme controller: the pre-paint guard in ``mvp/base.html``
that sets ``data-theme`` before first paint (FS-026 US1), and — later, T005
onward — the fall-through behaviour and the themed switcher component.

Assertions target rendered markup (Article XIII): the pre-paint guard cannot
be exercised with a real browser's ``localStorage`` from the Django test
client, so what's checked is the emitted script's source, which is the
guard's actual contract.
"""

import re
from pathlib import Path

import pytest

from mvp.config import MVP_CONFIG

BASE_DIR = Path(__file__).resolve().parent.parent.parent


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


class TestUnmatchedThemeNameFallsThrough:
    """A configured theme name matching no shipped or project theme block
    leaves the page rendering under the ``:where(:root)`` default, and
    nothing raises — the deliberate non-feature decisions.md D5 settled:
    theme names are not validated, because the package cannot see a
    project's own theme file. This is a regression guard on that decision:
    without it, a later contributor reads the absence of validation as an
    oversight and adds it back (FR-014, SC-008).
    """

    UNMATCHED_NAME = "totallynotarealtheme"

    @pytest.mark.django_db
    def test_unmatched_theme_name_renders_without_raising(self, client, monkeypatch):
        monkeypatch.setitem(MVP_CONFIG["theme"], "default", self.UNMATCHED_NAME)
        response = client.get("/")
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_unmatched_theme_name_is_emitted_unvalidated(self, client, monkeypatch):
        """No render-time check rejects it — the guard emits whatever name
        is configured, exactly as it does for a name that does match (T004),
        because the package cannot evaluate whether a project's own theme
        file defines it."""
        monkeypatch.setitem(MVP_CONFIG["theme"], "default", self.UNMATCHED_NAME)
        script = _guard_script(client.get("/").content.decode())
        assert script is not None
        assert f'"{self.UNMATCHED_NAME}"' in script

    def test_default_theme_stays_bound_through_where_root(self):
        """The zero-specificity :where(:root) arm is what makes the
        fall-through safe: it matches the document root unconditionally, so
        an unmatched data-theme value still resolves to the default theme's
        styles instead of an unstyled page."""
        stylesheet = BASE_DIR / "mvp" / "static" / "css" / "django-mvp.css"
        content = stylesheet.read_text(encoding="utf-8")
        assert ":where(:root)" in content, (
            "the :where(:root) fall-through binding for the default theme "
            "is missing from the shipped stylesheet"
        )
