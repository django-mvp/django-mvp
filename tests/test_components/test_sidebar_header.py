"""Tests for the <c-app.sidebar.header> component.

The sidebar header carries the brand icon and the sidebar toggle. In the
icon-rail collapse mode the rail hides label spans, so the brand icon's wrapper
span must be marked to survive that rule — otherwise the collapsed header
renders empty (regression guard for #174).
"""

from django import template
from django.template.context import Context
from django_cotton.compiler_regex import CottonCompiler

compiler = CottonCompiler()


def render(source, **context):
    """Compile a Cotton source string and render it."""
    return template.Template(compiler.process(source)).render(Context(context))


class TestSidebarHeader:
    def test_brand_icon_wrapper_is_marked_to_survive_the_rail(self):
        """The icon wrapper carries mvp-sidebar-brand-icon so the rail keeps it."""
        html = render("<c-app.sidebar.header />")
        assert "mvp-sidebar-brand-icon" in html

    def test_header_renders_toggle_and_brand(self):
        html = render("<c-app.sidebar.header />")
        assert "mvp-sidebar-brand" in html
        assert "mvp-sidebar-toggle" in html
