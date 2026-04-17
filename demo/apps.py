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
        """Initialize the app when Django starts.

        This method is called once Django has finished loading all apps.
        It's the perfect place to import menu definitions and other
        app initialization code.
        """
        # Import menu definitions to register them with AppMenu
        # This must happen in ready() to ensure all apps are loaded
        import contextlib

        with contextlib.suppress(ImportError):
            from . import menus  # noqa: F401

    verbose_name = "Demo"
