"""App config for the indexed model the search tests use (FS-046)."""

from django.apps import AppConfig


class TestAppSearchConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tests.testapp_search"
    label = "testapp_search"
    verbose_name = "Test App Search Fixture"
