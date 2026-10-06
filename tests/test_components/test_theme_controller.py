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
    @pytest.mark.django_db
    def test_falls_back_to_the_packaged_default_with_nothing_configured(self, client):
        assert MVP_CONFIG["theme"]["default"] == "light"
        script = _guard_script(client.get("/").content.decode())
        assert script is not None
        assert '"light"' in script

    @pytest.mark.django_db
    def test_configured_default_is_used_when_nothing_is_stored(
        self, client, monkeypatch
    ):
        monkeypatch.setitem(MVP_CONFIG["theme"], "default", "dracula")
        script = _guard_script(client.get("/").content.decode())
        assert script is not None
        assert '"dracula"' in script
        assert "'light'" not in script


class TestPrePaintThemeGuardEscaping:
    @pytest.mark.django_db
    def test_configured_default_cannot_break_out_of_the_script(
        self, client, monkeypatch
    ):
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
        r"<label[^>]*>(?:(?!</label>).)*?data-toggle-theme(?:(?!</label>).)*</label>",
        content,
        re.S,
    )
    return match.group(0) if match else None


class TestThemeControllerUnconfiguredShape:
    @pytest.mark.django_db
    def test_renders_the_checkbox_toggle_over_the_configured_pair(self, client):
        assert MVP_CONFIG["theme"]["choices"] == []
        content = client.get("/").content.decode()
        toggle = _theme_toggle_html(content)
        assert toggle is not None, "the checkbox toggle must render"
        assert 'data-toggle-theme="dark,light"' in toggle
        assert 'data-act-class="swap-active"' in toggle
        assert re.search(r'aria-label="[^"]+"', toggle), "needs an accessible name"
        assert "data-set-theme" not in toggle, (
            "the unconfigured shape must not carry the offered-set API"
        )

    @pytest.mark.django_db
    def test_the_toggle_is_a_named_switch(self, cotton_render_string_soup):
        soup = cotton_render_string_soup(
            "<c-mvp.actions.theme-controller />", context={"mvp_config": MVP_CONFIG}
        )

        toggle = soup.select_one("input[data-toggle-theme]")
        assert toggle["type"] == "checkbox"
        assert toggle["role"] == "switch"
        assert toggle["aria-label"].strip()

    @pytest.mark.django_db
    def test_the_toggle_follows_a_replaced_pair(self, client, monkeypatch):
        monkeypatch.setitem(MVP_CONFIG["theme"], "default", "sunrise")
        monkeypatch.setitem(MVP_CONFIG["theme"], "dark", "midnight")
        toggle = _theme_toggle_html(client.get("/").content.decode())

        assert toggle is not None, "the checkbox toggle must render"
        assert 'data-toggle-theme="midnight,sunrise"' in toggle


class TestThemeControllerOfferedSetShape:
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
    def test_each_entry_is_keyboard_reachable_with_an_accessible_name(
        self, client, monkeypatch
    ):
        monkeypatch.setitem(MVP_CONFIG["theme"], "choices", self.CHOICES)
        content = client.get("/").content.decode()
        for name in self.CHOICES:
            match = re.search(
                rf'<button[^>]*data-set-theme="{name}"[^>]*>(.*?)</button>',
                content,
                re.S,
            )
            assert match is not None, (
                f"the {name} entry must be a natively focusable element — a "
                "bare <a> without href is not in the tab order"
            )
            assert match.group(1).strip(), (
                f"{name} entry must have a non-empty accessible name"
            )

    @pytest.mark.django_db
    def test_the_choices_menu_has_an_accessible_name(
        self, cotton_render_string_soup, monkeypatch
    ):
        monkeypatch.setitem(MVP_CONFIG["theme"], "choices", self.CHOICES)

        soup = cotton_render_string_soup(
            "<c-mvp.actions.theme-controller />", context={"mvp_config": MVP_CONFIG}
        )

        assert soup.select_one("ul.menu")["aria-label"].strip()

    @pytest.mark.django_db
    def test_no_entry_is_a_non_focusable_anchor(self, client, monkeypatch):
        monkeypatch.setitem(MVP_CONFIG["theme"], "choices", self.CHOICES)
        content = client.get("/").content.decode()

        assert not re.search(r"<a[^>]*data-set-theme=", content), (
            "a theme entry rendered as an <a> without href, which is not "
            "keyboard reachable"
        )


class TestUnmatchedThemeNameFallsThrough:
    UNMATCHED_NAME = "totallynotarealtheme"

    @pytest.mark.django_db
    def test_unmatched_theme_name_renders_without_raising(self, client, monkeypatch):
        monkeypatch.setitem(MVP_CONFIG["theme"], "default", self.UNMATCHED_NAME)
        response = client.get("/")
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_unmatched_theme_name_is_emitted_unvalidated(self, client, monkeypatch):
        monkeypatch.setitem(MVP_CONFIG["theme"], "default", self.UNMATCHED_NAME)
        script = _guard_script(client.get("/").content.decode())
        assert script is not None
        assert f'"{self.UNMATCHED_NAME}"' in script

    def test_default_theme_stays_bound_through_where_root(self):
        stylesheet = BASE_DIR / "mvp" / "static" / "css" / "django-mvp.css"
        content = stylesheet.read_text(encoding="utf-8")
        assert ":where(:root)" in content, (
            "the :where(:root) fall-through binding for the default theme "
            "is missing from the shipped stylesheet"
        )


class TestPrePaintThemeGuardMembership:
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
        monkeypatch.setitem(MVP_CONFIG["theme"], "choices", self.CHOICES)
        script = _guard_script(client.get("/").content.decode())
        assert script is not None
        has_membership_check = (
            "indexOf(stored)" in script or "includes(stored)" in script
        )
        assert has_membership_check, (
            "the guard must check the stored value's membership in the offered set"
        )

    @pytest.mark.django_db
    def test_empty_offered_set_keeps_the_v0_18_0_short_circuit(self, client):
        assert MVP_CONFIG["theme"]["choices"] == []
        script = _guard_script(client.get("/").content.decode())
        assert script is not None
        assert "[]" in script, "the empty offered set must reach the guard"
