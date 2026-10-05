"""Tests for the <c-button> component, which daisy-cotton provides.

What is left here is how a caller's attributes reach it: a declared one sets the
size, and an undeclared one is forwarded to the element verbatim.
"""

import re

from django import template
from django.template.context import Context
from django_cotton.compiler_regex import CottonCompiler

compiler = CottonCompiler()


def render(source, **context):
    """Compile a Cotton source string and render it."""
    return template.Template(compiler.process(source)).render(Context(context))


class TestButtonSize:
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
