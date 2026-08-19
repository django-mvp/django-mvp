"""Tests for the shipped pytest plugin (``mvp.fixtures``).

``mvp/fixtures.py`` is registered as a ``pytest11`` entry point, so pytest
imports it at startup for every project that installs django-mvp. That makes it
public API of the package, and it is the one module a consumer runs before any
of their own code. These tests exercise all four fixtures against real packaged
components.

Coverage note: pytest imports plugin modules during its own bootstrap, before
pytest-cov starts measuring, so the fixture bodies are attributed to this file's
calls rather than to ``mvp/fixtures.py`` import time. The assertions below are
what proves the plugin works.
"""

import pytest

from mvp.fixtures import _beautiful_soup


class TestCottonRender:
    """The raw-HTML component renderer."""

    def test_renders_a_packaged_component(self, cotton_render):
        html = cotton_render("card", title="Quarterly report")
        assert "Quarterly report" in html

    def test_context_dict_and_kwargs_both_reach_the_component(self, cotton_render):
        from_kwargs = cotton_render("card", title="From kwargs")
        from_context = cotton_render("card", {"title": "From context"})
        assert "From kwargs" in from_kwargs
        assert "From context" in from_context


class TestCottonRenderSoup:
    """The component renderer that returns parsed HTML."""

    def test_returns_a_traversable_document(self, cotton_render_soup):
        soup = cotton_render_soup("card", title="Parsed card")
        assert soup.find(string=lambda s: "Parsed card" in s) is not None

    def test_find_all_sees_rendered_elements(self, cotton_render_soup):
        soup = cotton_render_soup("grid", md="2")
        assert soup.find("div") is not None


class TestCottonRenderString:
    """The inline-template renderer."""

    def test_renders_inline_component_markup(self, cotton_render_string):
        html = cotton_render_string("<c-card title='Inline'></c-card>")
        assert "Inline" in html

    def test_context_variables_are_interpolated(self, cotton_render_string):
        html = cotton_render_string(
            "<c-card title='{{ heading }}'></c-card>",
            context={"heading": "From the context"},
        )
        assert "From the context" in html

    def test_plain_django_markup_still_renders(self, cotton_render_string):
        html = cotton_render_string("{{ greeting }}", context={"greeting": "hello"})
        assert html.strip() == "hello"


class TestCottonRenderStringSoup:
    """The inline-template renderer that returns parsed HTML."""

    def test_nested_components_produce_nested_elements(self, cotton_render_string_soup):
        soup = cotton_render_string_soup(
            "<c-grid md='2'><c-card title='One'></c-card><c-card title='Two'></c-card></c-grid>"
        )
        text = soup.get_text()
        assert "One" in text
        assert "Two" in text

    def test_context_reaches_the_parsed_output(self, cotton_render_string_soup):
        soup = cotton_render_string_soup(
            "<c-card title='{{ title }}'></c-card>", context={"title": "Contextual"}
        )
        assert "Contextual" in soup.get_text()


class TestRequestAwareTags:
    """Both inline renderers must satisfy tags that read ``context.request``.

    ``{% querystring %}`` reads the attribute a ``RequestContext`` sets, not the
    ``request`` context variable, and ``c-pagination.link`` builds its href with
    it. A plain ``Context`` raises ``AttributeError`` from inside the tag, which
    would break these fixtures for every consuming project.
    """

    def test_string_renderer_supplies_the_request_attribute(
        self, cotton_render_string
    ):
        html = cotton_render_string('<c-pagination.link :page="2" text="2" />')
        assert "page=2" in html

    def test_soup_renderer_supplies_the_request_attribute(
        self, cotton_render_string_soup
    ):
        soup = cotton_render_string_soup('<c-pagination.link :page="2" text="2" />')
        assert "page=2" in soup.find("a")["href"]

    def test_a_caller_supplied_request_is_honoured(self, cotton_render_string):
        """A caller passing its own request keeps that request's query string,
        which is the only way to exercise a component that reads ``?`` state."""
        from django.test import RequestFactory

        html = cotton_render_string(
            '<c-pagination.link :page="2" text="2" />',
            context={"request": RequestFactory().get("/items/?q=widget")},
        )
        assert "q=widget" in html


class TestBeautifulSoupGuard:
    """beautifulsoup4 is not a runtime dependency, so the import is deferred."""

    def test_returns_the_class_when_installed(self):
        assert _beautiful_soup().__name__ == "BeautifulSoup"

    def test_fails_with_install_instructions_when_missing(self, monkeypatch):
        import builtins

        real_import = builtins.__import__

        def missing_bs4(name, *args, **kwargs):
            if name == "bs4":
                raise ImportError("No module named 'bs4'")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", missing_bs4)

        with pytest.raises(ImportError, match="beautifulsoup4"):
            _beautiful_soup()
