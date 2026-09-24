"""The manifest and the service worker."""

from django.http import JsonResponse
from django.shortcuts import render

from mvp.pwa.resolver import resolve


def manifest(request):
    """The web app manifest, built from the same values the page head uses."""
    app = resolve(request)
    data = {
        "name": app["name"],
        "short_name": app["short_name"],
        "start_url": app["start_url"],
        "scope": app["scope"],
        "display": app["display"],
        "icons": [
            {"src": app["icon_192"], "sizes": "192x192", "type": "image/png"},
            {"src": app["icon_512"], "sizes": "512x512", "type": "image/png"},
            {
                "src": app["icon_maskable_512"],
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "maskable",
            },
        ],
    }
    for key in ("theme_color", "background_color"):
        if app[key]:
            data[key] = app[key]
    return JsonResponse(data, content_type="application/manifest+json")


def service_worker(request):
    """The packaged worker, served from the root so it controls every page."""
    response = render(request, "mvp/pwa/sw.js", content_type="text/javascript")
    response["Cache-Control"] = "no-cache"
    return response
