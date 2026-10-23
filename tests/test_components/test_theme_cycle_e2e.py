"""The light, dark and automatic theme button, in a real browser.

Which theme applies depends on what the visitor stored and on the device's
colour-scheme setting, and both live in the browser. Rendered markup cannot
show either, so these drive the button and read the applied theme back.
"""

import pytest
from playwright.sync_api import expect

from mvp.config import MVP_CONFIG
from tests.conftest import requires_browser

pytestmark = [pytest.mark.e2e, requires_browser]

DESKTOP = {"width": 1280, "height": 800}


@pytest.fixture
def cycle_in_navbar(monkeypatch):
    monkeypatch.setitem(
        MVP_CONFIG["layout"]["navbar"], "end", ["mvp.actions.theme-cycle"]
    )


@pytest.fixture
def home(page, live_server, cycle_in_navbar):
    page.set_viewport_size(DESKTOP)
    page.goto(f"{live_server.url}/")
    return page


def _button(page):
    return page.locator("[data-theme-cycle]:visible")


def _state(page):
    return page.evaluate(
        """() => ({
            theme: document.documentElement.getAttribute('data-theme'),
            mode: document.documentElement.getAttribute('data-theme-mode'),
            stored: localStorage.getItem('theme'),
        })"""
    )


class TestStepping:
    def test_steps_through_light_dark_and_automatic(self, home):
        home.emulate_media(color_scheme="light")
        assert _state(home) == {"theme": "light", "mode": None, "stored": None}

        _button(home).click()
        assert _state(home) == {"theme": "dark", "mode": "dark", "stored": "dark"}

        _button(home).click()
        assert _state(home) == {"theme": "light", "mode": "auto", "stored": ""}

        _button(home).click()
        assert _state(home) == {"theme": "light", "mode": None, "stored": "light"}

    def test_each_step_names_itself(self, home):
        names = []
        for _ in range(3):
            names.append(_button(home).evaluate("el => el.innerText.trim()"))
            _button(home).click()

        assert all(names), "every step needs an accessible name"
        assert len(set(names)) == 3, f"the three steps share a name: {names}"


class TestAutomatic:
    def test_follows_the_device_while_the_page_is_open(self, home):
        home.emulate_media(color_scheme="light")
        _button(home).click()
        _button(home).click()

        home.emulate_media(color_scheme="dark")
        expect(home.locator("html")).to_have_attribute("data-theme", "dark")

        home.emulate_media(color_scheme="light")
        expect(home.locator("html")).to_have_attribute("data-theme", "light")

    def test_holds_across_a_reload(self, page, live_server, cycle_in_navbar):
        page.emulate_media(color_scheme="dark")
        page.goto(f"{live_server.url}/")
        page.evaluate("localStorage.setItem('theme', '')")

        page.reload()

        assert _state(page) == {"theme": "dark", "mode": "auto", "stored": ""}

    def test_a_visitor_who_never_chose_gets_the_default(
        self, page, live_server, cycle_in_navbar
    ):
        page.emulate_media(color_scheme="dark")
        page.goto(f"{live_server.url}/")

        assert _state(page) == {"theme": "light", "mode": None, "stored": None}


class TestOtherControls:
    def test_a_theme_set_elsewhere_moves_the_button_off_automatic(self, home):
        home.emulate_media(color_scheme="light")
        _button(home).click()
        _button(home).click()

        home.evaluate(
            """() => {
                localStorage.setItem('theme', 'dracula');
                document.documentElement.setAttribute('data-theme', 'dracula');
            }"""
        )

        expect(home.locator("html")).not_to_have_attribute("data-theme-mode", "auto")
        _button(home).click()
        assert _state(home)["theme"] == "dark"
