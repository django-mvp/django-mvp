"""Tests for the <c-page.list.actions.search> component.

Every reader-facing string in the action row is translatable and replaceable
by a caller. The submit button's label was the one exception (issue #282):
it was written as a literal, so a project could only change it by shipping
its own copy of the template.
"""

import re

from django import template
from django.template.context import Context
from django.utils import translation
from django_cotton.compiler_regex import CottonCompiler

compiler = CottonCompiler()


def render(source, **context):
    """Compile a Cotton source string and render it."""
    return template.Template(compiler.process(source)).render(Context(context))


class TestSearchActionButtonLabel:
    """[#282] The submit button's label is an attribute, not a literal."""

    def test_the_default_label_is_translated(self):
        """[#282] With no attribute the label goes through the catalogue."""
        with translation.override("de"):
            html = render(
                "<c-page.list.actions.search />",
                is_searchable=True,
            )
        assert "Suchen" in html
        assert "Search" not in html

    def test_a_caller_can_replace_the_label(self):
        """[#282] The label is replaceable without overriding the template."""
        html = render(
            '<c-page.list.actions.search label="Find products" />',
            is_searchable=True,
        )
        assert "Find products" in html


class TestSearchActionSize:
    """[#328] The search join matches the rest of the small action row: the
    submit button carries the declared `size="sm"`, and the input half of the
    join gets daisyUI's matching `input-sm` (`c-form.field` has no `size`
    attribute, so that goes through its `class`)."""

    def test_the_submit_button_is_small(self):
        html = render("<c-page.list.actions.search />", is_searchable=True)
        assert "btn-sm" in html

    def test_the_input_matches_the_buttons_size(self):
        html = render("<c-page.list.actions.search />", is_searchable=True)
        assert "input-sm" in html

    def test_no_element_carries_a_bare_small_or_large_attribute(self):
        html = render("<c-page.list.actions.search />", is_searchable=True)
        assert not re.search(r"<(button|input)[^>]*\bsmall\b[^>]*>", html)
        assert not re.search(r"<(button|input)[^>]*\blarge\b[^>]*>", html)
