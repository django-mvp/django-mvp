"""Installable-app support: the values behind the manifest and the page head."""

from django.templatetags.static import static
from django.urls import get_script_prefix

from mvp.config import MVP_CONFIG
from mvp.utils import reverse_or_none, site_name

MANIFEST_URL_NAME = "mvp-pwa-manifest"
WORKER_URL_NAME = "mvp-pwa-service-worker"

IMAGE_DIRECTORY = "brand/pwa/"
IMAGES = {
    "icon_192": "icon-192.png",
    "icon_512": "icon-512.png",
    "icon_maskable_512": "icon-maskable-512.png",
    "apple_touch_icon": "apple-touch-icon.png",
}


class InstallableApp:
    """Reads ``MVP_CONFIG["pwa"]``, which is on when truthy and may be a dict."""

    @staticmethod
    def enabled():
        return bool(MVP_CONFIG["pwa"])

    @staticmethod
    def theme_color():
        """The configured colour, or ``None`` when there is none."""
        setting = MVP_CONFIG["pwa"]
        return setting.get("theme_color") if isinstance(setting, dict) else None


def resolve(request):
    """Work out every installable-app value for ``request``.

    The manifest view and the page head both read this, so the two cannot
    disagree. ``manifest_url`` and ``worker_url`` are ``None`` when
    ``mvp.pwa.urls`` is not mounted, so a page still renders without them.
    """
    prefix = get_script_prefix()
    name = MVP_CONFIG["site_name"] or site_name(request)
    return {
        "name": name,
        "short_name": MVP_CONFIG["short_name"] or name,
        "start_url": prefix,
        "scope": prefix,
        "theme_color": InstallableApp.theme_color(),
        "manifest_url": reverse_or_none(MANIFEST_URL_NAME),
        "worker_url": reverse_or_none(WORKER_URL_NAME),
        **{key: static(IMAGE_DIRECTORY + file) for key, file in IMAGES.items()},
    }
