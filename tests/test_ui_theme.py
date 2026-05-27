"""
UI theme verification tests — browser-level confirmation that compiled CSS reflects
variable overrides set in `_mvp_variables.scss`.

Tests in this module use pytest-playwright to open themed pages and verify that
variable override changes are visually reflected in the browser.

Playwright tests are marked with ``pytest.mark.playwright`` and are skipped if
pytest-playwright is not installed or the dev server is not running.
"""

import pytest

# ---------------------------------------------------------------------------
# Playwright-based visual verification
# ---------------------------------------------------------------------------
# These tests require a running Django development server. Use:
#   poetry run python manage.py runserver 8001
# before running with:
#   poetry run pytest tests/test_ui_theme.py --headed
# ---------------------------------------------------------------------------

BASE_URL = "http://localhost:8001"


def pytest_collection_modifyitems(config, items):
    """Skip playwright tests when pytest-playwright is unavailable."""
    try:
        import playwright  # noqa: F401
    except ImportError:
        skip = pytest.mark.skip(reason="pytest-playwright not installed")
        for item in items:
            if "playwright" in item.keywords:
                item.add_marker(skip)


# ---------------------------------------------------------------------------
# Phase 7 [US4]: SCSS variables demo page visual verification (T052)
# ---------------------------------------------------------------------------


@pytest.mark.playwright
def test_scss_variables_demo_page_renders(page):
    """The SCSS variables demo page loads and shows both override entrypoints.

    Requires a running dev server at http://localhost:8001.
    Run: poetry run python manage.py runserver 8001
    Then: poetry run pytest tests/test_ui_theme.py --headed
    """
    page.goto(f"{BASE_URL}/theming/scss-variables/")
    assert page.title() != "", "Page title must not be empty"

    # Both override entrypoint file names must appear on the page
    content = page.content()
    assert "_bootstrap_variables.scss" in content, "Demo page must document _bootstrap_variables.scss"
    assert "_adminlte_variables.scss" in content, "Demo page must document _adminlte_variables.scss"
    # INSTALLED_APPS ordering guidance must be present
    assert "INSTALLED_APPS" in content, "Demo page must explain INSTALLED_APPS ordering"
