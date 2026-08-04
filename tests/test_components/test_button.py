"""Tests for the <c-button> component.

`condition` gates the entire component: when false, nothing renders. It
defaults to `True` via a bare c-vars boolean declaration (`condition=True`),
so this also locks in that the bare syntax resolves to the real Python
boolean rather than the string `"True"`/`"False"` (issue #153).
"""

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
