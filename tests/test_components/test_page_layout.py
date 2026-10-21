"""Tests for `<c-mvp.page.layout>` (FS-042, FR-001, FR-012, SC-002).

The layout draws a page's title, content and side panel. With no panel it
draws the title and the content and nothing else, exactly as a page without
one always was; with one, it puts the panel before or after the content by the
panel's own position. These tests give it a bare element in the side slot, so
they say nothing about the panel component itself.

Sources are compiled through the Cotton compiler and invoked as component
tags, as in `test_container.py`.
"""

import pytest
from bs4 import BeautifulSoup
from django import template
from django.template.context import Context
from django_cotton.compiler_regex import CottonCompiler

compiler = CottonCompiler()

HEADER = '<c-slot name="header"><h1 id="title">Title</h1></c-slot>'
CONTENT = '<p id="content">Content</p>'


def render(source, **context):
    html = template.Template(compiler.process(source)).render(Context(context))
    return BeautifulSoup(html, "html.parser")


def side(position="end", inner="panel"):
    return (
        '<c-slot name="side">'
        f'<aside id="panel" data-mvp-side-position="{position}">{inner}</aside>'
        "</c-slot>"
    )


def layout(*parts, attrs=""):
    return f"<c-mvp.page.layout {attrs}>{''.join(parts)}</c-mvp.page.layout>"


def order(soup):
    """Ids of the title, panel and content, in document order."""
    return [el["id"] for el in soup.find_all(id=["title", "panel", "content"])]


class TestPageLayoutWithoutAPanel:
    @pytest.mark.parametrize(
        "side_slot",
        ['<c-slot name="side"></c-slot>', '<c-slot name="side">  \n </c-slot>', ""],
        ids=["empty", "whitespace", "absent"],
    )
    def test_draws_the_title_and_content_with_no_wrapper(self, side_slot):
        soup = render(layout(HEADER, CONTENT, side_slot))

        assert soup.select_one(".mvp-page-layout") is None
        assert order(soup) == ["title", "content"]
        assert [el.name for el in soup.find_all(recursive=False)] == ["h1", "p"]

    def test_class_is_not_drawn_without_a_wrapper(self):
        soup = render(layout(HEADER, CONTENT, attrs='class="extra"'))

        assert soup.select_one(".extra") is None


class TestPageLayoutWithAPanel:
    def test_the_title_comes_first_then_the_content_then_an_end_panel(self):
        soup = render(layout(HEADER, CONTENT, side("end")))

        assert order(soup) == ["title", "content", "panel"]

    def test_a_start_panel_comes_before_the_content_and_after_the_title(self):
        soup = render(layout(HEADER, CONTENT, side("start")))

        assert order(soup) == ["title", "panel", "content"]

    @pytest.mark.parametrize("position", ["start", "end"])
    def test_the_title_and_content_sit_in_their_own_regions(self, position):
        soup = render(layout(HEADER, CONTENT, side(position)))

        wrapper = soup.select_one(".mvp-page-layout")
        assert wrapper.select_one(".mvp-page-header #title") is not None
        assert wrapper.select_one(".mvp-page-main #content") is not None
        assert wrapper.select_one("#panel") is not None

    @pytest.mark.parametrize("position", ["start", "end"])
    def test_text_in_the_panel_naming_a_position_does_not_move_it(self, position):
        other = "end" if position == "start" else "start"
        inner = f'data-mvp-side-position="{other}"'

        soup = render(layout(HEADER, CONTENT, side(position, inner)))

        assert (
            order(soup)
            == {
                "start": ["title", "panel", "content"],
                "end": ["title", "content", "panel"],
            }[position]
        )

    def test_an_attribute_on_a_nested_element_does_not_move_it(self):
        nested = '<div data-mvp-side-position="start"></div>'

        soup = render(layout(HEADER, CONTENT, side("end", nested)))

        assert order(soup) == ["title", "content", "panel"]

    def test_an_empty_header_slot_draws_no_header_wrapper(self):
        soup = render(layout('<c-slot name="header"></c-slot>', CONTENT, side()))

        assert soup.select_one(".mvp-page-header") is None
        assert order(soup) == ["content", "panel"]

    def test_class_reaches_the_wrapper(self):
        soup = render(layout(HEADER, CONTENT, side(), attrs='class="extra"'))

        assert "extra" in soup.select_one(".mvp-page-layout")["class"]
