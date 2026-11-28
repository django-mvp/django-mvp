"""Tests for demo.views.UtilityClassesView.

Source: demo/views.py, demo/urls.py

Renders docs/utility-classes.md inside the demo app so the page behaves like
its sibling component-doc pages instead of linking out to GitHub.
"""

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestUtilityClassesView:
    def test_drops_the_markdown_h1_so_the_page_has_one_heading(self, client):
        response = client.get(reverse("utility-classes"))
        content = response.content.decode()

        # The page chrome supplies the heading, so the file's own H1 must not
        # be rendered on top of it.
        assert content.count("<h1") == 1
