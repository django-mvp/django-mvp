"""Regression tests for issue #178: sidebar animates on every page load.

With ``collapse="icons"`` and a persistent (desktop-width) sidebar, the
server always renders the drawer checkbox unchecked (Django cannot read the
client's ``localStorage``). Alpine's ``$persist`` plugin scripts are
``defer``red, so they run after the browser's first paint — by the time
Alpine corrects the checkbox to match the persisted "open" state, the
sidebar's ``transition-[width]`` class has already been visible for a full
frame, and the correction plays as a visible width animation instead of
landing in its resting state.

These tests are E2E because the defect is about *when* the DOM reaches its
final state relative to the browser's first paint, and a CSS transition
firing — neither is observable from server-rendered markup alone.
"""

import pytest

pytest.importorskip("playwright")
from playwright.sync_api import expect  # noqa: E402

from tests.conftest import requires_browser  # noqa: E402

pytestmark = [pytest.mark.e2e, requires_browser]

DESKTOP = {"width": 1280, "height": 800}


def _sidebar_url(live_server):
    """The icons-collapse, persistent shell fixture, served at a real URL.

    ``demo/templates/tests/app_shell_override.html`` already extends
    ``mvp/base.html`` with ``breakpoint="xl" collapse="icons"`` for
    ``test_navbar_toggle_follows_shell_override`` (test_layout_config.py);
    reused here rather than adding a second fixture with the same shape.
    No route serves it by default, so the test wires one up itself, the
    same way ``TestFormsetAddRemoveRowsE2E`` does.
    """
    from django.urls import path
    from django.views.generic import TemplateView

    return path(
        "sidebar-persisted-state-e2e/",
        TemplateView.as_view(template_name="tests/app_shell_override.html"),
    )


@pytest.fixture
def sidebar_shell_urlconf():
    from importlib import import_module

    from django.conf import settings

    base_urlpatterns = import_module(settings.ROOT_URLCONF).urlpatterns
    return type(
        "_URLConf",
        (),
        {"urlpatterns": [_sidebar_url(None), *base_urlpatterns]},
    )


@pytest.mark.django_db
class TestSidebarStateSettledBeforeFirstPaint:
    """Loading a page with a persistent, icon-collapsed sidebar must never
    play a width transition — the persisted state has to be visually
    correct from the very first painted frame (#178)."""

    def test_no_width_transition_plays_on_load(
        self, page, live_server, sidebar_shell_urlconf
    ):
        from django.test import override_settings

        page.set_viewport_size(DESKTOP)
        # Attach the listener before any page script runs, so it can catch
        # a transition that starts during Alpine's hydration correction.
        page.add_init_script(
            """
            window.__widthTransitions = [];
            document.addEventListener('transitionstart', (e) => {
              if (e.propertyName === 'width') {
                window.__widthTransitions.push(e.target.className);
              }
            }, true);
            """
        )
        with override_settings(ROOT_URLCONF=sidebar_shell_urlconf):
            page.goto(f"{live_server.url}/sidebar-persisted-state-e2e/")
            # Alpine's persist scripts are deferred; give hydration + the
            # transition's own 200ms duration time to run before asserting.
            page.wait_for_timeout(600)

        assert page.evaluate("window.__widthTransitions") == [], (
            "the sidebar's width must already be correct on first paint — "
            "no post-hydration correction should ever animate (#178)"
        )

    def test_sidebar_is_already_open_on_first_frame(
        self, page, live_server, sidebar_shell_urlconf
    ):
        """A first-time visitor defaults to an open desktop sidebar
        (``$persist(true)``); the rendered rail must already show it at
        full width once Alpine has settled, not merely eventually."""
        from django.test import override_settings

        page.set_viewport_size(DESKTOP)
        with override_settings(ROOT_URLCONF=sidebar_shell_urlconf):
            page.goto(f"{live_server.url}/sidebar-persisted-state-e2e/")
            page.wait_for_timeout(600)

        sidebar = page.locator("aside.mvp-sidebar")
        expect(sidebar).to_be_visible()
        box = sidebar.bounding_box()
        assert box is not None
        assert box["width"] > 200, (
            "the icon-rail sidebar should have settled at its open (w-65) "
            "width, not stayed collapsed at the icon-rail (w-16) width"
        )
