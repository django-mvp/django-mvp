"""Tests for ``mvp.preferences`` — the start-up check on the user model's preferences field.

Source: mvp/preferences.py

Each case starts Django in a subprocess: the check runs while apps load, and the
test process has already loaded the demo's user model.
"""

import json
import subprocess
import sys
import textwrap
from pathlib import Path

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
    return subprocess.run(  # noqa: S603 - the interpreter running a script this test wrote
        [sys.executable, "-c", START.format(path=str(tmp_path))],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        check=False,
    )


class TestUserModelCheck:
    @pytest.mark.parametrize(
        "model", [None, "plain"], ids=["djangos-own", "custom-without-field"]
    )
    def test_a_user_model_without_the_field_stops_startup(self, tmp_path, model):
        result = start_django(tmp_path, model)

        assert result.returncode != 0
        assert "ImproperlyConfigured" in result.stderr
        assert "mvp.models.PreferencesMixin" in result.stderr
        assert "PreferencesField" in result.stderr

    def test_the_error_names_the_user_model(self, tmp_path):
        result = start_django(tmp_path, "plain")

        assert "accounts.User" in result.stderr

    def test_a_field_under_another_name_starts_and_leaves_the_preferences_attribute_alone(
        self, tmp_path
    ):
        result = start_django(tmp_path, "renamed")

        assert result.returncode == 0, result.stderr
        assert "accounts.User a project's own attribute" in result.stdout


FULL_SETTINGS = """
from tests.settings import *

INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "demo.users"] + ["accounts"]
AUTH_USER_MODEL = "accounts.User"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
ALLOWED_HOSTS = ["*"]
LANGUAGES = [("en", "English"), ("de", "German")]
"""

USE = """
import sys
sys.path[:0] = [{path!r}, {root!r}]
import os, json
os.environ["DJANGO_SETTINGS_MODULE"] = "project_settings"
import django
django.setup()
from django.core.management import call_command
call_command("migrate", run_syncdb=True, verbosity=0)
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from object_preferences.registry import registry
from tests.testapp_preferences.reading import page_size_for

person = get_user_model().objects.create_user(username="p", password="pw")
client = Client()
client.force_login(person)
page = client.get(reverse("account-preferences"))
saved = client.post(reverse("account-preferences"), {{
    "locale-timezone": "Asia/Tokyo",
    "locale-language": "de",
    "reminders-digest": "daily",
    "reminders-page_size": "50",
}})
after = client.get(reverse("account-center"))
person.refresh_from_db()
print(json.dumps({{
    "page": page.status_code,
    "fields": [n for n in ("locale-timezone", "reminders-digest") if f'name="{{n}}"' in page.content.decode()],
    "saved": saved.status_code,
    "stored": sorted(person.options),
    "language": after.headers["Content-Language"],
    "page_size": page_size_for(person),
    "locale": dict(registry.get_preferences(person)["locale"]),
}}, default=str))
"""


def use_project(tmp_path):
    """Run the preferences page, middleware and test app against a user model with ``options``.

    Args:
        tmp_path: A directory to write the project into.

    Returns:
        The finished ``subprocess.CompletedProcess`` with text output.
    """
    start_django(tmp_path, "renamed")
    (tmp_path / "project_settings.py").write_text(FULL_SETTINGS)
    root = Path(__file__).resolve().parents[1]
    return subprocess.run(  # noqa: S603 - the interpreter running a script this test wrote
        [sys.executable, "-c", USE.format(path=str(tmp_path), root=str(root))],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        check=False,
    )


class TestFieldUnderAnotherName:
    def test_the_page_the_middleware_and_an_apps_group_work_unchanged(self, tmp_path):
        result = use_project(tmp_path)

        assert result.returncode == 0, result.stderr
        seen = json.loads(result.stdout.splitlines()[-1])
        assert seen["page"] == 200
        assert seen["fields"] == ["locale-timezone", "reminders-digest"]
        assert seen["saved"] == 302
        assert set(seen["stored"]) == {"locale", "reminders"}
        assert seen["locale"]["timezone"] == "Asia/Tokyo"
        assert seen["language"] == "de"
        assert seen["page_size"] == 50
