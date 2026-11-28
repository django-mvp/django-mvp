"""Tests for ``mvp.models`` — the mixin that gives a user model its preferences field.

Source: mvp/models.py
"""

import os
import subprocess
import sys

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from object_preferences.fields import PreferencesField


class TestPreferencesMixin:
    def test_a_concrete_model_using_it_has_exactly_one_preferences_field(self):
        fields = [field for field in get_user_model()._meta.get_fields() if isinstance(field, PreferencesField)]

        assert [field.name for field in fields] == ["preferences"]


class TestDemoUserModel:
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

    @pytest.mark.django_db
    def test_preferences_add_no_table_of_their_own(self):
        tables = connection.introspection.table_names()

        assert not [table for table in tables if table.startswith("object_preferences")]
        assert "users_user" in tables
