"""Django app configuration for the mvp package."""

from django.apps import AppConfig
from django.core import checks


class MvpConfig(AppConfig):
    """Django app configuration for Django MVP."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "mvp"
    verbose_name = "Django MVP"

    def ready(self):
        """Register the mounted-apps system check."""
        from .mounted import check_mounted_apps

        checks.register(check_mounted_apps, checks.Tags.urls)
