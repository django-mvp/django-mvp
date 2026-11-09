"""Tests for the log-in button, ``<c-mvp.actions.login>``.

The button sends a signed-out visitor to the sign-in page carrying the page
they were on as ``next``, so signing in returns them there. On the sign-in,
sign-up and sign-out pages it carries no ``next``. Rendered via
tests/login_action.html.
"""

from urllib.parse import parse_qs, urlsplit

import pytest
from bs4 import BeautifulSoup
from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test import RequestFactory, override_settings
from django.urls import include, path, reverse
from django.views.generic import TemplateView


def _signup_urls():
    """A project with a sign-up page registered as ``account_signup``, the name allauth uses."""
    patterns = [
        path("", include("mvp.urls")),
        path("signup/", TemplateView.as_view(template_name="tests/login_action.html"), name="account_signup"),
    ]
    return type("_SignupUrls", (), {"urlpatterns": patterns})


SIGNUP_URLS = _signup_urls()


def _render(path_and_query, request=True):
    if not request:
        return render_to_string("tests/login_action.html")
    req = RequestFactory().get(path_and_query)
    req.user = AnonymousUser()
    return render_to_string("tests/login_action.html", request=req)


def _href(html):
    link = BeautifulSoup(html, "html.parser").select_one("a[href]")
    assert link is not None, "the log-in button must render for a signed-out visitor"
    return urlsplit(link["href"])


class TestLogInButtonCarriesTheCurrentPage:
    def test_the_link_names_the_page_it_was_pressed_on_as_next(self):
        href = _href(_render("/components/?page=2&q=x"))

        assert href.path == reverse("account_login")
        assert parse_qs(href.query) == {"next": ["/components/?page=2&q=x"]}

    def test_the_link_carries_no_next_on_the_sign_in_page(self):
        href = _href(_render(reverse("account_login")))

        assert href.path == reverse("account_login")
        assert href.query == ""

    def test_the_link_carries_no_next_on_the_sign_in_page_with_a_query(self):
        href = _href(_render(reverse("account_login") + "?next=/somewhere/"))

        assert href.query == ""

    @override_settings(ROOT_URLCONF=SIGNUP_URLS)
    def test_the_link_carries_no_next_on_the_sign_up_page(self):
        href = _href(_render(reverse("account_signup")))

        assert href.path == reverse("account_login")
        assert href.query == ""

    def test_the_link_carries_no_next_on_the_sign_out_page(self):
        href = _href(_render(reverse("account_logout")))

        assert href.path == reverse("account_login")
        assert href.query == ""

    def test_without_a_request_the_link_carries_no_next(self):
        href = _href(_render(None, request=False))

        assert href.path == reverse("account_login")
        assert href.query == ""


class TestSigningInFromTheButtonReturnsToThePage:
    @pytest.mark.django_db
    def test_a_visitor_lands_back_on_the_page_they_pressed_it_on(self, client, django_user_model):
        django_user_model.objects.create_user(username="reader", password="pw-for-tests")
        login = _href(_render("/some/page/?tab=2"))

        form = BeautifulSoup(client.get(f"{login.path}?{login.query}").content.decode(), "html.parser")
        next_value = form.select_one('input[name="next"]')["value"]
        response = client.post(
            reverse("account_login"),
            {"username": "reader", "password": "pw-for-tests", "next": next_value},
        )

        assert response.status_code == 302
        assert response.url == "/some/page/?tab=2"
