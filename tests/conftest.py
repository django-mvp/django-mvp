"""
Test fixtures for django-cotton-layouts test suite.

This module provides reusable fixtures for testing layout components.
"""


def pytest_configure(config):
    """Apply performance overrides for the test session.

    ``tests/settings.py`` is shared with the dev server (manage.py runserver),
    so expensive settings that are fine for development but hurt test speed are
    overridden here rather than in the settings file itself.

    Runs after pytest-django has called django.setup(), so django.conf.settings
    is safe to modify at this point.
    """
    from django.conf import settings

    # libsass takes ~1.35 s per SCSS file per render; with DummyCache every
    # template render recompiles from scratch.  Tests don't check CSS output.
    settings.COMPRESS_PRECOMPILERS = ()

    # LocMemCache lets django-compressor (and other middleware) cache across
    # requests within the same process, eliminating repeated work per test.
    settings.CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    }
