"""Tests for the ``locale`` preference group — a person's timezone and language.

Source: mvp/preferences.py
"""

from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth import get_user_model
from object_preferences.registry import registry

from mvp.preferences import LocalePreferences


def group_form(**data):
    """The locale group's form, bound when ``data`` is given."""
    group = registry.get_group(get_user_model(), "locale")
    return group.form_class(data=data or None)


class TestLocalePreferences:
    def test_is_registered_for_the_user_model_as_locale(self):
        group = registry.get_group(get_user_model(), "locale")

        assert group.form_class is LocalePreferences

    def test_timezone_defaults_to_the_project_timezone(self, settings):
        settings.TIME_ZONE = "Asia/Tokyo"

        assert group_form().fields["timezone"].initial == "Asia/Tokyo"

    def test_language_choices_are_automatic_then_the_projects_languages(self, settings):
        settings.LANGUAGES = [("en", "English"), ("de", "German")]

        field = group_form().fields["language"]

        assert list(field.choices) == [
            ("", "Automatic"),
            ("en", "English"),
            ("de", "German"),
        ]
        assert field.initial == ""
        assert field.required is False

    def test_language_field_is_absent_with_a_single_language(self, settings):
        settings.LANGUAGES = [("en", "English")]

        assert "language" not in group_form().fields

    def test_a_value_outside_the_choices_does_not_validate(self, settings):
        settings.LANGUAGES = [("en", "English"), ("de", "German")]

        form = group_form(timezone="Mars/Olympus", language="xx")

        assert not form.is_valid()
        assert set(form.errors) == {"timezone", "language"}

    def test_automatic_validates(self, settings):
        settings.LANGUAGES = [("en", "English"), ("de", "German")]

        assert group_form(timezone="Europe/Berlin", language="").is_valid()


@pytest.mark.django_db
class TestStoredLocale:
    def test_a_person_who_chose_nothing_reads_the_defaults(self, user, settings):
        settings.TIME_ZONE = "Asia/Tokyo"

        locale = registry.get_preferences(user)["locale"]

        assert locale == {"timezone": ZoneInfo("Asia/Tokyo"), "language": ""}

    def test_a_stored_language_the_project_no_longer_offers_reads_as_automatic(
        self, user, settings
    ):
        settings.LANGUAGES = [("en", "English"), ("de", "German")]
        user.preferences = {"locale": {"timezone": "Europe/Berlin", "language": "fr"}}
        user.save()
        user.refresh_from_db()

        locale = registry.get_preferences(user)["locale"]

        assert locale == {"timezone": ZoneInfo("Europe/Berlin"), "language": ""}


@pytest.mark.django_db
class TestSavedLocale:
    def test_a_chosen_timezone_saves_and_reads_back_as_that_zone(self, user):
        preferences = registry.get_preferences(user)
        preferences.change("locale", timezone="Asia/Tokyo")
        preferences.save()
        user.refresh_from_db()

        assert registry.get_preferences(user)["locale"]["timezone"] == ZoneInfo(
            "Asia/Tokyo"
        )

    def test_choosing_the_default_timezone_stores_nothing(self, user, settings):
        settings.TIME_ZONE = "Europe/Berlin"
        preferences = registry.get_preferences(user)
        preferences.change("locale", timezone="Europe/Berlin")
        preferences.save()
        user.refresh_from_db()

        assert "timezone" not in preferences.stored.get("locale", {})
