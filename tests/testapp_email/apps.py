"""App config for the third-party email sender the email tests stand in for (FS-044)."""

from django.apps import AppConfig


class TestAppEmailConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tests.testapp_email"
    label = "testapp_email"
    verbose_name = "Test App Email Fixture"
