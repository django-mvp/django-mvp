"""Django app configuration for the mvp package."""

from django.apps import AppConfig
from django.conf import settings
from django.core import checks
from django.utils.module_loading import autodiscover_modules


class MvpConfig(AppConfig):
    """Django app configuration for Django MVP."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "mvp"
    verbose_name = "Django MVP"

    def ready(self):
        """Register the system checks, and find the apps' email previews while ``DEBUG`` is on."""
        from .checks import (
            check_daisy_cotton_app,
            check_email_brand,
            check_page_title_layout,
        )
        from .mounted import check_mounted_apps

        checks.register(check_mounted_apps, checks.Tags.urls)
        checks.register(check_daisy_cotton_app)
        checks.register(check_page_title_layout)
        checks.register(check_email_brand)

        if settings.DEBUG:
            autodiscover_modules("email_previews")
