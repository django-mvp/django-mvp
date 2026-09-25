"""AppConfig for the demo's ``library`` app, a small mounted app."""

from django.apps import AppConfig


class LibraryConfig(AppConfig):
    """Installed so Django finds the app's templates."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "demo.library"
    label = "library"
    verbose_name = "Demo Library"
