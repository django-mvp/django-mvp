"""App config for the stand-in for an installed app that adds its own preferences (FS-045)."""

from django.apps import AppConfig


class TestAppPreferencesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tests.testapp_preferences"
    label = "testapp_preferences"
    verbose_name = "Test App Preferences Fixture"
