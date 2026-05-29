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


BS5_ICONS = {
    "add": "bi bi-plus-lg",
    "search": "bi bi-search",
    "delete": "bi bi-trash",
    "edit": "bi bi-pencil",
    "plus": "bi bi-plus",
    "minus": "bi bi-dash",
    "sort-asc": "bi bi-arrow-down-short",
    "sort-desc": "bi bi-arrow-up-short",
    "arrow-right": "bi bi-arrow-right",
    "arrow-left": "bi bi-arrow-left",
    "circle": "bi bi-circle",
    "dash": "bi bi-dash-lg",
    "dropdown_check": "bi bi-check-circle-fill",
    "filter": "bi bi-funnel",
    "github": "bi bi-github",
    "globe": "bi bi-globe",
    "home": "bi bi-house",
    "maximize": "bi bi-arrows-fullscreen",
    "minimize": "bi bi-arrows-angle-contract",
    "menu": "bi bi-list",
    "navbar": "bi bi-window",
    "people": "bi bi-people",
    "person": "bi bi-person",
    "settings": "bi bi-gear",
    "sidebar-left": "bi bi-layout-sidebar",
    "sidebar-right": "bi bi-layout-sidebar-reverse",
    "sort": "bi bi-sort-down",
    "table": "bi bi-table",
    "theme.auto": "bi bi-circle-half",
    "theme.dark": "bi bi-moon-stars-fill",
    "theme.light": "bi bi-sun",
    "x": "bi bi-x-lg",
    "check": "bi bi-check-lg",
    "life-preserver": "bi bi-life-preserver",
    "exclamation-circle": "bi bi-exclamation-circle",
    "shield-x": "bi bi-shield-x",
    "bug": "bi bi-bug",
    "logout": "bi bi-box-arrow-right",
}
