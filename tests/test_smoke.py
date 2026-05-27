"""
Smoke tests – quick sanity-checks that the package imports cleanly and
the Django configuration is valid.
"""

from pathlib import Path

import django
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent


def test_django_version():
    """Django is available and meets the minimum version."""
    major, minor, *_ = django.VERSION
    assert (major, minor) >= (4, 2), f"Django {major}.{minor} < 4.2"


@pytest.mark.django_db
def test_mvp_apps_load(client):
    """Django can resolve the root URL without raising configuration errors."""
    response = client.get("/")
    assert response.status_code in {200, 301, 302, 404}


def test_mvp_imports():
    """The published package surface imports without errors."""
    import mvp  # noqa: F401
    from mvp import (
        renderers,  # noqa: F401
        views,  # noqa: F401
    )
    from mvp.templatetags import mvp as mvp_tags  # noqa: F401


# ---------------------------------------------------------------------------
# Phase 5 [US3]: Quickstart command-path validation (T029)
# ---------------------------------------------------------------------------


def test_quickstart_md_exists():
    """The quickstart document exists for new team onboarding."""
    quickstart = BASE_DIR / "specs" / "018-vendor-adminlte-scss" / "quickstart.md"
    assert quickstart.exists(), "specs/018-vendor-adminlte-scss/quickstart.md must exist for new team onboarding."


def test_quickstart_documents_invoke_refresh_command():
    """Quickstart references the correct invoke task name."""
    quickstart = BASE_DIR / "specs" / "018-vendor-adminlte-scss" / "quickstart.md"
    content = quickstart.read_text(encoding="utf-8")
    assert "invoke refresh-adminlte-scss" in content, (
        "quickstart.md must document the 'invoke refresh-adminlte-scss' command "
        "so new teams can run the vendor refresh without searching the codebase."
    )


def test_quickstart_documents_override_file_path():
    """Quickstart references the correct override entrypoint file path."""
    quickstart = BASE_DIR / "specs" / "018-vendor-adminlte-scss" / "quickstart.md"
    content = quickstart.read_text(encoding="utf-8")
    assert "_bootstrap_variables.scss" in content, (
        "quickstart.md must name '_bootstrap_variables.scss' as the override entrypoint "
        "so new developers know which file to edit."
    )


# ---------------------------------------------------------------------------
# Phase 5 [US3]: Documentation snippet consistency (T030)
# ---------------------------------------------------------------------------


def test_readme_references_override_file():
    """README.md mentions _bootstrap_variables.scss in the theming section."""
    readme = BASE_DIR / "README.md"
    content = readme.read_text(encoding="utf-8")
    assert "_bootstrap_variables.scss" in content, (
        "README.md must reference '_bootstrap_variables.scss' so that new teams "
        "discover the override entrypoint from the top-level documentation."
    )


def test_readme_references_invoke_refresh_command():
    """README.md mentions the invoke refresh-adminlte-scss command."""
    readme = BASE_DIR / "README.md"
    content = readme.read_text(encoding="utf-8")
    assert "invoke refresh-adminlte-scss" in content, (
        "README.md must document 'invoke refresh-adminlte-scss' so that "
        "maintainers can find the vendor refresh command from the top-level docs."
    )


def test_override_path_consistent_across_docs():
    """The override entrypoint path is consistent between README and quickstart."""
    readme = BASE_DIR / "README.md"
    quickstart = BASE_DIR / "specs" / "018-vendor-adminlte-scss" / "quickstart.md"

    readme_content = readme.read_text(encoding="utf-8")
    quickstart_content = quickstart.read_text(encoding="utf-8")

    # Both must reference the same file path.
    assert "_bootstrap_variables.scss" in readme_content
    assert "_bootstrap_variables.scss" in quickstart_content
    # Both must reference the same vendored SCSS path.
    assert "mvp/static/adminlte/scss" in quickstart_content, (
        "quickstart.md must reference the canonical vendored SCSS path "
        "'mvp/static/adminlte/scss/' for path consistency."
    )


# ---------------------------------------------------------------------------
# Phase 7 [US4]: SCSS variables demo page accessibility (T051)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_scss_variables_demo_page_accessible(client):
    """The SCSS variables demo page responds with HTTP 200."""
    response = client.get("/theming/scss-variables/")
    assert response.status_code == 200, (
        "The SCSS variables demo page at /theming/scss-variables/ must return HTTP 200. "
        "Check that the URL is registered in demo/urls.py and the view renders without errors."
    )
