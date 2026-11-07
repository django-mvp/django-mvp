"""Tests for ``mvp.views.preferences.set_language`` — the switcher saving a choice.

Source: mvp/views/preferences.py, mvp/urls.py,
mvp/templates/cotton/mvp/actions/language_switcher.html,
mvp/templates/cotton/mvp/actions/language_switcher_modal.html
"""

import pytest
from bs4 import BeautifulSoup
from django.conf import settings as django_settings
from django.contrib.auth.models import AnonymousUser
from django.template import engines
from django.template.loader import render_to_string
from django.test import Client, RequestFactory
from django.urls import reverse
from django.utils import translation
from django_cotton.compiler_regex import CottonCompiler
from object_preferences.registry import registry

URL_NAME = "mvp-set-language"
PAGE = "account-preferences"


def stored(person):
    """What ``person``'s locale group reads as after a fresh read from the database."""
    person.refresh_from_db()
    return dict(registry.get_preferences(person)["locale"])


@pytest.fixture(autouse=True)
def three_languages(settings):
    settings.LANGUAGES = [("en", "English"), ("de", "German"), ("fr", "French")]


@pytest.fixture
def signed_in(client, user):
    client.force_login(user)
    return client


def render_dropdown(user, path="/some/path/"):
    """Draw the dropdown switcher for ``user``."""
    request = RequestFactory().get(path)
    request.user = user
    request.LANGUAGE_CODE = "en"
    source = CottonCompiler().process("<c-mvp.actions.language-switcher />")
    template = engines["django"].from_string(source)
    with translation.override("en"):
        html = template.render({}, request=request)
    return BeautifulSoup(html, "html.parser")


def render_modal(user, path="/some/path/"):
    """Draw the modal switcher for ``user``."""
    request = RequestFactory().get(path)
    request.user = user
    request.LANGUAGE_CODE = "en"
    with translation.override("en"):
        html = render_to_string("tests/language_switcher_modal.html", request=request)
    return BeautifulSoup(html, "html.parser")


@pytest.mark.django_db
class TestSwitchingWhileSignedIn:
    def test_the_choice_becomes_the_stored_language(self, signed_in, user):
        response = signed_in.post(reverse(URL_NAME), {"language": "de", "next": "/"})

        assert response.status_code == 302
        assert stored(user)["language"] == "de"

    def test_the_preferences_page_shows_it(self, signed_in):
        signed_in.post(reverse(URL_NAME), {"language": "fr", "next": "/"})

        response = signed_in.get(reverse(PAGE))

        soup = BeautifulSoup(response.content, "html.parser")
        selected = soup.select_one("select[name='locale-language'] option[selected]")
        assert selected["value"] == "fr"

    def test_the_timezone_is_left_as_it_was(self, signed_in, user):
        user.preferences = {"locale": {"timezone": "Asia/Tokyo", "language": "en"}}
        user.save()

        signed_in.post(reverse(URL_NAME), {"language": "de", "next": "/"})

        assert stored(user) == {"timezone": "Asia/Tokyo", "language": "de"}

    def test_the_cookie_and_the_redirect_are_djangos(self, signed_in):
        response = signed_in.post(
            reverse(URL_NAME), {"language": "de", "next": "/account/"}
        )

        assert response.status_code == 302
        assert response.url == "/account/"
        assert response.cookies[django_settings.LANGUAGE_COOKIE_NAME].value == "de"

    def test_an_address_off_the_site_is_not_followed(self, signed_in):
        response = signed_in.post(
            reverse(URL_NAME), {"language": "de", "next": "https://example.org/"}
        )

        assert response.url != "https://example.org/"

    def test_a_language_the_project_does_not_offer_stores_nothing(
        self, signed_in, user
    ):
        signed_in.post(reverse(URL_NAME), {"language": "xx", "next": "/"})

        assert stored(user)["language"] == ""

    def test_no_language_stores_nothing(self, signed_in, user):
        signed_in.post(reverse(URL_NAME), {"next": "/"})

        assert stored(user)["language"] == ""

    def test_a_project_offering_one_language_stores_nothing_and_does_not_fail(
        self, signed_in, user, settings
    ):
        settings.LANGUAGES = [("en", "English")]

        response = signed_in.post(reverse(URL_NAME), {"language": "en", "next": "/"})

        assert response.status_code == 302
        assert "language" not in stored(user)


@pytest.mark.django_db
class TestSwitchingAsAVisitor:
    def test_the_cookie_is_set_and_nothing_is_stored(self, client, user):
        response = client.post(reverse(URL_NAME), {"language": "de", "next": "/"})

        assert response.status_code == 302
        assert response.cookies[django_settings.LANGUAGE_COOKIE_NAME].value == "de"
        assert stored(user)["language"] == ""


@pytest.mark.django_db
class TestTheRequest:
    def test_get_is_refused(self, signed_in, user):
        response = signed_in.get(reverse(URL_NAME), {"language": "de"})

        assert response.status_code == 405
        assert stored(user)["language"] == ""

    def test_a_post_without_a_csrf_token_is_refused(self, user):
        client = Client(enforce_csrf_checks=True)
        client.force_login(user)

        response = client.post(reverse(URL_NAME), {"language": "de", "next": "/"})

        assert response.status_code == 403
        assert stored(user)["language"] == ""


@pytest.mark.django_db
class TestTheSwitchersChooseTheirAction:
    def test_the_dropdown_posts_to_the_view_for_a_signed_in_person(self, user):
        form = render_dropdown(user).select_one("form")

        assert form["action"] == reverse(URL_NAME)

    def test_the_dropdown_posts_to_djangos_view_for_a_visitor(self):
        form = render_dropdown(AnonymousUser()).select_one("form")

        assert form["action"] == reverse("set_language")

    def test_the_modal_posts_to_the_view_for_a_signed_in_person(self, user):
        form = render_modal(user).select_one("form")

        assert form["action"] == reverse(URL_NAME)

    def test_the_modal_posts_to_djangos_view_for_a_visitor(self):
        form = render_modal(AnonymousUser()).select_one("form")

        assert form["action"] == reverse("set_language")
