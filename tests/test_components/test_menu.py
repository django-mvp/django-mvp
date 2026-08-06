"""Tests for the <c-menu> component direction and paging modifiers.

c-menu renders a DaisyUI `menu` list. It stays vertical by default and opts
into a horizontal layout (#181) or DaisyUI's paged mode (#182) through
attributes, never raw utility classes.
"""

from django import template
from django.template.context import Context
from django_cotton.compiler_regex import CottonCompiler

compiler = CottonCompiler()


def render(source, **context):
    """Compile a Cotton source string and render it."""
    return template.Template(compiler.process(source)).render(Context(context))


class TestMenuDirection:
    def test_default_menu_is_vertical(self):
        html = render("<c-menu />")
        assert "menu-horizontal" not in html
        assert "menu-vertical" not in html

    def test_horizontal_menu(self):
        html = render("<c-menu horizontal />")
        assert "menu-horizontal" in html

    def test_responsive_menu_is_vertical_then_horizontal(self):
        html = render('<c-menu responsive="lg" />')
        assert "menu-vertical" in html
        assert "lg:menu-horizontal" in html
