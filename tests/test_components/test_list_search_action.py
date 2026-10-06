"""Tests for the <c-mvp.page.list.actions.search> component.

Every reader-facing string in the action row is translatable and replaceable
by a caller. The submit button's label was the one exception (issue #282):
it was written as a literal, so a project could only change it by shipping
its own copy of the template.
"""

from bs4 import BeautifulSoup
from django import template
from django.template.context import Context
from django_cotton.compiler_regex import CottonCompiler

compiler = CottonCompiler()


def render(source, **context):
    """Compile a Cotton source string and render it."""
    return template.Template(compiler.process(source)).render(Context(context))


class TestSearchActionButtonLabel:
    def test_a_caller_can_replace_the_label(self):
        html = render(
            '<c-mvp.page.list.actions.search label="Find products" />',
            is_searchable=True,
        )
        assert "Find products" in html


class TestSearchActionControl:
    """The search box stays wired to the shared filter form."""

    def _control(self, **context):
        html = render(
            "<c-mvp.page.list.actions.search />", is_searchable=True, **context
        )
        return BeautifulSoup(html, "html.parser").find("input", attrs={"name": "q"})

    def test_the_control_belongs_to_the_filter_form(self):
        assert self._control()["form"] == "filterForm"

    def test_the_current_query_round_trips_into_the_control(self):
        assert self._control(search_query="blue shoes")["value"] == "blue shoes"

    def test_the_control_has_an_accessible_name(self):
        assert self._control()["aria-label"]

    def test_the_box_is_not_drawn_for_an_unsearchable_view(self):
        html = render("<c-mvp.page.list.actions.search />", is_searchable=False)
        assert 'name="q"' not in html
