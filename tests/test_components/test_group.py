"""Tests for the <c-group> component.

A flex wrapper that stacks its children in a column by default and switches
to a row under one of two conditions: `row` (always a row) or `collapse`
(a row from the `lg` breakpoint up). Both are plain c-vars, so they must not
pick up an unrelated variable of the same name from the caller's ambient
context (regression for issue #120: django-mvp/base.html sets a `collapse`
context var for the sidebar, and any <c-group> rendered inside that shell
picked it up and silently went horizontal).
"""

from django import template
from django.template.context import Context
from django_cotton.compiler_regex import CottonCompiler

compiler = CottonCompiler()


def render(source, **context):
    """Compile a Cotton source string and render it."""
    return template.Template(compiler.process(source)).render(Context(context))


class TestGroupDefaults:
    """With no attributes and no ambient context, the group is a column."""

    def test_default_is_a_column(self):
        html = render("<c-group>content</c-group>")
        assert "flex-col" in html
        assert "flex-row" not in html
        assert "lg:flex-row" not in html


class TestGroupAttributes:
    """Explicit attributes still control row/collapse behaviour."""

    def test_row_attribute_forces_a_row(self):
        html = render("<c-group row>content</c-group>")
        assert "flex-row" in html
        assert "lg:flex-row" not in html

    def test_collapse_attribute_enables_the_breakpoint_row(self):
        html = render('<c-group :collapse="True">content</c-group>')
        assert "lg:flex-row" in html


class TestGroupAmbientContextIsolation:
    """An unrelated `collapse`/`row` var in the caller's context must not leak in."""

    def test_ambient_collapse_var_is_not_inherited(self):
        """A bare <c-group> ignores a same-named `collapse` var already in
        scope (e.g. the shell's sidebar-mode variable) and stays a column."""
        html = render("<c-group>content</c-group>", collapse="offcanvas")
        assert "lg:flex-row" not in html
        assert "flex-col" in html

    def test_ambient_row_var_is_not_inherited(self):
        html = render("<c-group>content</c-group>", row=True)
        assert "flex-row" not in html
        assert "flex-col" in html
