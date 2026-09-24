"""The system check that warns when the installable app is on but not mounted."""

from django.core import checks

from mvp.pwa.resolver import WORKER_URL_NAME, InstallableApp
from mvp.utils import reverse_or_none


class InstallableAppChecks:
    """What turning ``MVP_CONFIG["pwa"]`` on can leave half done."""

    @staticmethod
    def urls_mounted():
        """``mvp.W001``: the manifest and worker URLs are not registered."""
        if reverse_or_none(WORKER_URL_NAME) is not None:
            return []
        return [
            checks.Warning(
                "MVP_CONFIG['pwa'] is on, but mvp.urls is not included in the URLconf.",
                hint=(
                    "The manifest and the service worker are served by mvp.urls. "
                    "Add path('account/', include('mvp.urls')) to your URLconf."
                ),
                id="mvp.W001",
            )
        ]


@checks.register()
def check_installable_app(app_configs, **kwargs):
    if not InstallableApp.enabled():
        return []
    return InstallableAppChecks.urls_mounted()
