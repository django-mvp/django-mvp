"""App config for the mounted-app fixture (FS-032)."""

from django.apps import AppConfig


class TestAppMountedConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tests.testapp_mounted"
    label = "testapp_mounted"
    verbose_name = "Test App Mounted Fixture"
