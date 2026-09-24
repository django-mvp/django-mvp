"""The manifest and the service worker."""

from django.http import JsonResponse
from django.shortcuts import render
from django.templatetags.static import static
from django.urls import get_script_prefix

from mvp.config import MVP_CONFIG
from mvp.pwa import IMAGE_DIRECTORY, IMAGES
from mvp.utils import site_name


def manifest(request):
    """The web app manifest, built from ``MVP_CONFIG`` and the current site."""
    name = MVP_CONFIG["site_name"] or site_name(request)
    prefix = get_script_prefix()
    color = MVP_CONFIG["pwa"]["theme_color"]
    data = {
        "name": name,
        "short_name": MVP_CONFIG["short_name"] or name,
        "start_url": prefix,
        "scope": prefix,
        "display": "standalone",
        "theme_color": color,
        "background_color": color,
        "icons": [
            {
                "src": static(IMAGE_DIRECTORY + IMAGES["icon_192"]),
                "sizes": "192x192",
                "type": "image/png",
            },
            {
                "src": static(IMAGE_DIRECTORY + IMAGES["icon_512"]),
                "sizes": "512x512",
                "type": "image/png",
            },
            {
                "src": static(IMAGE_DIRECTORY + IMAGES["icon_maskable_512"]),
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "maskable",
            },
        ],
    }
    return JsonResponse(data, content_type="application/manifest+json")


def service_worker(request):
    """The packaged worker.

    ``Service-Worker-Allowed`` widens its scope from the folder it is served
    from to the whole site, so it controls every page.
    """
    response = render(request, "mvp/pwa/sw.js", content_type="text/javascript")
    response["Cache-Control"] = "no-cache"
    response["Service-Worker-Allowed"] = get_script_prefix()
    return response
