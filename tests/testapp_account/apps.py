"""App config for the Account Center's outside-the-package fixture (US-2)."""

from django.apps import AppConfig


class TestAppAccountConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tests.testapp_account"
    label = "testapp_account"
    verbose_name = "Test App Account Fixture"
