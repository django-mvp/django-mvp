"""Tests for the demo's list pages that place a filterset's fields.

Source: demo/views.py, demo/urls.py, demo/menus.py,
demo/management/commands/generate_dummy_data.py

The demo fails quietly, so these read the rendered page: a field placed in the
toolbar is drawn inside the filter form, a field placed in the filter panel is
drawn inside it, and a page with nothing left over draws no panel and no
Filters button.
"""

import io
import re

import pytest
from bs4 import BeautifulSoup
from django.core.management import call_command
from django.urls import reverse

from demo.models import Product
from mvp.menus import AppMenu


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

    def test_draws_the_sort_in_the_toolbar(self, client):
        content = client.get(reverse("product-list-quick")).content.decode()

        assert re.search(r'name="o"', content.split('id="filterForm"', 1)[1])

    def test_draws_no_filter_panel_and_no_panel_button(self, client):
        content = client.get(reverse("product-list-quick")).content.decode()

        assert 'id="filters"' not in content
        assert 'aria-controls="filters"' not in content


@pytest.mark.usefixtures("product")
class TestFilterPanelOnlyPage:
    def test_draws_every_field_in_the_panel(self, client):
        content = client.get(reverse("product-list-modal-only")).content.decode()

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

    def test_draws_the_panel_button(self, client):
        content = client.get(reverse("product-list-modal-only")).content.decode()

        assert 'aria-controls="filters"' in content


class TestListFilterPageMenuItems:
    @pytest.mark.parametrize(
        "name", ["product-list-quick", "product-list-modal-only"]
    )
    def test_menu_item_resolves_to_its_page(self, name):
        assert AppMenu.get(name).resolve_url() == reverse(name)


@pytest.mark.django_db
class TestDemoSeedLongName:
    def test_seeds_a_product_whose_name_wraps(self):
        call_command("generate_dummy_data", stdout=io.StringIO())

        longest = max(len(name) for name in Product.objects.values_list("name", flat=True))

        assert longest >= 60
