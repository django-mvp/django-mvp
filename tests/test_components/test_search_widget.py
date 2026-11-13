"""Tests for the search's navbar widget and the components it draws.

Source: mvp/templates/cotton/mvp/actions/search.html,
mvp/templates/cotton/mvp/search/field.html,
mvp/templates/cotton/mvp/search/button.html,
mvp/templates/cotton/mvp/search/dialog.html
"""

import pytest
from bs4 import BeautifulSoup
from django.template import engines
from django.test import RequestFactory
from django.urls import reverse
from django_cotton.compiler_regex import CottonCompiler

pytestmark = [pytest.mark.urls("tests.urls_search"), pytest.mark.django_db]


def draw(tag="<c-mvp.actions.search />"):
    """Render ``tag`` with a request and return the parsed page fragment."""
    request = RequestFactory().get("/")
    template = engines["django"].from_string(CottonCompiler().process(tag))
    return BeautifulSoup(template.render({}, request), "html.parser")


class TestSearchWidget:
    def test_draws_one_dialog_with_the_search_id(self):
        soup = draw()

        assert len(soup.select("dialog#mvp-search")) == 1

    def test_field_and_button_open_the_dialog(self):
        soup = draw()

        openers = soup.select("[commandfor=mvp-search][command=show-modal]")
        assert len(openers) == 2

    def test_field_announces_its_shortcut(self):
        soup = draw()

        field = soup.select_one(".mvp-search-field")
        assert "Control+K" in field["aria-keyshortcuts"]
        assert "Meta+K" in field["aria-keyshortcuts"]

    def test_button_stands_down_where_the_field_shows(self):
        soup = draw()

        button = soup.select_one(".mvp-search-button")
        assert "mvp-mobile-only" in button["class"]
        assert "mvp-desktop-only" in soup.select_one(".mvp-search-field")["class"]

    def test_names_open_with_the_site(self, monkeypatch):
        from mvp.config import MVP_CONFIG

        monkeypatch.setitem(MVP_CONFIG, "site_name", "Acme Docs")

        soup = draw()

        assert soup.select_one(".mvp-search-field")["aria-label"] == "Search Acme Docs"
        assert soup.select_one("dialog#mvp-search")["aria-label"] == "Search Acme Docs"


class TestSearchDialog:
    def test_form_is_a_search_landmark_posting_to_the_results_page(self):
        form = draw().select_one("#mvp-search form")

        assert form["role"] == "search"
        assert form["action"] == reverse("mvp-search")
        assert form["method"].lower() == "get"

    def test_input_is_a_combobox_over_the_results_list(self):
        soup = draw()

        field = soup.select_one("#mvp-search input[name=q]")
        results = soup.select_one("#mvp-search [role=listbox]")
        assert field["role"] == "combobox"
        assert field["aria-controls"] == results["id"]
        assert field["aria-expanded"] == "false"

    def test_input_asks_the_panel_and_replaces_older_requests(self):
        soup = draw()

        field = soup.select_one("#mvp-search input[name=q]")
        results = soup.select_one("#mvp-search [role=listbox]")
        assert field["hx-get"] == reverse("mvp-search-panel")
        assert field["hx-target"] == f"#{results['id']}"
        assert field["hx-sync"] == "this:replace"

    def test_results_list_holds_the_hints_at_first(self):
        results = draw().select_one("#mvp-search [role=listbox]")

        assert results.select_one(".mvp-search-hints") is not None
