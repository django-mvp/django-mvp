"""The system check that warns when the installable app is on but not mounted."""

from django.core import checks
from django.urls import get_script_prefix

from mvp.pwa.resolver import WORKER_URL_NAME, InstallableApp
from mvp.utils import reverse_or_none


class InstallableAppChecks:
    """What turning ``MVP_CONFIG["pwa"]`` on can leave half done."""

    @staticmethod
    def root_include():
        """``mvp.W001``: the worker is not served from the root of the site."""
        url = reverse_or_none(WORKER_URL_NAME)
        if url == get_script_prefix() + "sw.js":
            return []
        return [
            checks.Warning(
                "MVP_CONFIG['pwa'] is on, but mvp.pwa.urls is not "
                "included at the root of the URLconf.",
                hint=(
                    "A service worker only controls pages at or below its own path. "
                    "Add path('', include('mvp.pwa.urls')) to the root URLconf."
                ),
                id="mvp.W001",
            )
        ]


@checks.register()
def check_installable_app(app_configs, **kwargs):
    if not InstallableApp.enabled():
        return []
    return InstallableAppChecks.root_include()
