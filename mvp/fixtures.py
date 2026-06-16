"""Pytest fixtures for testing Django Cotton BS5 components."""

import pytest
from bs4 import BeautifulSoup
from django.template import Context, Template
from django.test import RequestFactory
from django_cotton.compiler_regex import CottonCompiler  # type: ignore[import-untyped]
from django_cotton.utils import render_component  # type: ignore[import-untyped]

compiler = CottonCompiler()


@pytest.fixture
def cotton_render():
    """
    Fixture that renders Django-Cotton components and returns raw HTML.

    Automatically provides a request object to be DRY. Component variables
    are passed as kwargs.

    Usage:
        def test_something(cotton_render):
            html = cotton_render(
                'cotton_bs5.alert',
                message="Hello",
                type="success"
            )
            assert 'alert-success' in html
    """
    factory = RequestFactory()

    def _render(component_name, context=None, **kwargs):
        """
        Render a Cotton component with automatic request injection.

        Args:
            component_name: Component name in dotted notation (e.g., "cotton_bs5.alert")
            context: Optional context dict to pass as component attributes
            **kwargs: Component attributes (alternative to context dict)

        Returns:
            Rendered HTML string
        """
        request = factory.get("/")
        return render_component(request, component_name, context, **kwargs)

    return _render


@pytest.fixture
def cotton_render_soup():
    """
    Fixture that renders Django-Cotton components and returns BeautifulSoup parsed HTML.

    Automatically provides a request object and parses the result for easy testing.
    Component variables are passed as kwargs.

    Usage:
        def test_something(cotton_render_soup):
            soup = cotton_render_soup(
                'cotton_bs5.alert',
                message="Hello",
                type="success"
            )
            assert soup.find('div')['class'] == ['alert', 'alert-success']
    """
    factory = RequestFactory()

    def _render(component_name, context=None, **kwargs):
        """
        Render a Cotton component with automatic request injection and parse with BeautifulSoup.

        Args:
            component_name: Component name in dotted notation (e.g., "cotton_bs5.alert")
            context: Optional context dict to pass as component attributes
            **kwargs: Component attributes (alternative to context dict)

        Returns:
            BeautifulSoup parsed HTML object
        """
        request = factory.get("/")
        html = render_component(request, component_name, context, **kwargs)
        return BeautifulSoup(html, "html.parser")

    return _render


@pytest.fixture
def cotton_render_string():
    """
    Fixture that compiles and renders Django template strings containing Cotton component syntax.

    This fixture takes a raw template string with Cotton components (e.g., <c-button>),
    compiles it through django-cotton's compiler, then renders it through Django's
    Template system. Useful for testing inline component markup without creating
    separate template files.

    Usage:
        def test_button_in_template(cotton_render_string):
            html = cotton_render_string("<c-button variant='primary'>Click me</c-button>")
            assert 'btn-primary' in html

        def test_with_context(cotton_render_string):
            html = cotton_render_string(
                "<c-alert>{{ message }}</c-alert>",
                context={'message': 'Hello World'}
            )
            assert 'Hello World' in html

    Returns:
        A callable function that accepts:
            - template_string (str): Django template string with Cotton component syntax
            - context (dict, optional): Template context variables

        The function returns the rendered HTML as a string.
    """
    factory = RequestFactory()

    def _render(template_string, context=None):
        """
        Compile and render a template string with Cotton components.

        Args:
            template_string: The Django template string containing Cotton component syntax
            context: Optional context dict for template variables

        Returns:
            Rendered HTML string
        """
        if context is None:
            context = {}
        request = factory.get("/")
        context["request"] = request

        # Compile Cotton component syntax into Django template syntax
        compiled_template = compiler.process(template_string)

        # Render through Django's Template system
        django_template = Template(compiled_template)
        django_context = Context(context)
        return django_template.render(django_context)

    return _render


@pytest.fixture
def cotton_render_string_soup():
    """
    Fixture that compiles and renders Django template strings with Cotton components,
    returning BeautifulSoup parsed HTML.

    This fixture combines the capabilities of cotton_render_string with BeautifulSoup
    parsing for easier DOM traversal and assertions. Particularly useful for testing
    multi-component features where you need to verify nested structure and relationships.

    Usage:
        def test_nested_list(cotton_render_string_soup):
            soup = cotton_render_string_soup(
                "<c-ul><c-li text='first' /><c-li text='second' /></c-ul>"
            )
            items = soup.find_all('li')
            assert len(items) == 2
            assert items[0].get_text() == 'first'
            assert items[1].get_text() == 'second'

        def test_complex_layout_with_context(cotton_render_string_soup):
            template = '''
                <c-card>
                    <c-card.title>{{ title }}</c-card.title>
                    <c-card.body>
                        <c-button variant='primary'>{{ action }}</c-button>
                    </c-card.body>
                </c-card>
            '''
            soup = cotton_render_string_soup(template, context={
                'title': 'My Card',
                'action': 'Click Here'
            })
            assert soup.find('h5').get_text() == 'My Card'
            assert 'btn-primary' in soup.find('button')['class']

    Returns:
        A callable function that accepts:
            - template_string (str): Django template string with Cotton component syntax
            - context (dict, optional): Template context variables

        The function returns a BeautifulSoup parsed HTML object.
    """
    factory = RequestFactory()

    def _render(template_string, context=None):
        """
        Compile, render, and parse a template string with Cotton components.

        Args:
            template_string: The Django template string containing Cotton component syntax
            context: Optional context dict for template variables

        Returns:
            BeautifulSoup parsed HTML object
        """
        if context is None:
            context = {}
        request = factory.get("/")
        context["request"] = request

        # Compile Cotton component syntax into Django template syntax
        compiled_template = compiler.process(template_string)

        # Render through Django's Template system
        django_template = Template(compiled_template)
        django_context = Context(context)
        html = django_template.render(django_context)

        # Parse with BeautifulSoup for easy DOM traversal
        return BeautifulSoup(html, "html.parser")

    return _render
