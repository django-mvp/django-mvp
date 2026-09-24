"""System checks that warn when the installable app is on but not fully set up."""

from django.contrib.staticfiles import finders
from django.core import checks
from django.urls import get_script_prefix

from mvp.config import MVP_CONFIG
from mvp.pwa.resolver import IMAGE_DIRECTORY, IMAGES, WORKER_URL_NAME, reverse_or_none


class InstallableAppChecks:
    """The two ways turning ``MVP_CONFIG["pwa"]`` on can be left half done."""

    @staticmethod
    def root_include():
        """``mvp.W001``: the worker is not served from the root of the site."""
        url = reverse_or_none(WORKER_URL_NAME)
        if url == get_script_prefix() + "sw.js":
            return []
        return [
            checks.Warning(
                "MVP_CONFIG['pwa']['enabled'] is on, but mvp.pwa.urls is not "
                "included at the root of the URLconf.",
                hint=(
                    "A service worker only controls pages at or below its own path. "
                    "Add path('', include('mvp.pwa.urls')) to the root URLconf."
                ),
                id="mvp.W001",
            )
        ]

    @staticmethod
    def images():
        """``mvp.W002``: an image the manifest and page head name is not in static files."""
        missing = [
            IMAGE_DIRECTORY + file
            for file in IMAGES.values()
            if not finders.find(IMAGE_DIRECTORY + file)
        ]
        if not missing:
            return []
        return [
            checks.Warning(
                "MVP_CONFIG['pwa']['enabled'] is on, but these images are missing "
                "from the static files: " + ", ".join(missing) + ".",
                hint="Generate them with: python manage.py mvp_pwa_icons",
                id="mvp.W002",
            )
        ]


@checks.register()
def check_installable_app(app_configs, **kwargs):
    if not MVP_CONFIG["pwa"]["enabled"]:
        return []
    return [*InstallableAppChecks.root_include(), *InstallableAppChecks.images()]
