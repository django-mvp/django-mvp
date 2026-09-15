"""Tests for the sidebar footer's fixed composition.

<c-app.sidebar.footer> no longer reads a widget list from settings (docs/adr/
0023): it always renders the user menu or the log-in button (whichever
matches the request), a theme control and a language control. Rendered via
tests/sidebar_footer.html.
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.utils import translation


def _render(user):
    request = RequestFactory().get("/some/path/")
    request.user = user
    request.LANGUAGE_CODE = "en"
    with translation.override("en"):
        return render_to_string("tests/sidebar_footer.html", request=request)


class TestSidebarFooterAuthenticated:
    """A signed-in request gets the user menu, never the log-in button."""

    @pytest.mark.django_db
    def test_renders_the_user_menu_theme_control_and_language_control(self):
        user = get_user_model().objects.create_user(username="alice", password="pw")
        html = _render(user)

        assert "alice" in html, "the user menu must show the signed-in user's name"
        assert "data-toggle-theme" in html, "the theme control must render"
        assert "showModal()" in html, "the language control must render"

    @pytest.mark.django_db
    def test_does_not_render_the_log_in_button(self):
        user = get_user_model().objects.create_user(username="bob", password="pw")
        html = _render(user)

        assert "Log in" not in html


class TestSidebarFooterAnonymous:
    """An anonymous request gets the log-in button, never the user menu."""

    @pytest.mark.django_db
    def test_renders_the_log_in_button_theme_control_and_language_control(self):
        html = _render(AnonymousUser())

        assert "Log in" in html
        assert "data-toggle-theme" in html, "the theme control must render"
        assert "showModal()" in html, "the language control must render"

    @pytest.mark.django_db
    def test_does_not_render_the_user_menu(self):
        html = _render(AnonymousUser())

        assert "dropdown-content" not in html, (
            "no user-menu dropdown panel must render for an anonymous request"
        )


class TestSidebarFooterThemeControlIsCompact:
    """The theme control is a square icon button, in either theme configuration.

    Without ``theme.choices`` the switcher normally renders an icon, a
    checkbox and a second icon side by side. That row needs about 77px, and
    the footer spends its width on the user's name instead, so the footer
    asks for the compact form. ``theme.choices`` is empty by package
    default, which makes this the shape most installs get.
    """

    @pytest.mark.django_db
    def test_renders_no_checkbox_when_no_theme_choices_are_configured(self):
        user = get_user_model().objects.create_user(username="carol", password="pw")
        html = _render(user)

        assert 'type="checkbox"' not in html, (
            "the footer's theme control must not render the wide toggle row"
        )
        assert "btn-square" in html, "the theme control must be a square icon button"
        assert "data-toggle-theme" in html, (
            "the compact button must still carry the theme-change binding"
        )
