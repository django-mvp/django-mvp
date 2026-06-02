"""
Test fixtures for django-cotton-layouts test suite.

This module provides reusable fixtures for testing layout components.
"""

import pytest


@pytest.fixture(autouse=True)
def disable_compressor(settings):
    settings.COMPRESS_ENABLED = False
    settings.COMPRESS_OFFLINE = False
    # Prevents libsass from executing on uncompressed files
    settings.COMPRESS_PRECOMPILERS = ()
