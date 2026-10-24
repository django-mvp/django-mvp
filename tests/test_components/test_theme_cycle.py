"""The light, dark and automatic theme button (``c-mvp.actions.theme-cycle``)
as rendered markup, and the part of the pre-paint guard in ``mvp/base.html``
that resolves the automatic choice.

What the button does in a browser is in ``test_theme_cycle_e2e.py``. Here is
the markup its script reads, and the guard's source, which is the guard's
contract for the same reason given in ``test_theme_controller.py``.
"""

import re

import pytest

from mvp.config import MVP_CONFIG


def _guard_script(html):
    match = re.search(r"<head>.*?<script>(.*?)</script>", html, re.S)
    return match.group(1) if match else None


class TestThemeCycleButton:
    @pytest.mark.django_db
    def test_is_a_plain_button_carrying_the_configured_pair(
        self, cotton_render_string_soup
    ):
        soup = cotton_render_string_soup(
            "<c-mvp.actions.theme-cycle />", context={"mvp_config": MVP_CONFIG}
        )

        button = soup.select_one("[data-theme-cycle]")
        assert button.name == "button"
        assert button["type"] == "button"
        assert button["data-theme-cycle"] == "light,dark"

    @pytest.mark.django_db
    def test_follows_a_replaced_pair(self, cotton_render_string_soup, monkeypatch):
        monkeypatch.setitem(MVP_CONFIG["theme"], "default", "sunrise")
        monkeypatch.setitem(MVP_CONFIG["theme"], "dark", "midnight")

        soup = cotton_render_string_soup(
            "<c-mvp.actions.theme-cycle />", context={"mvp_config": MVP_CONFIG}
        )

        assert soup.select_one("[data-theme-cycle]")["data-theme-cycle"] == (
            "sunrise,midnight"
        )

    @pytest.mark.django_db
    def test_renders_where_the_layout_lists_it(self, client, monkeypatch):
        monkeypatch.setitem(
            MVP_CONFIG["layout"]["navbar"], "end", ["mvp.actions.theme-cycle"]
        )

        content = client.get("/").content.decode()

        assert 'data-theme-cycle="light,dark"' in content
        assert "data-toggle-theme" in content, (
            "the sidebar footer keeps the packaged toggle"
        )


class TestPrePaintGuardAutomatic:
    @pytest.mark.django_db
    def test_reads_the_device_setting_for_an_automatic_choice(self, client):
        script = _guard_script(client.get("/").content.decode())

        assert "prefers-color-scheme: dark" in script
        assert "=== ''" in script, (
            "an empty stored theme is the automatic choice, and only that "
            "value, so a visitor who never chose still gets the default"
        )

    @pytest.mark.django_db
    def test_resolves_to_the_configured_dark_theme(self, client, monkeypatch):
        monkeypatch.setitem(MVP_CONFIG["theme"], "dark", "midnight")

        script = _guard_script(client.get("/").content.decode())

        assert '"midnight"' in script

    @pytest.mark.django_db
    def test_configured_dark_cannot_break_out_of_the_script(self, client, monkeypatch):
        malicious = '"; alert(1); //</script><script>alert(2)</script>'
        monkeypatch.setitem(MVP_CONFIG["theme"], "dark", malicious)

        content = client.get("/").content.decode()
        head_start = content.find("<head>")
        stylesheet_pos = content.find('rel="stylesheet"', head_start)

        assert content[head_start:stylesheet_pos].count("<script") == 1
