"""Tests for the sidebar footer's fixed composition.

<c-app.sidebar.footer> no longer reads a widget list from settings (docs/adr/
0023): it always renders the user menu or the log-in button (whichever
matches the request), a theme control and a language control. Rendered via
tests/sidebar_footer.html, and tests/sidebar_footer_bg.html where a passed
background is what is under test.
"""

import re

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.utils import translation


def _render(user, template="tests/sidebar_footer.html"):
    request = RequestFactory().get("/some/path/")
    request.user = user
    request.LANGUAGE_CODE = "en"
    with translation.override("en"):
        return render_to_string(template, request=request)


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

    @pytest.mark.django_db
    def test_the_log_in_button_fills_the_row_and_carries_emphasis(self):
        """Signing in is the one thing this footer wants a visitor to do."""
        html = _render(AnonymousUser())

        link = re.search(r'<a class="([^"]*)"[^>]*>\s*<span>Log in</span>', html)
        if link is None:
            link = re.search(r'<a class="([^"]*)"[^>]*>(?:(?!</a>).)*Log in', html, re.S)
        assert link is not None, "the log-in button must render as a link"

        classes = link.group(1)
        assert "btn-primary" in classes, f"expected the primary variant, got {classes}"
        assert "btn-block" in classes, f"expected it to fill its row, got {classes}"


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

    @pytest.mark.django_db
    def test_the_theme_and_language_controls_are_the_same_size(self):
        """They sit side by side, so a size on one without the other shows.

        ``c-button`` defaults to its medium size, which is 40px square
        against the theme control's 32px at ``sm``.
        """
        user = get_user_model().objects.create_user(username="dave", password="pw")
        html = _render(user)

        squares = re.findall(r'class="([^"]*\bbtn-square\b[^"]*)"', html)
        assert len(squares) == 2, (
            f"expected the theme and language controls, found {len(squares)} square buttons"
        )
        assert all("btn-sm" in classes for classes in squares), (
            f"both footer controls must render at the same size, got {squares}"
        )


class TestSidebarFooterTakesTheSidebarsBackground:
    """The footer looks like the sidebar it sits in, without being told twice.

    ``<c-app.sidebar>`` hands its own ``bg`` to its header and its footer, so
    repainting the rail is one attribute. A background hard-coded here would
    leave a strip of the old colour across the bottom of a repainted sidebar.
    Anything beyond the colour is an override of this template, by design —
    see docs/adr/0023-the-sidebar-footer-is-a-fixed-composition.md.
    """

    @pytest.mark.django_db
    def test_a_passed_background_replaces_the_default(self):
        html = _render(AnonymousUser(), template="tests/sidebar_footer_bg.html")

        # The component's own element is the first one the fixture renders.
        # Controls inside it carry base colours of their own, so the assertion
        # has to be about this element rather than the whole fragment.
        root = re.search(r"<div class=\"([^\"]*)\"", html)
        assert root is not None, "the footer must render an element of its own"

        classes = root.group(1)
        assert "bg-primary" in classes, f"expected the background it was given, got {classes}"
        assert "bg-base-200" not in classes, (
            f"the default background must not survive alongside it, got {classes}"
        )
