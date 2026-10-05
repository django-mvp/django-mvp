"""Isolating a call to a daisy-cotton component with Cotton's `only` attribute.

`menu.title` declares `text` with no default, so a call that does not pass `text`
reads a page variable of that name. `only` keeps page variables out of the
component, while content between the tags and in named slots is still rendered with
the page's variables.
"""

import pytest
from bs4 import BeautifulSoup
from django import template
from django.contrib import messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.template.context import Context
from django.test import RequestFactory
from django.urls import reverse
from django_cotton.compiler_regex import CottonCompiler

from tests.factories import OrderLineFactory

compiler = CottonCompiler()

PAGE_TEXT = "page-text-7f3a"
PAGE_VALUE = "page-value-2c9e"
GIVEN_TEXT = "given-text-5d18"

# A page variable named after every attribute daisy-cotton's components declare
# with no default. Each value would change the element it reaches.
PAGE_VARIABLES = {
    "items": [{"text": "leak-item", "href": "/leak/"}],
    "class": "leak-class",
    "aria_label": "leak-aria-label",
    "text": "leak-text",
    "href": "/leak/",
    "size": "xl",
    "icon": "bell",
    "label": "leak-label",
    "variant": "primary",
    "hover": True,
    "horizontal": True,
    "paged": True,
}


def page_variables(request):
    """Context processor that puts the page variables on every page."""
    return PAGE_VARIABLES


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


DIRECT_CALL_ELEMENTS = {
    "shell": (
        "get",
        "home",
        {},
        ["nav.dock", "nav.dock > *", "nav.grow > ul.menu"],
    ),
    "list": (
        "get",
        "product-list",
        {},
        [
            "nav.breadcrumbs",
            "nav.breadcrumbs li",
            "nav.breadcrumbs li a",
            "nav.breadcrumbs li span",
        ],
    ),
    "sign-out": ("post", "account_logout", {}, ["a.link"]),
    "formset": ("get", "project-create", {}, [".divider"]),
}


@pytest.mark.django_db
class TestPageVariablesAndDirectCalls:
    """A page variable named after a component's attribute changes no element
    drawn by a call the package makes directly.

    An element a kept ``c-mvp.*`` component draws is outside the comparison:
    a component that declares an attribute with no default and forwards it still
    picks a page variable up, like the log-in button's ``variant`` or the share
    button's ``size``. That is a separate fault, tracked as #485.
    """

    @pytest.fixture(params=DIRECT_CALL_ELEMENTS)
    def page(self, request):
        return DIRECT_CALL_ELEMENTS[request.param]

    def drawn(self, client, page, selectors):
        method, name, kwargs, _ = page
        response = getattr(client, method)(reverse(name, kwargs=kwargs))
        assert response.status_code == 200
        soup = BeautifulSoup(response.content.decode(), "html.parser")
        return {
            selector: [(el.name, el.attrs) for el in soup.select(selector)]
            for selector in selectors
        }

    def test_each_element_is_the_same_with_and_without_the_variables(
        self, admin_client, page, settings
    ):
        selectors = page[3]
        without = self.drawn(admin_client, page, selectors)
        settings.TEMPLATES = [
            {
                **settings.TEMPLATES[0],
                "OPTIONS": {
                    **settings.TEMPLATES[0]["OPTIONS"],
                    "context_processors": [
                        *settings.TEMPLATES[0]["OPTIONS"]["context_processors"],
                        f"{__name__}.page_variables",
                    ],
                },
            }
        ]

        with_variables = self.drawn(admin_client, page, selectors)

        assert all(without.values()), "a selector drew nothing on the page"
        assert with_variables == without


@pytest.mark.django_db
class TestContentInsideAnIsolatedAlert:
    """The package's own content between an alert's tags reads the page."""

    def test_a_message_is_drawn_inside_its_alert(self, cotton_render_string_soup):
        request = RequestFactory().get("/")
        request.session = {}
        request._messages = FallbackStorage(request)
        messages.add_message(request, messages.SUCCESS, PAGE_VALUE)

        soup = cotton_render_string_soup(
            "<c-mvp.messages :messages='messages' />",
            context={"messages": messages.get_messages(request), "request": request},
        )

        assert PAGE_VALUE in soup.select_one(".toast > [role='alert']").get_text()

    def test_the_blocking_records_are_listed_inside_their_alert(self, client, product):
        line = OrderLineFactory(product=product)

        response = client.get(reverse("product-delete", kwargs={"pk": product.pk}))

        soup = BeautifulSoup(response.content.decode(), "html.parser")
        listed = [li.get_text() for li in soup.select("[role='alert'] li")]
        assert str(line) in listed


class TestDismissibleAlertCalledWithOnly:
    def render(self, source, **context):
        html = template.Template(compiler.process(source)).render(Context(context))
        return BeautifulSoup(html, "html.parser")

    def test_the_dismiss_button_is_drawn(self):
        soup = self.render("<c-alert variant='success' dismissible only>x</c-alert>")

        assert soup.select_one("[role='alert'] button[type='button']") is not None

    def test_the_icon_is_looked_up_by_name_through_this_package(self):
        soup = self.render("<c-alert variant='success' dismissible only>x</c-alert>")

        icon = soup.select_one("[role='alert'] i")
        assert icon is not None
        assert "bi" in icon["class"]
