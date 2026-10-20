"""A project's own drawer is not styled by the shell's drawer rules.

The shell is a daisyUI drawer, and a project is free to put another one
anywhere: inside a page, or around the whole shell. The shell's rules in
``mvp/tailwind/base.css`` used to be written against any ``.drawer``, so they
reached both. Which rules match which element is decided by the browser's
selector engine against real markup, so this is a browser test.

Every class the templates use is one the prebuilt stylesheet already emits.
"""

from importlib import import_module

import pytest
from django.conf import settings
from django.test import override_settings
from django.urls import path
from django.views.generic import TemplateView

from tests.conftest import requires_browser, urlconf_of

pytestmark = [pytest.mark.e2e, requires_browser]

DESKTOP = {"width": 1440, "height": 900}

NESTED_URLCONF = urlconf_of(
    path(
        "drawer-in-page/",
        TemplateView.as_view(template_name="tests/drawer_in_page.html"),
    ),
    path(
        "drawer-around-shell/",
        TemplateView.as_view(template_name="tests/drawer_around_shell.html"),
    ),
    *import_module(settings.ROOT_URLCONF).urlpatterns,
)


def _open_page(page, live_server, url, *, sidebar_open):
    page.add_init_script(
        f"localStorage.setItem('mvp-app-drawer-open', '{str(sidebar_open).lower()}')"
    )
    page.set_viewport_size(DESKTOP)
    with override_settings(ROOT_URLCONF=NESTED_URLCONF):
        page.goto(f"{live_server.url}{url}")
    return page


def _style(page, selector, prop):
    return page.evaluate(
        "([sel, prop]) => getComputedStyle(document.querySelector(sel))[prop]",
        [selector, prop],
    )


@pytest.mark.django_db
class TestADrawerInsideAPage:
    @pytest.fixture
    def drawer_page(self, page, live_server):
        return _open_page(page, live_server, "/drawer-in-page/", sidebar_open=True)

    def test_the_shell_sidebar_is_open(self, drawer_page):
        assert drawer_page.locator("#mvp-app-toggle").is_checked()
        assert not drawer_page.locator("#project-drawer-toggle").is_checked()

    def test_is_drawer_open_does_not_follow_the_shell(self, drawer_page):
        # The project drawer is closed; the shell's being open must not count.
        assert _style(drawer_page, "#project-open-probe", "marginInlineEnd") == "0px"

    def test_is_drawer_close_follows_its_own_drawer(self, drawer_page):
        assert (
            _style(drawer_page, "#project-close-probe", "paddingInlineStart") == "8px"
        )

    def test_is_drawer_open_follows_its_own_drawer(self, drawer_page):
        # daisyUI hides the toggle off-screen, so it cannot be clicked.
        drawer_page.evaluate(
            "document.getElementById('project-drawer-toggle').checked = true"
        )

        assert _style(drawer_page, "#project-open-probe", "marginInlineEnd") == "8px"
        assert (
            _style(drawer_page, "#project-close-probe", "paddingInlineStart") == "0px"
        )

    def test_a_filled_page_does_not_fill_the_project_drawer(self, drawer_page):
        assert _style(drawer_page, "#project-drawer-content", "display") != "flex"
        assert (
            _style(drawer_page, "#project-drawer-content", "minHeight")
            != f"{DESKTOP['height']}px"
        )

    def test_a_filled_page_still_fills_the_shell(self, drawer_page):
        assert _style(drawer_page, "#mvp-app > .drawer-content", "display") == "flex"
        assert (
            _style(drawer_page, "#mvp-app > .drawer-content", "height")
            == f"{DESKTOP['height']}px"
        )


@pytest.mark.django_db
class TestADrawerAroundTheShell:
    def test_a_closed_sidebar_stays_closed_while_the_project_drawer_is_open(
        self, page, live_server
    ):
        page = _open_page(
            page, live_server, "/drawer-around-shell/", sidebar_open=False
        )

        assert page.locator("#project-drawer-toggle").is_checked()
        assert not page.locator("#mvp-app-toggle").is_checked()
        assert page.locator(".mvp-sidebar").bounding_box()["width"] == 0

    def test_an_open_sidebar_keeps_its_width(self, page, live_server):
        page = _open_page(page, live_server, "/drawer-around-shell/", sidebar_open=True)

        assert page.locator("#mvp-app-toggle").is_checked()
        assert page.locator(".mvp-sidebar").bounding_box()["width"] == pytest.approx(
            260, abs=1
        )
