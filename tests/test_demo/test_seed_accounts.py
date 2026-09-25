"""Tests for the demo's ``seed_accounts`` command.

Source: demo/management/commands/seed_accounts.py
"""

import pytest
from django.contrib.auth import authenticate, get_user_model
from django.core.management import call_command


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
