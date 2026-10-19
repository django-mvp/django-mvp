"""Tests for the demo's list pages that place a filterset's fields.

Source: demo/views.py, demo/urls.py, demo/menus.py,
demo/management/commands/generate_dummy_data.py

The demo fails quietly, so these read the rendered page: a field placed in the
toolbar is drawn inside the filter form before the filter modal, a field placed
in the modal is drawn inside it, and a page with nothing left over draws no
modal and no Filter button.
"""

import io
import re

import pytest
from django.core.management import call_command
from django.urls import reverse

from demo.models import Product
from mvp.menus import AppMenu


def _placed_fields(content):
    """Return the field names drawn in the toolbar and in the filter modal."""
    form = content.split('id="filterForm"', 1)[1]
    toolbar, _, modal = form.partition('id="filterModal"')
    toolbar = toolbar.split("</form>", 1)[0]
    modal = modal.split("</dialog>", 1)[0]

    def names(html):
        return list(dict.fromkeys(re.findall(r'name="([^"]+)"', html)))

    return names(toolbar), names(modal)


@pytest.mark.usefixtures("product")
class TestToolbarFiltersOnlyPage:
    def test_draws_every_field_in_the_toolbar(self, client):
        content = client.get(reverse("product-list-quick")).content.decode()

        toolbar, modal = _placed_fields(content)

        assert toolbar == ["q", "status", "is_featured"]
        assert modal == []

    def test_draws_the_sort_in_the_toolbar(self, client):
        content = client.get(reverse("product-list-quick")).content.decode()

        assert re.search(r'name="o"', content.split('id="filterForm"', 1)[1])

    def test_draws_no_filter_modal_and_no_filter_button(self, client):
        content = client.get(reverse("product-list-quick")).content.decode()

        assert 'id="filterModal"' not in content
        assert "filterModal.showModal()" not in content


@pytest.mark.usefixtures("product")
class TestFilterModalOnlyPage:
    def test_draws_every_field_in_the_modal(self, client):
        content = client.get(reverse("product-list-modal-only")).content.decode()

        toolbar, modal = _placed_fields(content)

        assert toolbar == []
        assert modal == [
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

    def test_draws_the_filter_button(self, client):
        content = client.get(reverse("product-list-modal-only")).content.decode()

        assert "filterModal.showModal()" in content


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
