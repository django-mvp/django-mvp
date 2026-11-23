"""Tests for the start-up checks on preferences: ``mvp.E004`` and ``mvp.W006``.

Source: mvp/checks.py
"""

from io import StringIO

import pytest
from django.core import checks
from django.core.checks.registry import registry
from django.core.management import call_command
from django.core.management.base import SystemCheckError

from mvp.checks import (
    check_object_preferences_app,
    check_preferences_middleware,
    object_preferences_app_messages,
    preferences_middleware_messages,
)

AUTHENTICATION = "django.contrib.auth.middleware.AuthenticationMiddleware"
PREFERENCES = "mvp.middleware.PreferencesMiddleware"


class TestObjectPreferencesAppMessages:
    def test_a_missing_app_is_an_error(self):
        messages = object_preferences_app_messages(["mvp"])

        assert [message.id for message in messages] == ["mvp.E004"]
        assert isinstance(messages[0], checks.Error)

    def test_the_hint_names_the_app_and_the_mixin(self):
        (message,) = object_preferences_app_messages(["mvp"])

        assert "object_preferences" in message.hint
        assert "mvp.models.PreferencesMixin" in message.hint

    def test_an_installed_app_passes(self):
        assert object_preferences_app_messages(["mvp", "object_preferences"]) == []


class TestObjectPreferencesAppCheck:
    def test_the_repositorys_own_settings_report_nothing(self):
        assert check_object_preferences_app(None) == []

    def test_the_check_is_registered(self):
        assert check_object_preferences_app in registry.registered_checks

    def test_a_missing_app_stops_the_check_command(self, settings):
        settings.INSTALLED_APPS = [app for app in settings.INSTALLED_APPS if app != "object_preferences"]

        with pytest.raises(SystemCheckError, match=r"mvp\.E004"):
            call_command("check", "mvp", stderr=StringIO())


class TestPreferencesMiddlewareMessages:
    def test_a_missing_middleware_is_a_warning(self):
        messages = preferences_middleware_messages([AUTHENTICATION])

        assert [message.id for message in messages] == ["mvp.W006"]
        assert isinstance(messages[0], checks.Warning)

    def test_the_middleware_before_authentication_is_a_warning(self):
        messages = preferences_middleware_messages([PREFERENCES, AUTHENTICATION])

        assert [message.id for message in messages] == ["mvp.W006"]

    def test_the_hint_names_the_middleware_and_where_it_goes(self):
        (message,) = preferences_middleware_messages([])

        assert PREFERENCES in message.hint
        assert AUTHENTICATION in message.hint

    def test_the_middleware_after_authentication_passes(self):
        assert preferences_middleware_messages([AUTHENTICATION, "x", PREFERENCES]) == []

    def test_the_middleware_without_authentication_passes(self):
        assert preferences_middleware_messages([PREFERENCES]) == []


class TestPreferencesMiddlewareCheck:
    def test_the_check_is_registered(self):
        assert check_preferences_middleware in registry.registered_checks

    def test_a_correct_configuration_reports_nothing(self, settings):
        settings.MIDDLEWARE = [AUTHENTICATION, PREFERENCES]

        assert check_preferences_middleware(None) == []

    def test_a_missing_middleware_is_reported_on_the_check_command(self, settings):
        settings.MIDDLEWARE = [name for name in settings.MIDDLEWARE if name != PREFERENCES]
        err = StringIO()

        call_command("check", "mvp", stderr=err)

        assert "mvp.W006" in err.getvalue()
