"""Tests for the <c-page.list.actions.search> list action.

The action wraps a search input and submit button in a single `join`. The
input must render as a bare control (no fieldset legend) so it lines up with
the button and the other page-title widgets — the parent's `label` c-var must
not leak into the inner <c-form.field> (regression guard for #175).
"""

from django import template
from django.template.context import Context
from django_cotton.compiler_regex import CottonCompiler

compiler = CottonCompiler()


def render(source, **context):
    """Compile a Cotton source string and render it."""
    return template.Template(compiler.process(source)).render(Context(context))


class TestListSearchAction:
    def test_search_renders_without_a_fieldset_label(self):
        html = render("<c-page.list.actions.search />", is_searchable=True)
        assert "fieldset" not in html
        assert "fieldset-legend" not in html

    def test_search_input_and_button_share_the_join(self):
        html = render("<c-page.list.actions.search />", is_searchable=True)
        assert "join-item" in html
        assert 'name="q"' in html

    def test_hidden_when_not_searchable(self):
        html = render("<c-page.list.actions.search />", is_searchable=False)
        assert 'name="q"' not in html
