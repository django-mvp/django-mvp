"""Context processors for django-mvp."""

from django.forms import Media
from django.http import HttpRequest
from django.utils.functional import SimpleLazyObject

from .config import MVP_CONFIG
from .mounted import MountedApp


def mvp_config(request: HttpRequest) -> dict:
    """Provide MVP configuration and the current mounted app to all templates.

    Exposes the merged MVP_CONFIG dict as ``mvp_config`` so templates and
    Cotton components can read settings-driven configuration, e.g.
    ``{{ mvp_config.layout.sidebar.breakpoint }}``.

    It also exposes two lazy values that the shell reads. ``mounted_app`` is the
    app to name in the page title and the sidebar's back link, and
    ``mounted_menu`` is the menu the sidebar draws. Each is false when there is
    nothing to name or draw. Nothing is looked up until a template reads one, so
    a page that never asks pays nothing::

        {% if mounted_app %}{{ mounted_app.name }}{% endif %}

    ``icon_stylesheet_url`` is the address of ``MVP_CONFIG["icon_stylesheet"]``,
    by the rule form media uses: a full URL or a path starting with ``/`` stays
    as written, and anything else is a static file path.

    Args:
        request: The current request.

    Returns:
        A dict with "mvp_config", "mounted_app", "mounted_menu" and
        "icon_stylesheet_url".
    """
    icon_stylesheet = MVP_CONFIG["icon_stylesheet"]
    return {
        "mvp_config": MVP_CONFIG,
        "mounted_app": SimpleLazyObject(lambda: MountedApp.shell(request).app),
        "mounted_menu": SimpleLazyObject(lambda: MountedApp.shell(request).menu),
        "icon_stylesheet_url": SimpleLazyObject(
            lambda: icon_stylesheet and Media().absolute_path(str(icon_stylesheet))
        ),
    }
