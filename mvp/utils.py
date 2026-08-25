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
#
# Classes are checked against the pinned Bootstrap Icons release
# (mvp/templates/mvp/base.html) in tests/test_utils.py, against a vendored
# name list at tests/fixtures/bootstrap-icons-1.13.1-names.txt. Bumping that
# template's version means regenerating the fixture from the matching
# https://cdn.jsdelivr.net/npm/bootstrap-icons@<version>/font/bootstrap-icons.json.
BS5_ICONS = {
    # ── Actions ──────────────────────────────────────────────────────────
    "add, plus, create": "bi bi-plus",
    "minus, dash": "bi bi-dash",
    "delete, remove, trash": "bi bi-trash",
    "edit, pencil": "bi bi-pencil",
    "copy, duplicate, clone": "bi bi-copy",
    "search, find": "bi bi-search",
    "filter": "bi bi-funnel",
    "check, tick, confirm": "bi bi-check-lg",
    "x, close, cancel": "bi bi-x-lg",
    "share": "bi bi-share",
    "copy-link, link": "bi bi-link-45deg",
    "login": "bi bi-box-arrow-in-right",
    "logout": "bi bi-box-arrow-right",
    "save": "bi bi-save2",
    "print": "bi bi-printer",
    "view, preview, eye": "bi bi-eye",
    "hide, eye-slash": "bi bi-eye-slash",
    "import, upload": "bi bi-upload",
    "export, download": "bi bi-download",
    "refresh, reload, sync": "bi bi-arrow-clockwise",
    "undo": "bi bi-arrow-counterclockwise",
    "archive": "bi bi-archive",
    "drag, move, grip": "bi bi-grip-vertical",
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
    "chevron-up": "bi bi-chevron-up",
    "chevron-down": "bi bi-chevron-down",
    "chevron-left": "bi bi-chevron-left",
    "chevron-right": "bi bi-chevron-right",
    "expand, chevron-expand": "bi bi-chevron-expand",
    "collapse, chevron-contract": "bi bi-chevron-contract",
    "grid-view, grid": "bi bi-grid-3x3-gap",
    "list-view": "bi bi-view-list",
    "more, options, kebab": "bi bi-three-dots-vertical",
    "external-link": "bi bi-box-arrow-up-right",
    # ── Sorting ──────────────────────────────────────────────────────────
    # A sort control that is not currently sorting anything uses "sort"; the
    # directional pair is for a header that is showing the direction it sorted
    # by, so each has to point the way it reads.
    "sort": "bi bi-sort-down",
    "sort-asc": "bi bi-arrow-up-short",
    "sort-desc": "bi bi-arrow-down-short",
    # ── People ───────────────────────────────────────────────────────────
    "person, user, account": "bi bi-person",
    "people, users": "bi bi-people",
    # ── Settings & theme ─────────────────────────────────────────────────
    "settings, gear, cog, gears": "bi bi-gear",
    "theme.auto": "bi bi-circle-half",
    "theme.dark": "bi bi-moon-stars-fill",
    "theme.light": "bi bi-sun",
    # ── Communication ────────────────────────────────────────────────────
    "email, envelope": "bi bi-envelope",
    "phone, telephone": "bi bi-telephone",
    "chat, message, comment": "bi bi-chat-dots",
    "notification, bell": "bi bi-bell",
    "attachment, paperclip": "bi bi-paperclip",
    # ── Time & location ──────────────────────────────────────────────────
    "calendar, date": "bi bi-calendar",
    "clock, time": "bi bi-clock",
    "location, map, map-pin": "bi bi-geo-alt",
    # ── Files & media ────────────────────────────────────────────────────
    "document, file": "bi bi-file-earmark",
    "folder": "bi bi-folder",
    "image, photo": "bi bi-image",
    "video": "bi bi-camera-video",
    "audio, music": "bi bi-music-note-beamed",
    "pdf": "bi bi-file-earmark-pdf",
    "database": "bi bi-database",
    "cloud": "bi bi-cloud",
    # ── Security ─────────────────────────────────────────────────────────
    "lock, locked": "bi bi-lock",
    "unlock, unlocked": "bi bi-unlock",
    "key, password": "bi bi-key",
    # ── Social ───────────────────────────────────────────────────────────
    "github": "bi bi-github",
    "facebook": "bi bi-facebook",
    "twitter": "bi bi-twitter-x",
    "reddit": "bi bi-reddit",
    "pinterest": "bi bi-pinterest",
    "linkedin": "bi bi-linkedin",
    "youtube": "bi bi-youtube",
    "instagram": "bi bi-instagram",
    "whatsapp": "bi bi-whatsapp",
    "telegram": "bi bi-telegram",
    "mastodon": "bi bi-mastodon",
    "bluesky": "bi bi-bluesky",
    "discord": "bi bi-discord",
    "slack": "bi bi-slack",
    # ── Misc glyphs ──────────────────────────────────────────────────────
    "circle": "bi bi-circle",
    "globe": "bi bi-globe",
    "life-preserver": "bi bi-life-preserver",
    "exclamation-circle": "bi bi-exclamation-circle",
    "shield-x": "bi bi-shield-x",
    "bug": "bi bi-bug",
    "help, question": "bi bi-question-circle",
    "star, favorite": "bi bi-star",
    "bookmark": "bi bi-bookmark",
    # ── Status (keyed to alert/badge variant names so a component can pass
    #    its variant straight through to <c-icon>) ─────────────────────────
    "info": "bi bi-info-circle-fill",
    "success, dropdown_check": "bi bi-check-circle-fill",
    "warning": "bi bi-exclamation-triangle-fill",
    "error": "bi bi-x-circle-fill",
}
