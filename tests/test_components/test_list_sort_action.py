"""Tests for the <c-mvp.page.list.actions.sort> component.

The options set the ordering through the Alpine value the dropdown wrapper
holds, and a hidden input tied to the filter form carries it to the server.

Source: mvp/templates/cotton/mvp/page/list/actions/sort.html
"""

from bs4 import BeautifulSoup
from django import template
from django.template.context import Context
from django_cotton.compiler_regex import CottonCompiler

compiler = CottonCompiler()

CHOICES = [
    ("name_asc", "Name (A-Z)", "name"),
    ("name_desc", "Name (Z-A)", "-name"),
]


def render(**context):
    """Render the sort action with the view's ordering context."""
    html = template.Template(
        compiler.process("<c-mvp.page.list.actions.sort />")
    ).render(Context(context))
    return BeautifulSoup(html, "html.parser")


class TestSortActionOptions:
    def test_each_choice_is_a_button_that_sets_the_ordering_to_its_key(self):
        soup = render(order_by_choices=CHOICES, current_ordering="")

        options = soup.select("button.ordering-option")
        assert [option["@click"] for option in options] == [
            "value='name_asc'",
            "value='name_desc'",
        ]

    def test_an_option_does_not_submit_a_form_by_itself(self):
        soup = render(order_by_choices=CHOICES, current_ordering="")

        assert {o["type"] for o in soup.select("button.ordering-option")} == {"button"}

    def test_only_the_current_ordering_is_ticked(self):
        soup = render(order_by_choices=CHOICES, current_ordering="name_desc")

        ticked = [
            o["@click"] for o in soup.select("button.ordering-option:has(svg, i)")
        ]
        assert ticked == ["value='name_desc'"]

    def test_the_ordering_reaches_the_filter_form_through_a_hidden_input(self):
        soup = render(order_by_choices=CHOICES, current_ordering="name_asc")

        hidden = soup.select_one("input[type='hidden'][name='o']")
        assert hidden["form"] == "filterForm"
        assert hidden[":value"] == "value"

    def test_the_current_ordering_seeds_the_alpine_value(self):
        soup = render(order_by_choices=CHOICES, current_ordering="name_asc")

        assert "'name_asc'" in soup.select_one("[x-data]")["x-data"]

    def test_nothing_is_drawn_for_a_view_without_ordering(self):
        assert render(current_ordering="").select_one("[x-data]") is None
