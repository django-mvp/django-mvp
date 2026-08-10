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
            # Cotton component names rendered in the sidebar footer, in order,
            # e.g. "actions.theme-controller" -> <c-actions.theme-controller />.
            # Laid out as a horizontally centered, wrapping flex row.
            "footer": [],
        },
        "navbar": {
            # Cotton component names rendered at the end (right side) of the navbar,
            # in order, e.g. "actions.theme-controller" -> <c-actions.theme-controller />
            # Configured separately for mobile and desktop (issue #176) so a widget
            # that only makes sense at one screen size doesn't have to be baked
            # responsive by its own author — see _apply_legacy_flat_navbar_config
            # below for the pre-split "navbar.end" shape this replaces.
            "mobile": {"end": ["actions.theme-controller", "actions.login"]},
            "desktop": {"end": ["actions.theme-controller", "actions.login"]},
            # Whether the header sticks to the top of the viewport on scroll.
            # True (default) pins it (app-style); False lets it scroll away with
            # the page (traditional-site behaviour). Applies at every screen size.
            "sticky": True,
        },
    },
}

merge(MVP_CONFIG, getattr(settings, "MVP_CONFIG", {}))


def _apply_legacy_flat_navbar_config(config):
    """Map a flat, pre-#176 ``layout.navbar.end`` override onto both
    ``navbar.mobile.end`` and ``navbar.desktop.end``.

    Before the mobile/desktop split, ``MVP_CONFIG["layout"]["navbar"]["end"]``
    was the only widget list, applied at every screen size. A project's
    ``settings.MVP_CONFIG`` may still set it in that flat shape, and
    ``mergedeep.merge`` above only adds it as a sibling of the new "mobile"/
    "desktop" keys rather than replacing them. Normalize it here so templates
    read one shape: a flat override replaces both breakpoints' lists, exactly
    what it did before the split.
    """
    navbar = config["layout"]["navbar"]
    legacy_end = navbar.pop("end", None)
    if legacy_end is not None:
        navbar["mobile"]["end"] = legacy_end
        navbar["desktop"]["end"] = legacy_end


_apply_legacy_flat_navbar_config(MVP_CONFIG)
