"""Pytest fixtures for testing django-mvp's Cotton components."""

from typing import Any

import pytest
from django.template import Context, Template
from django.test import RequestFactory
from django_cotton.compiler_regex import CottonCompiler  # type: ignore[import-untyped]
from django_cotton.utils import render_component  # type: ignore[import-untyped]

compiler = CottonCompiler()


def _beautiful_soup():
    """Return the BeautifulSoup class, or raise with install instructions.

    This module is registered as a pytest11 entry point, so pytest imports it at
    startup for every project that installs django-mvp. beautifulsoup4 is not a
    runtime dependency of the package, so importing it at module level would
    break collection for consumers who never use the ``*_soup`` fixtures. Only
    those two fixtures need it, and only when they are actually requested.

    Returns:
        The ``bs4.BeautifulSoup`` class.

    Raises:
        ImportError: beautifulsoup4 is not installed.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError as exc:
        raise ImportError(
            "The *_soup fixtures need beautifulsoup4, which django-mvp does not "
            "install. Add it to your test dependencies: pip install beautifulsoup4"
        ) from exc
    return BeautifulSoup


@pytest.fixture
def cotton_render():
    """Provide a callable that renders a Cotton component to raw HTML.

    The callable builds a request itself, and takes the component's attributes
    as keyword arguments.

    Returns:
        A callable taking a component name, an optional context dict and
        attribute keywords, and returning the rendered HTML.

    Example::

        def test_something(cotton_render):
            html = cotton_render("card", title="Hello")
            assert "Hello" in html
    """
    factory = RequestFactory()

    def _render(
        component_name: str, context: dict[str, Any] | None = None, **kwargs: Any
    ):
        """Render a Cotton component with a request supplied.

        Args:
            component_name: Component name in dotted notation, such as ``card``
                or ``app.sidebar``.
            context: Component attributes as a dict.
            **kwargs: Component attributes, as an alternative to ``context``.

        Returns:
            The rendered HTML.
        """
        request = factory.get("/")
        return render_component(request, component_name, context, **kwargs)

    return _render


@pytest.fixture
def cotton_render_soup():
    """Provide a callable that renders a Cotton component and parses it.

    Like ``cotton_render``, but the HTML comes back parsed by BeautifulSoup.

    Returns:
        A callable taking a component name, an optional context dict and
        attribute keywords, and returning the parsed HTML.

    Example::

        def test_something(cotton_render_soup):
            soup = cotton_render_soup("card", title="Hello")
            assert "Hello" in soup.get_text()
    """
    factory = RequestFactory()

    def _render(
        component_name: str, context: dict[str, Any] | None = None, **kwargs: Any
    ):
        """Render a Cotton component with a request supplied, then parse it.

        Args:
            component_name: Component name in dotted notation, such as ``card``
                or ``app.sidebar``.
            context: Component attributes as a dict.
            **kwargs: Component attributes, as an alternative to ``context``.

        Returns:
            The rendered HTML, parsed by BeautifulSoup.
        """
        request = factory.get("/")
        html = render_component(request, component_name, context, **kwargs)
        return _beautiful_soup()(html, "html.parser")

    return _render


@pytest.fixture
def cotton_render_string():
    """Provide a callable that renders a template string holding Cotton markup.

    The string goes through django-cotton's compiler and then Django's
    ``Template``, so inline component markup such as ``<c-button>`` can be
    tested without a template file.

    Returns:
        A callable taking a template string and an optional context dict, and
        returning the rendered HTML.

    Example::

        def test_button_in_template(cotton_render_string):
            html = cotton_render_string("<c-card title='Click me'></c-card>")
            assert "Click me" in html


        def test_with_context(cotton_render_string):
            html = cotton_render_string(
                "<c-alert>{{ message }}</c-alert>",
                context={"message": "Hello World"},
            )
            assert "Hello World" in html
    """
    factory = RequestFactory()

    def _render(template_string: str, context: dict[str, Any] | None = None):
        """Compile and render a template string holding Cotton components.

        Args:
            template_string: A Django template string using Cotton syntax.
            context: Template context variables. A ``request`` in it is used,
                otherwise one is built.

        Returns:
            The rendered HTML.
        """
        if context is None:
            context = {}
        request = context.get("request") or factory.get("/")
        context["request"] = request

        compiled_template = compiler.process(template_string)

        django_template = Template(compiled_template)
        django_context = Context(context)
        # Tags such as {% querystring %} read context.request, the attribute a
        # RequestContext sets, rather than the "request" context variable.
        django_context.request = request  # type: ignore[attr-defined]
        return django_template.render(django_context)

    return _render


@pytest.fixture
def cotton_render_string_soup():
    """Provide a callable that renders Cotton markup in a string and parses it.

    Like ``cotton_render_string``, but the HTML comes back parsed by
    BeautifulSoup, for asserting on nested structure across components.

    Returns:
        A callable taking a template string and an optional context dict, and
        returning the parsed HTML.

    Example::

        def test_nested_list(cotton_render_string_soup):
            soup = cotton_render_string_soup(
                "<c-ul><c-li text='first' /><c-li text='second' /></c-ul>"
            )
            items = soup.find_all("li")
            assert len(items) == 2
            assert items[0].get_text() == "first"
            assert items[1].get_text() == "second"


        def test_complex_layout_with_context(cotton_render_string_soup):
            template = '''
                <c-card>
                    <c-card.title>{{ title }}</c-card.title>
                    <c-card.body>
                        <c-button variant='primary'>{{ action }}</c-button>
                    </c-card.body>
                </c-card>
            '''
            soup = cotton_render_string_soup(
                template, context={"title": "My Card", "action": "Click Here"}
            )
            assert "My Card" in soup.get_text()
            assert "Click Here" in soup.get_text()
    """
    factory = RequestFactory()

    def _render(template_string: str, context: dict[str, Any] | None = None):
        """Compile, render and parse a template string holding Cotton components.

        Args:
            template_string: A Django template string using Cotton syntax.
            context: Template context variables. A ``request`` in it is used,
                otherwise one is built.

        Returns:
            The rendered HTML, parsed by BeautifulSoup.
        """
        if context is None:
            context = {}
        request = context.get("request") or factory.get("/")
        context["request"] = request

        compiled_template = compiler.process(template_string)

        django_template = Template(compiled_template)
        django_context = Context(context)
        django_context.request = request  # type: ignore[attr-defined]
        html = django_template.render(django_context)

        return _beautiful_soup()(html, "html.parser")

    return _render
