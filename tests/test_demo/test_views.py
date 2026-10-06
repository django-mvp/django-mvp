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


@pytest.mark.django_db
class TestUtilityClassesView:
    def test_renders_200(self, client):
        response = client.get(reverse("utility-classes"))

        assert response.status_code == 200

    def test_drops_the_markdown_h1_so_the_page_has_one_heading(self, client):
        response = client.get(reverse("utility-classes"))
        content = response.content.decode()

        # The page chrome supplies the heading, so the file's own H1 must not
        # be rendered on top of it.
        assert "Utility Class Reference" not in content
        assert content.count("<h1") == 1


class TestUtilityClassesMenuItem:
    def test_menu_item_resolves_to_the_internal_url(self):
        item = AppMenu.get("utility-classes")

        assert item is not None
        assert item.resolve_url() == reverse("utility-classes")
