"""Tests for ``mvp.preferences`` — the start-up check on the user model's preferences field.

Source: mvp/preferences.py

Each case starts Django in a subprocess: the check runs while apps load, and the
test process has already loaded the demo's user model.
"""

import subprocess
import sys
import textwrap

import pytest

SETTINGS = """
SECRET_KEY = "x"
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "object_preferences",
    "mvp",
    {extra_apps}
]
{user_model}
"""

MODELS = {
    "plain": """
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    pass
""",
    "renamed": """
from django.contrib.auth.models import AbstractUser
from object_preferences.fields import PreferencesField

class User(AbstractUser):
    preferences = "a project's own attribute"
    options = PreferencesField()
""",
}

START = """
import sys
sys.path.insert(0, {path!r})
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "project_settings"
import django
django.setup()
from django.contrib.auth import get_user_model
print(get_user_model()._meta.label, get_user_model().__dict__["preferences"])
"""


def start_django(tmp_path, model=None):
    """Run ``django.setup()`` in a subprocess for a project with the given user model.

    Args:
        tmp_path: A directory to write the project into.
        model: A key of ``MODELS`` for a custom user model, or ``None`` for Django's own.

    Returns:
        The finished ``subprocess.CompletedProcess`` with text output.
    """
    if model:
        (tmp_path / "accounts").mkdir()
        (tmp_path / "accounts" / "__init__.py").write_text("")
        (tmp_path / "accounts" / "models.py").write_text(textwrap.dedent(MODELS[model]))
    (tmp_path / "project_settings.py").write_text(
        SETTINGS.format(
            extra_apps='"accounts",' if model else "",
            user_model='AUTH_USER_MODEL = "accounts.User"' if model else "",
        )
    )
    return subprocess.run(
        [sys.executable, "-c", START.format(path=str(tmp_path))],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        check=False,
    )


class TestUserModelCheck:
    @pytest.mark.parametrize("model", [None, "plain"], ids=["djangos-own", "custom-without-field"])
    def test_a_user_model_without_the_field_stops_startup(self, tmp_path, model):
        result = start_django(tmp_path, model)

        assert result.returncode != 0
        assert "ImproperlyConfigured" in result.stderr
        assert "mvp.models.PreferencesMixin" in result.stderr
        assert "PreferencesField" in result.stderr

    def test_the_error_names_the_user_model(self, tmp_path):
        result = start_django(tmp_path, "plain")

        assert "accounts.User" in result.stderr

    def test_a_field_under_another_name_starts_and_leaves_the_preferences_attribute_alone(self, tmp_path):
        result = start_django(tmp_path, "renamed")

        assert result.returncode == 0, result.stderr
        assert "accounts.User a project's own attribute" in result.stdout
