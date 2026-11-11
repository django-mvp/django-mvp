"""Tests for ``mvp.models`` — the mixin that gives a user model its preferences field.

Source: mvp/models.py
"""

import os
import subprocess
import sys

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from object_preferences.fields import PreferencesField

from mvp.models import PreferencesMixin


class TestPreferencesMixin:
    def test_the_mixin_is_abstract(self):
        assert PreferencesMixin._meta.abstract

    def test_the_mixin_declares_one_preferences_field(self):
        assert [type(field) for field in PreferencesMixin._meta.local_fields] == [PreferencesField]

    def test_a_concrete_model_using_it_has_exactly_one_preferences_field(self):
        fields = [field for field in get_user_model()._meta.get_fields() if isinstance(field, PreferencesField)]

        assert [field.name for field in fields] == ["preferences"]


class TestDemoUserModel:
    def test_the_demo_user_model_is_the_demo_users_user(self):
        assert get_user_model()._meta.label == "users.User"
        assert issubclass(get_user_model(), PreferencesMixin)

    def test_makemigrations_has_nothing_to_write_for_any_app(self):
        result = subprocess.run(
            [sys.executable, "-m", "django", "makemigrations", "--check", "--dry-run"],
            capture_output=True,
            text=True,
            env={**os.environ, "DJANGO_SETTINGS_MODULE": "tests.settings"},
            check=False,
        )

        assert result.returncode == 0, result.stdout + result.stderr
        assert "No changes detected" in result.stdout

    def test_the_demo_users_app_has_one_migration(self):
        loader = MigrationLoader(None, ignore_no_migrations=True)

        assert [name for app, name in loader.disk_migrations if app == "users"] == ["0001_initial"]

    @pytest.mark.django_db
    def test_preferences_add_no_table_of_their_own(self):
        tables = connection.introspection.table_names()

        assert not [table for table in tables if table.startswith("object_preferences")]
        assert "users_user" in tables
