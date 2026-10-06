"""Tests for the <c-mvp.actions.language-switcher> dropdown.

Choosing a language posts ``language=<code>`` to Django's ``set_language`` view
with the CSRF token and the page to return to.

Source: mvp/templates/cotton/mvp/actions/language_switcher.html
"""

import pytest
from bs4 import BeautifulSoup
from django.contrib.auth.models import AnonymousUser
from django.template import engines
from django.test import RequestFactory
from django.urls import reverse
from django.utils import translation
from django_cotton.compiler_regex import CottonCompiler


def render(language_code="en", path="/some/path/"):
    """Draw the switcher on a request whose active language is set."""
    request = RequestFactory().get(path)
    request.user = AnonymousUser()
    request.LANGUAGE_CODE = language_code
    source = CottonCompiler().process("<c-mvp.actions.language-switcher />")
    template = engines["django"].from_string(source)
    with translation.override(language_code):
        html = template.render({}, request=request)
    return BeautifulSoup(html, "html.parser")


@pytest.mark.django_db
class TestLanguageSwitcher:
    def test_the_form_posts_to_the_set_language_view(self):
        form = render().select_one("form")

        assert form["method"] == "post"
        assert form["action"] == reverse("set_language")

    def test_the_form_carries_the_csrf_token_and_the_page_to_return_to(self):
        form = render(path="/some/path/").select_one("form")

        assert form.select_one("input[name='csrfmiddlewaretoken']") is not None
        assert form.select_one("input[name='next']")["value"] == "/some/path/"

    def test_each_language_is_a_submit_button_inside_the_form(self):
        buttons = render().select("form button[type='submit'][name='language']")

        codes = [button["value"] for button in buttons]
        assert {"en", "fr"} <= set(codes)
        assert len(codes) == len(set(codes))

    def test_the_list_holds_only_list_items(self):
        soup = render()

        assert soup.select("ul.menu > :not(li)") == []

    def test_only_the_current_language_is_marked_active(self):
        active = render("fr").select("button[name='language'].menu-active")

        assert [button["value"] for button in active] == ["fr"]
