from django.apps import apps
from django.contrib.staticfiles import finders
from django.templatetags.static import static


def avatar_url(user, height):
    return None


def logo_url(request, height, theme):
    """Default logo resolver.

    Returns brand/logo.svg for light theme. For dark theme, returns
    brand/logo_dark.svg if that asset is present, otherwise falls back
    to brand/logo.svg. Unrecognised themes also fall back to brand/logo.svg.

    Args:
        request: The current HttpRequest, or None (e.g. management commands).
        height: Advisory max image height in pixels. Unused by the default resolver.
        theme: Theme identifier ('light', 'dark', or any other string).

    Returns:
        str: Static URL for the appropriate brand logo asset.
    """
    if theme == "dark" and finders.find("brand/logo_dark.svg"):
        return static("brand/logo_dark.svg")

    return static("brand/logo.svg")


def icon_url(request, height, theme):
    """Default icon resolver.

    Returns brand/icon.svg for light theme and unrecognised themes. For dark
    theme, returns brand/icon_dark.svg if that asset is present, otherwise
    falls back to brand/icon.svg.

    Args:
        request: The current HttpRequest, or None (e.g. management commands).
        height: Advisory max image height in pixels. Unused by the default resolver.
        theme: Theme identifier ('light', 'dark', or any other string).

    Returns:
        str: Static URL for the appropriate brand icon asset.
    """
    if theme == "dark" and finders.find("brand/icon_dark.svg"):
        return static("brand/icon_dark.svg")

    return static("brand/icon.svg")


def app_is_installed(app_name: str) -> bool:
    """
    Check if a Django app is installed.

    Args:
        app_name: The app name or app config label to check for.
                  Can be either the full path (e.g., "crispy_forms")
                  or a label (e.g., "admin").

    Returns:
        bool: True if the app is installed in INSTALLED_APPS, False otherwise.

    Example:
        >>> from mvp.utils import app_is_installed
        >>> CRISPY_FORMS = app_is_installed("crispy_forms")
        >>> if CRISPY_FORMS:
        ...     from crispy_forms.helper import FormHelper
    """
    return apps.is_installed(app_name)


# Comma-separated keys declare several aliases for one icon (expanded by
# django-easy-icons); surrounding whitespace is stripped. Every alias below
# resolves to the same Bootstrap Icons class, keeping the pack flexible for
# callers while grouping synonyms onto single, manageable lines.
BS5_ICONS = {
    # ── Actions ──────────────────────────────────────────────────────────
    "add, plus, create": "bi bi-plus",
    "minus, dash": "bi bi-dash",
    "delete, remove, trash": "bi bi-trash",
    "edit, pencil": "bi bi-pencil",
    "search, find": "bi bi-search",
    "filter": "bi bi-funnel",
    "check, tick": "bi bi-check-lg",
    "x, close": "bi bi-x-lg",
    "share": "bi bi-share",
    "copy-link, link": "bi bi-link-45deg",
    "login": "bi bi-box-arrow-in-right",
    "logout": "bi bi-box-arrow-right",
    # ── Navigation & layout ──────────────────────────────────────────────
    "home, house": "bi bi-house",
    "menu": "bi bi-list",
    "navbar": "bi bi-window",
    "table": "bi bi-table",
    "sidebar-left": "bi bi-layout-sidebar",
    "sidebar-right": "bi bi-layout-sidebar-reverse",
    "maximize": "bi bi-arrows-fullscreen",
    "minimize": "bi bi-arrows-angle-contract",
    "arrow-right": "bi bi-arrow-right",
    "arrow-left": "bi bi-arrow-left",
    # ── Sorting ──────────────────────────────────────────────────────────
    "sort": "bi bi-sort-down",
    "sort-asc": "bi bi-arrow-down-short",
    "sort-desc": "bi bi-arrow-up-short",
    # ── People ───────────────────────────────────────────────────────────
    "person, user, account": "bi bi-person",
    "people, users": "bi bi-people",
    # ── Settings & theme ─────────────────────────────────────────────────
    "settings, gear, cog": "bi bi-gear",
    "theme.auto": "bi bi-circle-half",
    "theme.dark": "bi bi-moon-stars-fill",
    "theme.light": "bi bi-sun",
    # ── Social ───────────────────────────────────────────────────────────
    "github": "bi bi-github",
    "facebook": "bi bi-facebook",
    "twitter": "bi bi-twitter-x",
    "reddit": "bi bi-reddit",
    "pinterest": "bi bi-pinterest",
    "email, envelope": "bi bi-envelope",
    # ── Misc glyphs ──────────────────────────────────────────────────────
    "circle": "bi bi-circle",
    "globe": "bi bi-globe",
    "life-preserver": "bi bi-life-preserver",
    "exclamation-circle": "bi bi-exclamation-circle",
    "shield-x": "bi bi-shield-x",
    "bug": "bi bi-bug",
    # ── Status (keyed to alert/badge variant names so a component can pass
    #    its variant straight through to <c-icon>) ─────────────────────────
    "info": "bi bi-info-circle-fill",
    "success, dropdown_check": "bi bi-check-circle-fill",
    "warning": "bi bi-exclamation-triangle-fill",
    "error": "bi bi-x-circle-fill",
}
