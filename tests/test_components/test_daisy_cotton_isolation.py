"""Isolating a call to a daisy-cotton component with Cotton's `only` attribute.

`menu.title` declares `text` with no default, so a call that does not pass `text`
reads a page variable of that name. `only` keeps page variables out of the
component, while content between the tags and in named slots is still rendered with
the page's variables.
"""

from bs4 import BeautifulSoup
from django import template
from django.template.context import Context
from django_cotton.compiler_regex import CottonCompiler

compiler = CottonCompiler()

PAGE_TEXT = "page-text-7f3a"
PAGE_VALUE = "page-value-2c9e"
GIVEN_TEXT = "given-text-5d18"


class TestIsolatedCall:
    def render(self, source, **context):
        html = template.Template(compiler.process(source)).render(Context(context))
        return BeautifulSoup(html, "html.parser")

    def test_a_page_variable_does_not_reach_an_isolated_call(self):
        soup = self.render("<c-menu.title only />", text=PAGE_TEXT)

        assert soup.select_one(".menu-title") is not None
        assert PAGE_TEXT not in str(soup)

    def test_a_page_variable_reaches_a_call_that_is_not_isolated(self):
        soup = self.render("<c-menu.title />", text=PAGE_TEXT)

        assert PAGE_TEXT in soup.select_one(".menu-title").get_text()

    def test_default_slot_content_sees_the_page_variables(self):
        soup = self.render(
            "<c-menu.title only>{{ page_value }}</c-menu.title>",
            text=PAGE_TEXT,
            page_value=PAGE_VALUE,
        )

        assert PAGE_VALUE in soup.select_one(".menu-title").get_text()
        assert PAGE_TEXT not in str(soup)

    def test_named_slot_content_sees_the_page_variables(self):
        soup = self.render(
            '<c-stat only><c-slot name="title">{{ page_value }}</c-slot></c-stat>',
            page_value=PAGE_VALUE,
            title=PAGE_TEXT,
        )

        assert PAGE_VALUE in soup.select_one(".stat-title").get_text()
        assert PAGE_TEXT not in str(soup)

    def test_a_passed_attribute_is_used_and_the_page_variable_is_not(self):
        soup = self.render(f'<c-menu.title text="{GIVEN_TEXT}" only />', text=PAGE_TEXT)

        assert GIVEN_TEXT in soup.select_one(".menu-title").get_text()
        assert PAGE_TEXT not in str(soup)
