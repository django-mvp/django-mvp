"""Demo app configuration."""

from django.apps import AppConfig


class DemoConfig(AppConfig):
    """Demo app configuration.

    Automatically loads menu definitions on app startup to populate
    the navigation menu with demo items.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "demo"

    def ready(self):
        """Import menu definitions so they register with AppMenu once apps are loaded."""
        import contextlib

        with contextlib.suppress(ImportError):
            from . import menus  # noqa: F401

    verbose_name = "Demo"
