"""Tests for the <c-brand.logo> component.

The brand logo must never be stretched: the image keeps its aspect ratio with
`object-contain` and an automatic width, so a consumer sizing it by height (or
dropping it into a constrained box, e.g. an error page) gets a clean logo
rather than a distorted one (regression guard for #183).
"""

from django import template
from django.template.context import Context
from django_cotton.compiler_regex import CottonCompiler

compiler = CottonCompiler()


def render(source, **context):
    """Compile a Cotton source string and render it."""
    return template.Template(compiler.process(source)).render(Context(context))


class TestBrandLogo:
    def test_logo_preserves_aspect_ratio(self):
        html = render("<c-brand.logo />")
        assert "object-contain" in html
        assert "w-auto" in html
        assert "max-w-full" in html

    def test_logo_is_not_forced_to_fill_its_box(self):
        """`h-full` stretched the logo when the parent constrained height."""
        html = render("<c-brand.logo />")
        assert "h-full" not in html

    def test_extra_classes_pass_through(self):
        html = render('<c-brand.logo class="h-16 mb-4" />')
        assert "h-16" in html
        assert "mb-4" in html
