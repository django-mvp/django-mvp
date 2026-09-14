"""Tests for ``<c-account.nav>`` — the Account Center's navigation panel.

Source: mvp/templates/cotton/account/nav.html

Fixture: ``demo/templates/tests/account_nav.html``.
``tests/test_components/test_layout_config.py`` is the pattern for the
breakpoint assertions this file follows.
"""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test import RequestFactory, override_settings
from django.urls import include, path


def _urlconf():
    """The Account Center mounted, independent of whether the demo app also
    mounts it (T011): the "overview" entry's ``view_name="account-center"``
    has to resolve for the panel to draw it at all."""
    patterns = [path("account/", include("mvp.urls"))]
    return type("_URLConf", (), {"urlpatterns": patterns})


ACCOUNT_URLCONF = _urlconf()


def _render(template_name):
    """Render a template with full request context (anonymous user)."""
    request = RequestFactory().get("/")
    request.user = AnonymousUser()
    return render_to_string(template_name, request=request)


class TestAccountNav:
    """The panel renders as a nav landmark, draws every entry, and renders
    twice for the two breakpoints (FR-013)."""

    @pytest.fixture(autouse=True)
    def _account_urlconf(self):
        with override_settings(ROOT_URLCONF=ACCOUNT_URLCONF):
            yield

    def test_renders_as_a_nav_landmark_with_an_accessible_name(self):
        html = _render("tests/account_nav.html")
        assert 'role="navigation"' in html
        assert 'aria-label="Account navigation"' in html

    def test_draws_the_entry_for_the_landing_page(self):
        html = _render("tests/account_nav.html")
        assert "Overview" in html

    def test_renders_a_persistent_panel_at_the_configured_breakpoint(self):
        """Above ``lg`` (the test suite's configured breakpoint) the panel is
        a persistent block. ``navbar_wide_only_class`` is the same mechanism
        the header's own desktop/mobile widget split already uses."""
        html = _render("tests/account_nav.html")
        assert "hidden lg:flex" in html

    def test_renders_a_collapsed_control_below_the_breakpoint(self):
        html = _render("tests/account_nav.html")
        assert "flex lg:hidden" in html

    def test_the_collapsed_control_is_the_packaged_dropdown(self):
        html = _render("tests/account_nav.html")
        assert "dropdown" in html
        assert "dropdown-content" in html

    def test_the_landmark_appears_twice_one_per_breakpoint_region(self):
        """One menu, two render sites (FR-013) — not a single landmark toggled
        with CSS, or the entries in the collapsed control would be a stale
        copy the moment a check or an ordering changes per request."""
        html = _render("tests/account_nav.html")
        assert html.count('aria-label="Account navigation"') == 2
