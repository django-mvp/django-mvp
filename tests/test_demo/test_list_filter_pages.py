"""Tests for the demo's list pages that place a filterset's fields.

Source: demo/views.py, demo/urls.py, demo/menus.py,
demo/management/commands/generate_dummy_data.py

The demo fails quietly, so these read the rendered page: a field placed in the
toolbar is drawn inside the filter form, a field placed in the filter panel is
drawn inside it, and a page with nothing left over draws no panel and no
Filters button.
"""

import pytest
from bs4 import BeautifulSoup
from django.urls import reverse


def _placed_fields(content):
    """Return the field names drawn in the toolbar's form and in the filter panel."""
    soup = BeautifulSoup(content, "html.parser")

    def names(element):
        if element is None:
            return []
        return list(
            dict.fromkeys(el["name"] for el in element.find_all(attrs={"name": True}))
        )

    return names(soup.find(id="filterForm")), names(soup.find(id="filters"))


@pytest.mark.usefixtures("product")
class TestToolbarFiltersOnlyPage:
    def test_draws_every_field_in_the_toolbar(self, client):
        content = client.get(reverse("product-list-quick")).content.decode()

        toolbar, panel = _placed_fields(content)

        assert toolbar == ["q", "status", "is_featured"]
        assert panel == []
        assert 'id="filters"' not in content
        assert 'aria-controls="filters"' not in content


@pytest.mark.usefixtures("product")
class TestFilterPanelOnlyPage:
    def test_draws_every_field_in_the_panel(self, client):
        content = client.get(reverse("product-list-panel-only")).content.decode()

        toolbar, panel = _placed_fields(content)

        assert toolbar == []
        assert panel == [
            "q",
            "status",
            "category",
            "is_featured",
            "priority",
            "sku",
            "price_min",
            "price_max",
            "stock_min",
            "stock_max",
            "release_date_after",
            "release_date_before",
            "is_available",
            "o",
        ]
        assert 'aria-controls="filters"' in content
