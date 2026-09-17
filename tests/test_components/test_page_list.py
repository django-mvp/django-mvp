"""``<c-page.list>`` renders each row with the template its ``card`` names.

The component declared ``card``, and ``list_view.html`` passed it, but the body
reached past it for a ``list_item_template`` key in the surrounding view
context. So the declared attribute did nothing, and the component could only
work inside a view that happened to set that key — which is the opposite of
the rule that a component is configured through its attributes.
"""

import pytest
from django.template import TemplateDoesNotExist

CARD = "cards/product_card.html"


class TestPageListCard:
    @pytest.mark.django_db
    def test_the_card_attribute_names_the_row_template(
        self, cotton_render_string_soup, product
    ):
        soup = cotton_render_string_soup(
            f'<c-page.list :list="items" card="{CARD}" />',
            context={"items": [product]},
        )

        assert product.name in soup.get_text()

    @pytest.mark.django_db
    def test_the_surrounding_context_no_longer_decides(
        self, cotton_render_string_soup, product
    ):
        """A stale ``list_item_template`` in context must not be reached for.

        It names a template that does not exist, so rendering raises if the
        component still prefers it over its own attribute.
        """
        soup = cotton_render_string_soup(
            f'<c-page.list :list="items" card="{CARD}" />',
            context={"items": [product], "list_item_template": "no/such/card.html"},
        )

        assert product.name in soup.get_text()

    @pytest.mark.django_db
    def test_an_unknown_card_is_not_swallowed(
        self, cotton_render_string_soup, product
    ):
        """The attribute is load-bearing, so a wrong value has to say so."""
        with pytest.raises(TemplateDoesNotExist):
            cotton_render_string_soup(
                '<c-page.list :list="items" card="no/such/card.html" />',
                context={"items": [product]},
            )

    @pytest.mark.django_db
    def test_an_empty_list_draws_the_empty_state_instead(
        self, cotton_render_string_soup
    ):
        soup = cotton_render_string_soup(
            f'<c-page.list :list="items" card="{CARD}" '
            ':empty_state="empty_state" />',
            context={"items": [], "empty_state": {"heading": "Nothing here yet"}},
        )

        assert "Nothing here yet" in soup.get_text()
