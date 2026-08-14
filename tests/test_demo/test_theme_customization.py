"""Tests for demo.views.theme_customization_demo.

Source: demo/settings.py, demo/templates/demo/theme_customization.html

This is FS-026 US-3's demo evidence (SC-002, SC-005): the page a reader checks
docs/theming.md against. The switcher offers the demo's actual configured set
of themes, and no theme definition is requested from a host outside the
project.

The demo used to configure a sixth theme, ``sunrise``, hand-written into
``demo/static/css/theme-sunrise.css`` and linked from the demo's own base
template. It was there to prove a project can add a palette of its own. The
package now ships its own ``mvp`` and ``mvp-dark`` themes and docs/theming.md
teaches the same technique, so the extra file was removed and the two tests
that only asserted its presence went with it (issue #239). The claim worth
keeping — that no theme comes from a third party — is asserted below against
whatever the demo configures.

``tests/settings.py`` deliberately pins a bare ``MVP_CONFIG`` with no
``theme.choices`` (its own docstring: "visual tweaks to the demo don't ripple
into tests"), so these tests apply the demo's real configuration for their own
duration via the same ``monkeypatch.setitem(MVP_CONFIG["theme"], ...)`` seam
``tests/test_components/test_theme_controller.py`` already uses, rather than
hardcoding a second copy of the choices list.
"""

import pytest
from django.urls import reverse

from demo.settings import MVP_CONFIG as DEMO_MVP_CONFIG
from mvp.config import MVP_CONFIG

DEMO_THEME_CHOICES = DEMO_MVP_CONFIG["theme"]["choices"]


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

    def test_the_packaged_themes_are_offered_first(self, client, demo_theme_choices):
        """The demo opens in the brand, so mvp and mvp-dark lead the picker."""
        assert DEMO_THEME_CHOICES[:2] == ["mvp", "mvp-dark"]

    def test_no_theme_definition_comes_from_outside_the_project(
        self, client, demo_theme_choices
    ):
        """SC-002. Every offered theme is defined in the shipped stylesheet."""
        response = client.get(reverse("customization"))
        content = response.content.decode()

        assert "cdn.jsdelivr.net/npm/daisyui" not in content
        assert "css/django-mvp.css" in content, (
            "the page must load the packaged stylesheet, which is where every "
            "offered theme is defined"
        )
