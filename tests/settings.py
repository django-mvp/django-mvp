"""
Test-specific Django settings.

This module provides a stable, minimal configuration for testing.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent
NPM_BIN_PATH = r"C:\Program Files\nodejs\npm.cmd"
SECRET_KEY = "test-secret-key-for-testing-only"

DEBUG = True

ALLOWED_HOSTS = ["*"]

USE_I18N = True

# Minimal app configuration for testing
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.sites",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "demo",
    "mvp",
    "easy_icons",
    "crispy_forms",
    "crispy_tailwind",
    "flex_menu",
    "django_cotton",
    "django_browser_reload",  # Optional, commented for testing
    "django_watchfiles",
]


# Add django-tables2 if installed (optional dependency)
try:
    import django_tables2  # noqa: F401

    INSTALLED_APPS.append("django_tables2")
except ImportError:
    pass


SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sites.middleware.CurrentSiteMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "django.middleware.locale.LocaleMiddleware",  # MUST be here
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django_browser_reload.middleware.BrowserReloadMiddleware",
]

ROOT_URLCONF = "demo.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "mvp.context_processors.mvp_config",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(BASE_DIR / "db.sqlite3"),  # Use persistent database file
    }
}

AUTH_PASSWORD_VALIDATORS = []

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

STATIC_URL = "/static/"
STATIC_ROOT = str(BASE_DIR / "static")

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

STATICFILES_DIRS = []

STORAGES = {
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


CACHES = {
    "default": {
        # "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
}

CRISPY_ALLOWED_TEMPLATE_PACKS = ["tailwind"]
CRISPY_TEMPLATE_PACK = "tailwind"

# Easy Icons configuration
EASY_ICONS = {
    "default": {
        "renderer": "easy_icons.renderers.ProviderRenderer",
        "config": {"tag": "i"},
        "packs": [
            "mvp.utils.BS5_ICONS",
        ],
        # place icons here that are not critical for the deployed application
        "icons": {
            "add": "bi bi-plus-circle",
            "arrow-left": "bi bi-arrow-left",
            "bicycle": "bi bi-bicycle",
            "book": "bi bi-book",
            "box-seam": "bi bi-box-seam",
            "briefcase": "bi bi-briefcase",
            "calendar-event": "bi bi-calendar-event",
            "calendar": "bi bi-calendar3",
            "cancel": "bi bi-x-lg",
            "cart": "bi bi-cart-fill",
            "check-circle-fill": "bi bi-check-circle-fill",
            "check2-square": "bi bi-check2-square",
            "chevron_right": "bi bi-chevron-right",
            "code-slash": "bi bi-code-slash",
            "cpu": "bi bi-cpu",
            "database-fill": "bi bi-database-fill",
            "documentation": "bi bi-book",
            "dollar": "bi bi-currency-dollar",
            "email": "bi bi-envelope",
            "eye": "bi bi-eye",
            "folder": "bi bi-folder",
            "form": "bi bi-journal-text",
            "graph-up": "bi bi-graph-up-arrow",
            "grid": "bi bi-grid-3x3-gap",
            "gears": "bi bi-gear",
            "heart": "bi bi-heart",
            "home": "bi bi-house",
            "info-circle": "bi bi-info-circle",
            "laptop": "bi bi-laptop",
            "layout-wtf": "bi bi-layout-wtf",
            "layout": "bi bi-layout-text-window-reverse",
            "link": "bi bi-link-45deg",
            "list-ul": "bi bi-list-ul",
            "list": "bi bi-card-list",
            "newspaper": "bi bi-newspaper",
            "notification": "bi bi-bell-fill",
            "person-circle": "bi bi-person-circle",
            "plus": "bi bi-plus-lg",
            "shirt": "bi bi-shirt",
            "sort-desc": "bi bi-sort-down",
            "sidebar-left": "bi bi-layout-sidebar",
            "sidebar-right": "bi bi-layout-sidebar-right",
            "submit": "bi bi-check-lg",
            "support": "bi bi-life-preserver",
            "pencil": "bi bi-pencil",
            "trash": "bi bi-trash",
        },
    },
}

# Flex Menu configuration
FLEX_MENUS = {
    "renderers": {
        "sidebar": "mvp.renderers.SidebarRenderer",
        "dock": "mvp.renderers.MobileFooterNavRenderer",
    },
    "log_url_failures": DEBUG,
}

INTERNAL_IPS = ["127.0.0.1"]
