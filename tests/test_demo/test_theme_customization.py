"""Tests for demo.views.theme_customization_demo.

Source: demo/settings.py, demo/templates/base.html,
demo/templates/demo/theme_customization.html, demo/static/css/theme-sunrise.css

This is FS-026 US-3's demo evidence (SC-002, SC-005): the page a reader checks
docs/theming.md against. The switcher offers the demo's actual configured set
of themes, which mixes shipped themes with "sunrise", a project-written custom
theme, and no theme definition is requested from a host outside the project.

``tests/settings.py`` deliberately pins a bare ``MVP_CONFIG`` with no
``theme.choices`` (its own docstring: "visual tweaks to the demo don't ripple
into tests"), so these tests apply the demo's real configuration for their own
duration via the same ``monkeypatch.setitem(MVP_CONFIG["theme"], ...)`` seam
``tests/test_components/test_theme_controller.py`` already uses, rather than
hardcoding a second copy of the choices list.
"""

import pytest
from django.urls import reverse

from demo.settings import BASE_DIR
from demo.settings import MVP_CONFIG as DEMO_MVP_CONFIG
from mvp.config import MVP_CONFIG

DEMO_THEME_CHOICES = DEMO_MVP_CONFIG["theme"]["choices"]
CUSTOM_THEME_NAME = "sunrise"
CUSTOM_THEME_CSS = BASE_DIR / "demo" / "static" / "css" / "theme-sunrise.css"


@pytest.fixture
def demo_theme_choices(monkeypatch):
    monkeypatch.setitem(MVP_CONFIG["theme"], "choices", DEMO_THEME_CHOICES)


@pytest.mark.django_db
class TestThemeCustomizationDemoPage:
    """The demo's theme page, exercised under the demo's own theme config."""

    def test_renders_200(self, client, demo_theme_choices):
        response = client.get(reverse("customization"))

        assert response.status_code == 200

    def test_switcher_offers_every_configured_theme(self, client, demo_theme_choices):
        assert DEMO_THEME_CHOICES, (
            "demo.settings.MVP_CONFIG must configure theme.choices for this "
            "test to mean anything"
        )
        response = client.get(reverse("customization"))
        content = response.content.decode()

        for theme in DEMO_THEME_CHOICES:
            assert f'data-set-theme="{theme}"' in content, (
                f'the switcher is missing an entry for "{theme}", one of '
                "the demo's configured theme.choices"
            )

    def test_switcher_includes_a_project_written_custom_theme(
        self, client, demo_theme_choices
    ):
        response = client.get(reverse("customization"))
        content = response.content.decode()

        assert f'data-set-theme="{CUSTOM_THEME_NAME}"' in content

    def test_custom_theme_stylesheet_is_self_hosted_not_a_cdn(
        self, client, demo_theme_choices
    ):
        response = client.get(reverse("customization"))
        content = response.content.decode()

        assert "css/theme-sunrise.css" in content, (
            "the custom theme's stylesheet must be linked from the page"
        )
        assert "cdn.jsdelivr.net/npm/daisyui" not in content, (
            "no theme definition may be requested from a host outside the "
            "project (SC-002)"
        )

    def test_custom_theme_stylesheet_defines_its_own_theme_block(self):
        css = CUSTOM_THEME_CSS.read_text(encoding="utf-8")

        assert f'[data-theme="{CUSTOM_THEME_NAME}"]' in css
        assert "--color-primary" in css
