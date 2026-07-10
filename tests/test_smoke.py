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
# Styling docs discoverability (Tailwind/DaisyUI era)
# ---------------------------------------------------------------------------


def test_styling_doc_exists():
    """The styling guide exists and documents the consumer build command."""
    styling = BASE_DIR / "docs" / "styling.md"
    assert styling.exists(), "docs/styling.md must exist — it is the canonical CSS/theming guide."
    content = styling.read_text(encoding="utf-8")
    assert "mvp_tailwind" in content, (
        "docs/styling.md must document the 'python manage.py mvp_tailwind' command "
        "so Tier 2 consumers can find the CSS rebuild path."
    )


def test_readme_references_styling_doc_and_command():
    """README.md points at the styling guide and the mvp_tailwind command."""
    readme = BASE_DIR / "README.md"
    content = readme.read_text(encoding="utf-8")
    assert "mvp_tailwind" in content, (
        "README.md must reference 'manage.py mvp_tailwind' so consumers discover "
        "the CSS rebuild path from the top-level documentation."
    )
    assert "docs/styling.md" in content, "README.md must link to docs/styling.md."


def test_entry_css_imports_packaged_preset():
    """The package's own Tailwind entry uses the same preset shipped to consumers."""
    entry = (BASE_DIR / "assets" / "tailwind.css").read_text(encoding="utf-8")
    assert '@plugin "daisyui";' in entry, (
        "assets/tailwind.css must load the daisyui plugin — its removal once "
        "shipped a stylesheet with no DaisyUI classes at all."
    )
    assert "mvp/tailwind/base.css" in entry, (
        "assets/tailwind.css must import the packaged preset so the shipped "
        "stylesheet and consumer builds share one source of truth."
    )
    assert (BASE_DIR / "mvp" / "tailwind" / "base.css").exists()


# ---------------------------------------------------------------------------
