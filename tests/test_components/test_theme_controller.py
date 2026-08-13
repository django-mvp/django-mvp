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


def _theme_toggle_html(content):
    """The unconfigured switcher's ``<label>...</label>`` — the checkbox
    toggle, isolated from the rest of the page (it renders twice per page,
    once in the navbar and once in the sidebar footer, per
    ``tests/settings.py``)."""
    match = re.search(
        r'<label[^>]*title="Toggle dark mode"[^>]*>.*?</label>', content, re.S
    )
    return match.group(0) if match else None


class TestThemeControllerUnconfiguredShape:
    """With ``theme.choices`` empty (the package default), the switcher
    renders exactly today's markup: the ``data-toggle-theme="dark,light"``
    checkbox, its ``data-act-class``, both icons and the translated label
    (FR-006, FR-008). Written against the *current* template, before T006's
    production change, so it is a genuine regression guard rather than a
    description of whatever the change produces."""

    @pytest.mark.django_db
    def test_renders_the_v0_18_0_checkbox_toggle_unchanged(self, client):
        assert MVP_CONFIG["theme"]["choices"] == []
        content = client.get("/").content.decode()
        toggle = _theme_toggle_html(content)
        assert toggle is not None, "the checkbox toggle must render"
        assert 'data-toggle-theme="dark,light"' in toggle
        assert 'data-act-class="swap-active"' in toggle
        assert "bi bi-sun" in toggle, "the light-mode icon must render"
        assert "bi bi-moon-stars-fill" in toggle, "the dark-mode icon must render"
        assert 'title="Toggle dark mode"' in toggle
        assert 'aria-label="Toggle dark mode"' in toggle
        assert "data-set-theme" not in toggle, (
            "the unconfigured shape must not carry the offered-set API"
        )


class TestThemeControllerOfferedSetShape:
    """With ``theme.choices`` populated, the switcher renders one entry per
    configured theme, in the configured order, each carrying
    ``data-set-theme="<name>"`` — theme-change's documented API, present in
    the shipped bundle. Entries carry accessible names (Article XIII) and
    the control's own label goes through ``gettext`` (Article VIII)
    (FR-007, FR-008, FR-009)."""

    CHOICES = ["dracula", "synthwave", "forest"]

    @pytest.mark.django_db
    def test_offers_exactly_the_configured_themes_in_order(self, client, monkeypatch):
        monkeypatch.setitem(MVP_CONFIG["theme"], "choices", self.CHOICES)
        content = client.get("/").content.decode()

        positions = [content.find(f'data-set-theme="{name}"') for name in self.CHOICES]
        assert all(pos != -1 for pos in positions), (
            "every configured theme must carry data-set-theme"
        )
        assert positions == sorted(positions), (
            "entries must render in the configured order"
        )
        renders = content.count('data-set-theme="dracula"')
        assert renders >= 1, "the configured theme must render at least once"
        assert content.count("data-set-theme=") == len(self.CHOICES) * renders, (
            "no theme outside the configured set may be offered, on any of "
            "the controller's render sites on the page (navbar mobile/"
            "desktop + sidebar footer, per tests/settings.py)"
        )

    @pytest.mark.django_db
    def test_configured_shape_drops_the_unconfigured_checkbox_toggle(
        self, client, monkeypatch
    ):
        monkeypatch.setitem(MVP_CONFIG["theme"], "choices", self.CHOICES)
        content = client.get("/").content.decode()
        assert "data-toggle-theme" not in content

    @pytest.mark.django_db
    def test_each_entry_has_an_accessible_name(self, client, monkeypatch):
        monkeypatch.setitem(MVP_CONFIG["theme"], "choices", self.CHOICES)
        content = client.get("/").content.decode()
        for name in self.CHOICES:
            match = re.search(
                rf'<a[^>]*data-set-theme="{name}"[^>]*>([^<]*)</a>', content
            )
            assert match is not None, f"{name} entry must render as a link"
            assert match.group(1).strip(), (
                f"{name} entry must have a non-empty accessible name"
            )

    @pytest.mark.django_db
    def test_controls_own_label_is_translated(self, client, monkeypatch):
        monkeypatch.setitem(MVP_CONFIG["theme"], "choices", self.CHOICES)
        content = client.get("/").content.decode()
        assert "Choose theme" in content


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


class TestPrePaintThemeGuardMembership:
    """FR-010: once a project declares ``theme.choices``, a stored selection
    that has fallen outside that set must not be honoured — the guard falls
    back to ``theme.default`` instead. A stored value still inside the set
    is honoured, and with ``theme.choices`` empty any stored value is
    honoured, unchanged from v0.18.0 (already covered by
    ``TestPrePaintThemeGuardDefault``).

    This is *not* the validation decisions.md D5 rejected: D5 is about a
    name the package was never given (``theme.default`` against a project's
    own, unreadable stylesheet). Here the offered set is a list the project
    itself declared in ``MVP_CONFIG``, so the package genuinely knows it.

    Per the module docstring, the Django test client cannot exercise real
    browser ``localStorage``, so — as for every other guard test in this
    file — what's checked is the emitted script's source: the offered set
    it must consult, and that it performs a membership check against the
    stored value rather than an unconditional fall-through (decisions.md
    D12 records why source inspection, not a JS runtime, is the seam used
    here too)."""

    CHOICES = ["dracula", "synthwave"]

    @pytest.mark.django_db
    def test_offered_set_reaches_the_guard_for_the_membership_check(
        self, client, monkeypatch
    ):
        monkeypatch.setitem(MVP_CONFIG["theme"], "choices", self.CHOICES)
        script = _guard_script(client.get("/").content.decode())
        assert script is not None
        for name in self.CHOICES:
            assert f'"{name}"' in script, (
                f"{name} must appear in the guard's offered-set array"
            )

    @pytest.mark.django_db
    def test_guard_checks_stored_value_membership_before_honouring_it(
        self, client, monkeypatch
    ):
        """A stored value is only honoured when it is inside the offered
        set — the guard's expression must consult membership, not just
        presence, once a set is configured."""
        monkeypatch.setitem(MVP_CONFIG["theme"], "choices", self.CHOICES)
        script = _guard_script(client.get("/").content.decode())
        assert script is not None
        has_membership_check = "indexOf(stored)" in script or "includes(stored)" in script
        assert has_membership_check, (
            "the guard must check the stored value's membership in the offered set"
        )

    @pytest.mark.django_db
    def test_empty_offered_set_keeps_the_v0_18_0_short_circuit(self, client):
        """With nothing configured (the package default), the emitted
        offered-set array is empty — the membership check's own logic must
        make that equivalent to 'any stored value is honoured' (SC-006),
        not silently reject every stored value."""
        assert MVP_CONFIG["theme"]["choices"] == []
        script = _guard_script(client.get("/").content.decode())
        assert script is not None
        assert "[]" in script, "the empty offered set must reach the guard"
