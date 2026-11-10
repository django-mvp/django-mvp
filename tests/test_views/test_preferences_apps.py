"""Tests for a preference group declared by an installed app, on the Account Center's preferences page.

Source: mvp/views/preferences.py, tests/testapp_preferences/preferences.py
"""

import pytest
from bs4 import BeautifulSoup
from django.urls import reverse
from object_preferences.registry import registry

from tests.testapp_preferences.reading import page_size_for

URL_NAME = "account-preferences"


def values(**overrides):
    """A valid submission of both groups, with ``overrides`` applied."""
    data = {
        "locale-timezone": "Asia/Tokyo",
        "locale-language": "de",
        "reminders-digest": "daily",
        "reminders-page_size": "50",
    }
    return {**data, **overrides}


@pytest.fixture(autouse=True)
def three_languages(settings):
    settings.LANGUAGES = [("en", "English"), ("de", "German"), ("fr", "French")]


@pytest.fixture
def signed_in(client, user):
    client.force_login(user)
    return client


def reread(person):
    """``person``'s preferences after a fresh read from the database."""
    person.refresh_from_db()
    return registry.get_preferences(person)


@pytest.mark.django_db
class TestAnInstalledAppsGroup:
    def test_the_group_is_a_fieldset_of_its_own_beside_locale(self, signed_in):
        response = signed_in.get(reverse(URL_NAME))

        assert list(response.context["forms"]) == ["locale", "reminders"]
        soup = BeautifulSoup(response.content, "html.parser")
        fieldsets = soup.select_one("main form").find_all("fieldset", recursive=False)
        assert len(fieldsets) == 2
        assert fieldsets[1].select_one("[name='reminders-digest']") is not None
        assert fieldsets[0].select_one("[name='reminders-digest']") is None

    def test_changing_both_groups_saves_both(self, signed_in, user):
        response = signed_in.post(reverse(URL_NAME), values())

        assert response.status_code == 302
        preferences = reread(user)
        assert str(preferences["locale"]["timezone"]) == "Asia/Tokyo"
        assert preferences["reminders"]["digest"] == "daily"
        assert preferences["reminders"]["page_size"] == 50

    def test_an_invalid_value_in_the_apps_group_saves_nothing_in_either(
        self, signed_in, user, settings
    ):
        response = signed_in.post(
            reverse(URL_NAME), values(**{"reminders-page_size": "1"})
        )

        assert response.status_code == 200
        assert response.context["forms"]["reminders"].has_error("page_size")
        assert not response.context["forms"]["locale"].errors
        preferences = reread(user)
        assert str(preferences["locale"]["timezone"]) == settings.TIME_ZONE
        assert preferences["reminders"]["digest"] == "weekly"

    def test_the_error_is_marked_inside_the_apps_fieldset(self, signed_in):
        response = signed_in.post(
            reverse(URL_NAME), values(**{"reminders-page_size": "1"})
        )

        soup = BeautifulSoup(response.content, "html.parser")
        fieldsets = soup.select_one("main form").find_all("fieldset", recursive=False)
        assert fieldsets[1].select("[aria-invalid='true']")
        assert not fieldsets[0].select("[aria-invalid='true']")

    def test_the_app_reads_the_default_until_the_person_chooses(self, user):
        assert page_size_for(user) == 20

    def test_the_app_reads_what_the_person_saved(self, signed_in, user):
        signed_in.post(reverse(URL_NAME), values())

        user.refresh_from_db()
        assert page_size_for(user) == 50
