"""Tests for the <c-button> component.

`condition` gates the entire component: when false, nothing renders. It
defaults to `True` via a bare c-vars boolean declaration (`condition=True`),
so this also locks in that the bare syntax resolves to the real Python
boolean rather than the string `"True"`/`"False"` (issue #153).
"""

import re

from django import template
from django.template.context import Context
from django_cotton.compiler_regex import CottonCompiler

compiler = CottonCompiler()


def render(source, **context):
    """Compile a Cotton source string and render it."""
    return template.Template(compiler.process(source)).render(Context(context))


class TestButtonCondition:
    """`condition` defaults to True and fully suppresses output when False."""

    def test_default_condition_renders_the_button(self):
        html = render('<c-button text="Save" />')
        assert "<button" in html
        assert "Save" in html

    def test_condition_false_renders_nothing(self):
        html = render('<c-button text="Save" :condition="False" />')
        assert html.strip() == ""


class TestButtonSize:
    """[#328] `size` is the only attribute that changes a button's size.

    `small` and `large` are not declared in `<c-vars>`, so Cotton forwards
    them straight through to the rendered element as bare, invalid HTML
    attributes instead of applying any sizing class.
    """

    def test_size_sm_applies_the_small_class(self):
        html = render('<c-button text="Save" size="sm" />')
        assert "btn-sm" in html

    def test_size_lg_applies_the_large_class(self):
        html = render('<c-button text="Save" size="lg" />')
        assert "btn-lg" in html

    def test_an_undeclared_small_attribute_does_not_size_the_button(self):
        html = render('<c-button text="Save" small />')
        assert "btn-sm" not in html
        assert re.search(r"<button[^>]*\bsmall\b[^>]*>", html), (
            "an undeclared attribute is forwarded verbatim, which is the "
            "defect this test locks in a reproduction of"
        )
