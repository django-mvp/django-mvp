"""Tests for demo.views.theme_customization_demo.

Source: demo/settings.py, demo/templates/demo/theme_customization.html

This is FS-026 US-3's demo evidence (SC-002, SC-005): the page a reader checks
docs/theming.md against. No theme definition is requested from a host
outside the project.

Two of the five themes on offer, ``mvp`` and ``mvp-dark``, are the demo's own:
they carry django-mvp's branding, so they live in
``demo/static/css/themes.css`` rather than in the wheel (docs/adr/0016), and
the demo's base template links them alongside the packaged stylesheet. That
makes the page a live worked example of the technique docs/theming.md
describes, which is what a sixth hand-written theme called ``sunrise`` used to
be here for (issue #239). What is asserted below is the page: none of the
themes comes from a third party.

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
    def test_no_theme_definition_comes_from_outside_the_project(
        self, client, demo_theme_choices
    ):
        response = client.get(reverse("customization"))
        content = response.content.decode()

        assert "cdn.jsdelivr.net/npm/daisyui" not in content
        assert "css/django-mvp.css" in content, (
            "the page must load the packaged stylesheet, which is where the "
            "prebuilt themes are defined"
        )
        assert "css/themes.css" in content, (
            "the page must load the demo's own stylesheet, which is where mvp "
            "and mvp-dark are defined — without it the first two entries in "
            "the picker render as an unstyled fallback and nothing raises"
        )
