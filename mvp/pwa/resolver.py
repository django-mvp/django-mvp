"""Installable-app support: the values behind the manifest and the page head."""

from django.contrib.sites.shortcuts import get_current_site
from django.templatetags.static import static
from django.urls import NoReverseMatch, get_script_prefix, reverse

from mvp.config import MVP_CONFIG
from mvp.pwa.colors import ThemeColors

MANIFEST_URL_NAME = "mvp-pwa-manifest"
WORKER_URL_NAME = "mvp-pwa-service-worker"

IMAGE_DIRECTORY = "brand/pwa/"
IMAGES = {
    "icon_192": "icon-192.png",
    "icon_512": "icon-512.png",
    "icon_maskable_512": "icon-maskable-512.png",
    "apple_touch_icon": "apple-touch-icon.png",
}


def reverse_or_none(name):
    """The URL for ``name``, or ``None`` when the root include is not mounted."""
    try:
        return reverse(name)
    except NoReverseMatch:
        return None


def resolve(request):
    """Work out every installable-app value for ``request``.

    The manifest view and the page head both read this, so the two cannot
    disagree. ``manifest_url`` and ``worker_url`` are ``None`` when
    ``mvp.pwa.urls`` is not mounted, so a page still renders without them.
    """
    config = MVP_CONFIG["pwa"]
    prefix = get_script_prefix()
    theme_color = ThemeColors.for_theme(MVP_CONFIG["theme"]["default"])
    name = config["name"] or get_current_site(request).name
    return {
        "name": name,
        "short_name": config["short_name"] or name,
        "start_url": config["start_url"] or prefix,
        "scope": prefix,
        "display": config["display"],
        "theme_color": config["theme_color"] or theme_color,
        "background_color": config["background_color"] or theme_color,
        "manifest_url": reverse_or_none(MANIFEST_URL_NAME),
        "worker_url": config["service_worker"] or reverse_or_none(WORKER_URL_NAME),
        **{key: static(IMAGE_DIRECTORY + file) for key, file in IMAGES.items()},
    }
