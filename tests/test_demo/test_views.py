"""Tests for demo.views.UtilityClassesView and its "Utility Classes" menu entry.

Source: demo/views.py, demo/menus.py, demo/urls.py

Renders docs/utility-classes.md inside the demo app so the page behaves like
its sibling component-doc pages instead of linking out to GitHub. The
"Utility Classes" MenuItem is autodiscovered from demo/menus.py during app
startup (django-flex-menus' ``autodiscover_modules("menus")``), so the tree
under ``mvp.menus.AppMenu`` already carries demo's extensions by the time
these tests run.
"""

import pytest
from django.urls import reverse

from mvp.menus import AppMenu

GITHUB_UTILITY_CLASSES_URL = (
    "https://github.com/django-mvp/django-mvp/blob/main/docs/utility-classes.md"
)


@pytest.mark.django_db
class TestUtilityClassesView:
    """The demo app renders docs/utility-classes.md at its own URL."""

    def test_renders_200(self, client):
        response = client.get(reverse("utility-classes"))

        assert response.status_code == 200

    def test_renders_a_known_string_from_the_markdown_file(self, client):
        response = client.get(reverse("utility-classes"))
        content = response.content.decode()

        # Class names from the inventory tables — proof the source file was
        # rendered, not paraphrased.
        assert "grid-cols-{1..12}" in content
        assert "focus-visible:border-error" in content

    def test_drops_the_markdown_h1_so_the_page_has_one_heading(self, client):
        response = client.get(reverse("utility-classes"))
        content = response.content.decode()

        # The page chrome supplies the heading, so the file's own H1 must not
        # be rendered on top of it.
        assert "Utility Class Reference" not in content
        assert content.count("<h1") == 1


class TestUtilityClassesMenuItem:
    """The "Utility Classes" menu entry points at the internal page, not GitHub."""

    def test_menu_item_resolves_to_the_internal_url(self):
        item = AppMenu.get("utility-classes")

        assert item is not None
        assert item.resolve_url() == reverse("utility-classes")

    def test_menu_item_no_longer_links_to_github(self):
        item = AppMenu.get("utility-classes")

        assert item.resolve_url() != GITHUB_UTILITY_CLASSES_URL
