"""Context processors for django-mvp."""

from django.utils.functional import SimpleLazyObject

from .config import MVP_CONFIG
from .mounted import MountedApp


def mvp_config(request):
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
    """

    return {
        "mvp_config": MVP_CONFIG,
        "mounted_app": SimpleLazyObject(lambda: MountedApp.shell(request).app),
        "mounted_menu": SimpleLazyObject(lambda: MountedApp.shell(request).menu),
    }
