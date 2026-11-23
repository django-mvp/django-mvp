"""Tests for the demo's ``seed_accounts`` command.

Source: demo/management/commands/seed_accounts.py
"""

import pytest
from django.contrib.auth import authenticate, get_user_model
from django.core.management import call_command
from object_preferences.registry import registry


@pytest.mark.django_db
class TestSeedAccounts:
    def test_creates_the_three_accounts_with_their_roles(self):
        call_command("seed_accounts")
        users = {u.username: u for u in get_user_model().objects.all()}
        assert set(users) == {"regular.user", "staff.user", "super.user"}
        assert not users["regular.user"].is_staff
        assert users["staff.user"].is_staff
        assert not users["staff.user"].is_superuser
        assert users["super.user"].is_superuser
        assert users["super.user"].email == "super.user@example.com"

    def test_each_signs_in_with_the_standard_password(self):
        call_command("seed_accounts")
        for username in ("regular.user", "staff.user", "super.user"):
            assert authenticate(username=username, password="password") is not None

    def test_running_twice_resets_rather_than_duplicates(self):
        call_command("seed_accounts")
        call_command("seed_accounts")
        assert get_user_model().objects.count() == 3


@pytest.mark.django_db
class TestSeedAccountsPreferences:
    @staticmethod
    def locale_of(username):
        """What the account's locale group reads as."""
        user = get_user_model().objects.get(username=username)
        locale = dict(registry.get_preferences(user)["locale"])
        locale["timezone"] = str(locale["timezone"])
        return locale

    def test_the_regular_account_has_chosen_a_timezone_and_language(self, settings):
        call_command("seed_accounts")

        locale = self.locale_of("regular.user")
        assert locale["timezone"] != settings.TIME_ZONE
        assert locale["language"] not in ("", None)
        assert locale["language"] in dict(settings.LANGUAGES)

    def test_the_other_accounts_read_the_defaults(self, settings):
        call_command("seed_accounts")

        for username in ("staff.user", "super.user"):
            assert self.locale_of(username) == {
                "timezone": settings.TIME_ZONE,
                "language": "",
            }

    def test_running_twice_keeps_the_choices(self):
        call_command("seed_accounts")
        first = self.locale_of("regular.user")
        call_command("seed_accounts")

        assert self.locale_of("regular.user") == first
