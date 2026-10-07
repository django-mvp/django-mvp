"""Tests for the width `<c-mvp.container>` gives a page (issue #501).

`width` takes one of the names in `mvp.views.base.PageWidth`, and a view's
`page_width` reaches the packaged page templates through it. Tailwind's
`container` class is the one that steps with the breakpoints, so it marks the
wide width and no other.

Sources are compiled through the Cotton compiler and invoked as component
tags, as in `test_entrance.py`.
"""

import pytest
from bs4 import BeautifulSoup
from django import template
from django.template.context import Context
from django_cotton.compiler_regex import CottonCompiler

from mvp.views.base import PageWidth

compiler = CottonCompiler()


def container_classes(source, **context):
    """The class list of the container a Cotton source string renders."""
    html = template.Template(compiler.process(source)).render(Context(context))
    return BeautifulSoup(html, "html.parser").find("div")["class"]


class TestContainerWidth:
    def test_a_container_is_wide_unless_it_says_otherwise(self):
        assert container_classes("<c-mvp.container>x</c-mvp.container>") == (
            container_classes('<c-mvp.container width="wide">x</c-mvp.container>')
        )

    def test_only_the_wide_width_steps_with_the_breakpoints(self):
        stepped = {
            width
            for width in PageWidth
            if "container"
            in container_classes(
                f'<c-mvp.container width="{width}">x</c-mvp.container>'
            )
        }
        assert stepped == {PageWidth.WIDE}

    def test_every_width_renders_its_own_classes(self):
        rendered = {
            " ".join(
                container_classes(
                    f'<c-mvp.container width="{width}">x</c-mvp.container>'
                )
            )
            for width in PageWidth
        }
        assert len(rendered) == len(PageWidth)

    @pytest.mark.parametrize("width", list(PageWidth))
    def test_a_width_from_the_context_matches_the_written_name(self, width):
        assert container_classes(
            '<c-mvp.container :width="width">x</c-mvp.container>', width=width
        ) == container_classes(
            f'<c-mvp.container width="{width.value}">x</c-mvp.container>'
        )

    def test_fill_ignores_the_width(self):
        assert container_classes(
            '<c-mvp.container fill width="narrow">x</c-mvp.container>'
        ) == container_classes("<c-mvp.container fill>x</c-mvp.container>")

    def test_extra_classes_are_kept(self):
        assert "py-4" in container_classes(
            '<c-mvp.container width="narrow" class="py-4">x</c-mvp.container>'
        )
