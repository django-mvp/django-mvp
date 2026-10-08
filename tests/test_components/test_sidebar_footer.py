"""Tests for the sidebar footer's fixed composition.

<c-app.sidebar.footer> no longer reads a widget list from settings (docs/adr/
0023): it always renders the user menu or the log-in button (whichever
matches the request), a theme control and a language control. Rendered via
tests/sidebar_footer.html, and tests/sidebar_footer_bg.html where a passed
background is what is under test.
"""

import re

import pytest
from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test import RequestFactory, override_settings
from django.urls import include, path, reverse
from django.utils import translation


def _render(user, template="tests/sidebar_footer.html"):
    request = RequestFactory().get("/some/path/")
    request.user = user
    request.LANGUAGE_CODE = "en"
    with translation.override("en"):
        return render_to_string(template, request=request)


def _mvp_urls_only():
    """A project that mounts only the Account Center — nothing else the
    shell's own controls could fall back to (T008)."""
    patterns = [path("", include("mvp.urls"))]
    return type("_MvpUrlsOnly", (), {"urlpatterns": patterns})


MVP_URLS_ONLY = _mvp_urls_only()


class TestSidebarFooterAuthenticated:
    @pytest.mark.django_db
    def test_renders_the_user_menu_theme_control_and_language_control(self, make_user):
        user = make_user(username="alice")
        html = _render(user)

        assert "alice" in html, "the user menu must show the signed-in user's name"
        assert "data-toggle-theme" in html, "the theme control must render"
        assert "showModal()" in html, "the language control must render"

    @pytest.mark.django_db
    def test_does_not_render_the_log_in_button(self, user):
        html = _render(user)

        assert f'href="{reverse("account_login")}"' not in html


class TestSidebarFooterAnonymous:
    @pytest.mark.django_db
    def test_renders_the_log_in_button_theme_control_and_language_control(self):
        html = _render(AnonymousUser())

        assert f'href="{reverse("account_login")}"' in html
        assert "data-toggle-theme" in html, "the theme control must render"
        assert "showModal()" in html, "the language control must render"

    @pytest.mark.django_db
    def test_does_not_render_the_user_menu(self):
        html = _render(AnonymousUser())

        assert "dropdown-content" not in html, (
            "no user-menu dropdown panel must render for an anonymous request"
        )


class TestSidebarFooterThemeControlIsCompact:
    @pytest.mark.django_db
    def test_renders_no_checkbox_when_no_theme_choices_are_configured(self, user):
        html = _render(user)

        assert 'type="checkbox"' not in html, (
            "the footer's theme control must not render the wide toggle row"
        )
        assert "data-toggle-theme" in html, (
            "the compact button must still carry the theme-change binding"
        )


class TestSidebarFooterTakesTheSidebarsBackground:
    @pytest.mark.django_db
    def test_a_passed_background_replaces_the_default(self):
        html = _render(AnonymousUser(), template="tests/sidebar_footer_bg.html")

        # The component's own element is the first one the fixture renders.
        # Controls inside it carry base colours of their own, so the assertion
        # has to be about this element rather than the whole fragment.
        root = re.search(r"<div class=\"([^\"]*)\"", html)
        assert root is not None, "the footer must render an element of its own"

        classes = root.group(1)
        assert "bg-primary" in classes, (
            f"expected the background it was given, got {classes}"
        )
        assert "bg-base-200" not in classes, (
            f"the default background must not survive alongside it, got {classes}"
        )


class TestSidebarFooterLogInButtonResolvesAccountLogin:
    @pytest.mark.django_db
    def test_an_anonymous_request_draws_the_log_in_button_at_account_login(self):
        with override_settings(ROOT_URLCONF=MVP_URLS_ONLY):
            html = _render(AnonymousUser())

            assert f'href="{reverse("account_login")}"' in html
