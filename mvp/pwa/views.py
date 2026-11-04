"""The manifest, the service worker and the install page."""

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.templatetags.static import static
from django.urls import get_script_prefix
from django.utils.translation import gettext as _

from mvp.config import MVP_CONFIG
from mvp.pwa import IMAGE_DIRECTORY, IMAGES
from mvp.utils import site_name
from mvp.views.base import PageWidth
from mvp.views.extra import MVPTemplateView


def manifest(request: HttpRequest) -> JsonResponse:
    """Return the web app manifest, built from ``MVP_CONFIG`` and the current site.

    Args:
        request: The current request.

    Returns:
        A ``JsonResponse`` with the ``application/manifest+json`` content type.
    """
    name = MVP_CONFIG["site_name"] or site_name(request)
    prefix = get_script_prefix()
    color = MVP_CONFIG["pwa"]["theme_color"]  # type: ignore[index]
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


def service_worker(request: HttpRequest) -> HttpResponse:
    """Return the packaged service worker script.

    ``Service-Worker-Allowed`` widens its scope from the folder it is served
    from to the whole site, so it controls every page.

    Args:
        request: The current request.

    Returns:
        The service worker script response.
    """
    response = render(request, "mvp/pwa/sw.js", content_type="text/javascript")
    response["Cache-Control"] = "no-cache"
    response["Service-Worker-Allowed"] = get_script_prefix()
    return response


class InstallView(MVPTemplateView):
    """The page that tells a visitor how to install the site as an app.

    The instructions for every platform are in the page. The bundled script
    picks out the ones for the device it is open on, shows the browser's own
    install button where the browser offers one, and replaces the page with a
    short message when it is already open in the installed app.
    """

    template_name = "mvp/pwa/install.html"
    page_width = PageWidth.NARROW

    def get_app_name(self) -> str:
        """Return the name the app installs under, as the home screen shows it."""
        return (
            MVP_CONFIG["short_name"]
            or MVP_CONFIG["site_name"]
            or site_name(self.request)
        )

    def get_page_title(self) -> str:
        """Name the app in the title: "Install Open Language"."""
        return _("Install %(name)s") % {"name": self.get_app_name()}

    def get_page_lead(self) -> str:
        """Say what installing gets the visitor."""
        return _(
            "Open it from your home screen or dock, in a window of its own, "
            "like any other app."
        )

    def get_context_data(self, **kwargs):
        """Add the app's name for the instructions."""
        context = super().get_context_data(**kwargs)
        context["app_name"] = self.get_app_name()
        return context
