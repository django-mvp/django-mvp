"""Tests for ``mvp.middleware`` — a signed-in person's timezone and language.

Source: mvp/middleware.py
"""

from datetime import UTC, datetime

import pytest
from django.conf.urls.i18n import i18n_patterns
from django.http import HttpResponse
from django.test import Client
from django.urls import path
from django.utils import timezone as dj_timezone
from django.utils import translation

from tests.conftest import urlconf_of

NOON_UTC = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)


def clock(request):
    """Report the hour, the language and a translated word the request renders with."""
    local = dj_timezone.localtime(NOON_UTC)
    return HttpResponse(
        f"{local:%H} {translation.get_language()} {translation.gettext('Password')}"
    )


URLCONF = urlconf_of(path("clock/", clock))
PREFIXED_URLCONF = urlconf_of(
    path("plain/", clock), *i18n_patterns(path("clock/", clock))
)

TOKYO_IN_GERMAN = {"timezone": "Asia/Tokyo", "language": "de"}


@pytest.fixture(autouse=True)
def clock_urlconf(settings):
    settings.ROOT_URLCONF = URLCONF
    settings.LANGUAGES = [("en", "English"), ("de", "German"), ("fr", "French")]
    settings.LANGUAGE_CODE = "en"
    settings.TIME_ZONE = "UTC"


@pytest.fixture
def chosen(user):
    user.preferences = {"locale": TOKYO_IN_GERMAN}
    user.save()
    return user


def signed_in(user):
    client = Client()
    client.force_login(user)
    return client


@pytest.mark.django_db
class TestPreferencesMiddleware:
    def test_times_render_in_the_chosen_timezone(self, chosen):
        response = signed_in(chosen).get("/clock/")

        assert response.content.decode().split()[0] == "21"

    def test_the_page_is_in_the_chosen_language(self, chosen):
        response = signed_in(chosen).get("/clock/", headers={"accept-language": "fr"})

        body = response.content.decode()
        assert body.split()[1] == "de"
        assert "Passwort" in body
        assert response.headers["Content-Language"] == "de"

    def test_a_second_client_signed_in_as_the_same_person_gets_both(self, chosen):
        signed_in(chosen).get("/clock/")

        response = signed_in(chosen).get("/clock/")

        hour, language, *_ = response.content.decode().split()
        assert (hour, language) == ("21", "de")

    def test_a_person_who_chose_nothing_gets_the_defaults_and_negotiated_language(
        self, user
    ):
        response = signed_in(user).get("/clock/", headers={"accept-language": "fr"})

        hour, language, *_ = response.content.decode().split()
        assert (hour, language) == ("12", "fr")

    def test_a_visitor_gets_what_they_get_without_the_middleware(self, chosen):
        response = Client().get("/clock/", headers={"accept-language": "fr"})

        hour, language, *_ = response.content.decode().split()
        assert (hour, language) == ("12", "fr")
        assert response.headers["Content-Language"] == "fr"

    def test_the_timezone_is_deactivated_after_the_response(self, chosen):
        signed_in(chosen).get("/clock/")

        assert dj_timezone.get_current_timezone_name() == "UTC"

    def test_without_locale_middleware_a_visitor_after_a_person_gets_the_default(
        self, chosen, settings
    ):
        settings.MIDDLEWARE = [
            m
            for m in settings.MIDDLEWARE
            if m != "django.middleware.locale.LocaleMiddleware"
        ]
        signed_in(chosen).get("/clock/")

        response = Client().get("/clock/")

        assert response.content.decode().split()[1] == "en"


@pytest.mark.django_db
class TestPreferencesMiddlewareWithLanguagePrefixes:
    @pytest.fixture(autouse=True)
    def prefixed_urlconf(self, settings):
        settings.ROOT_URLCONF = PREFIXED_URLCONF

    def test_the_language_in_the_address_wins_over_the_stored_one(self, chosen):
        response = signed_in(chosen).get("/fr/clock/")

        assert response.status_code == 200
        hour, language, *_ = response.content.decode().split()
        assert (hour, language) == ("21", "fr")
        assert response.headers["Content-Language"] == "fr"

    def test_without_a_prefix_the_stored_language_applies(self, chosen):
        response = signed_in(chosen).get("/plain/")

        assert response.status_code == 200
        assert response.content.decode().split()[1] == "de"
