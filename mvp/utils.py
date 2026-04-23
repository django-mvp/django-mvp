from django.apps import apps


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
    "sort-asc": "bi bi-arrow-down-short",
    "sort-desc": "bi bi-arrow-up-short",
    "arrow-right": "bi bi-arrow-right",
    "arrow-left": "bi bi-arrow-left",
    "circle": "bi bi-circle",
    "dash": "bi bi-dash-lg",
    "dropdown_check": "bi bi-check-circle-fill",
    "filter": "bi bi-funnel",
    "github": "bi bi-github",
    "home": "bi bi-house",
    "maximize": "bi bi-arrows-fullscreen",
    "menu": "bi bi-list",
    "minimize": "bi bi-arrows-angle-contract",
    "navbar": "bi bi-window",
    "people": "bi bi-people",
    "person": "bi bi-person",
    "search": "bi bi-search",
    "settings": "bi bi-gear",
    "sidebar-left": "bi bi-layout-sidebar",
    "sidebar-right": "bi bi-layout-sidebar-reverse",
    "sort": "bi bi-sort-down",
    "table": "bi bi-table",
    "theme_auto": "bi bi-circle-half",
    "theme_dark": "bi bi-moon-stars-fill",
    "theme_light": "bi bi-sun",
}
