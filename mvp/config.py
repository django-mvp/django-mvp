"""Package configuration for django-mvp.

MVP_CONFIG is the single source of truth for all package settings. It is built by
deep-merging package defaults with user overrides from ``settings.MVP_CONFIG``.
Consumers import it directly::

    from mvp.config import MVP_CONFIG

"""

from django.conf import settings
from mergedeep import merge  # type: ignore[import-untyped]

MVP_CONFIG = {
    "view_names": {
        "list": "{model_name}-list",
        "detail": "{model_name}-detail",
        "create": "{model_name}-create",
        "update": "{model_name}-update",
        "delete": "{model_name}-delete",
    },
    "brand": {
        "avatar_resolver": "mvp.utils.avatar_url",
        "logo_resolver": "mvp.utils.logo_url",
        "icon_resolver": "mvp.utils.icon_url",
    },
    "layout": {
        "sidebar": {
            # Tailwind breakpoint at which the sidebar becomes persistent
            # (below it, the sidebar is a mobile drawer):
            # sm | md | lg | xl | 2xl | never
            # "never" keeps the sidebar an off-canvas overlay at every width.
            "breakpoint": "lg",
            # How the sidebar collapses when toggled at or above the breakpoint:
            # "offcanvas" (slides fully away) or "icons" (collapses to an icon rail)
            "collapse": "offcanvas",
            # Text shown beside the brand icon in the sidebar header. Falsey
            # (the default) renders no title. Hidden while collapsed to an icon rail.
            "title": None,
        },
        "navbar": {
            # Cotton component names rendered at the end (right side) of the navbar,
            # in order, e.g. "actions.theme-controller" -> <c-actions.theme-controller />
            "end": ["actions.theme-controller", "actions.login"],
            # Whether the header sticks to the top of the viewport on scroll.
            # True (default) pins it (app-style); False lets it scroll away with
            # the page (traditional-site behaviour).
            "sticky": True,
        },
    },
}

merge(MVP_CONFIG, getattr(settings, "MVP_CONFIG", {}))
