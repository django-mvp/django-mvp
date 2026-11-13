"""The site search's keyboard and focus behaviour in a real browser.

Where focus goes, which key opens the dialog and what Enter does are browser
behaviour, so only a browser settles them. The results themselves are covered
by the view tests. The pages serve the demo's component page with the search
mounted at ``search/`` and two function kinds registered.

Source: assets/js/search.js
"""

import time

import pytest
from playwright.sync_api import expect

from mvp.config import MVP_CONFIG
from mvp.search.kinds import Result
from tests.conftest import requires_browser

pytestmark = [pytest.mark.e2e, requires_browser]

NARROW = {"width": 600, "height": 800}
WIDE = {"width": 1440, "height": 900}


def fruit(query, request):
    """Find three fruits for any query; a query of ``ap`` is answered slowly."""
    if query == "ap":
        time.sleep(0.8)
    names = ["apple", "apricot"] if query.startswith("ap") else ["avocado"]
    return [
        Result(
            title=name.title(),
            url=f"/components/?hit={name}",
            where="Fruit",
            passage=f"about {query}",
        )
        for name in names
    ]


def vegetables(query, request):
    """Find one vegetable for any query."""
    return [Result(title="Artichoke", url="/components/?hit=artichoke", where="Veg")]


@pytest.fixture(autouse=True)
def search_site(settings, search_registry, monkeypatch):
    """Serve the search at ``search/`` with the widget in the navbar."""
    settings.ROOT_URLCONF = "tests.urls_search"
    navbar = MVP_CONFIG["layout"]["navbar"]
    monkeypatch.setitem(navbar, "end", [*navbar["end"], "mvp.actions.search"])
    search_registry.register(fruit, name="fruit", label="Fruit", icon="file")
    search_registry.register(vegetables, name="veg", label="Vegetables", icon="file")


def open_page(page, live_server, viewport=WIDE):
    page.set_default_timeout(5000)
    page.set_viewport_size(viewport)
    page.goto(f"{live_server.url}/components/")
    page.wait_for_function("() => window.htmx && window.Alpine")


def dialog_is_open(page):
    return page.evaluate("() => document.getElementById('mvp-search').open")


def focused(page):
    """The id of the focused element, or its tag name when it has none."""
    return page.evaluate(
        "() => document.activeElement.id || document.activeElement.tagName"
    )


def search_for(page, text):
    page.keyboard.press("Control+k")
    page.keyboard.type(text)
    page.wait_for_selector("#mvp-search-results [role=option]")


@pytest.mark.django_db(transaction=True)
class TestOpening:
    def test_ctrl_k_opens_the_dialog_with_the_field_focused(self, page, live_server):
        open_page(page, live_server)

        page.keyboard.press("Control+k")

        assert dialog_is_open(page)
        expect(page.locator("#mvp-search input[name=q]")).to_be_focused()

    def test_ctrl_k_opens_it_from_inside_another_input(self, page, live_server):
        open_page(page, live_server)
        page.evaluate(
            """() => {
                const input = document.createElement('input');
                input.id = 'other';
                document.body.prepend(input);
                input.focus();
            }"""
        )

        page.keyboard.press("Control+k")

        assert dialog_is_open(page)
        expect(page.locator("#mvp-search input[name=q]")).to_be_focused()

    def test_meta_k_opens_it_on_a_mac(self, page, live_server):
        page.add_init_script(
            "Object.defineProperty(navigator, 'platform', {get: () => 'MacIntel'})"
        )
        open_page(page, live_server)

        page.keyboard.press("Meta+k")

        assert dialog_is_open(page)
        expect(page.locator("[data-mvp-search-modifier]")).to_have_text("⌘")

    def test_slash_opens_it_outside_a_text_field(self, page, live_server):
        open_page(page, live_server)

        page.keyboard.press("/")

        assert dialog_is_open(page)
        expect(page.locator("#mvp-search input[name=q]")).to_have_value("")

    def test_slash_is_typed_inside_a_text_field(self, page, live_server):
        open_page(page, live_server)
        page.evaluate(
            """() => {
                const input = document.createElement('input');
                input.id = 'other';
                document.body.prepend(input);
                input.focus();
            }"""
        )

        page.keyboard.type("a/b")

        assert not dialog_is_open(page)
        expect(page.locator("#other")).to_have_value("a/b")

    def test_clicking_the_field_opens_it(self, page, live_server):
        open_page(page, live_server)

        page.locator(".mvp-search-field").click()

        assert dialog_is_open(page)
        expect(page.locator("#mvp-search input[name=q]")).to_be_focused()

    def test_clicking_the_button_opens_it_on_a_narrow_screen(self, page, live_server):
        open_page(page, live_server, NARROW)

        page.locator(".mvp-search-button").click()

        assert dialog_is_open(page)
        expect(page.locator("#mvp-search input[name=q]")).to_be_focused()


@pytest.mark.django_db(transaction=True)
class TestResults:
    def test_typing_shows_results_grouped_by_kind(self, page, live_server):
        open_page(page, live_server)

        search_for(page, "ap")

        headings = page.locator("#mvp-search-results .mvp-search-label")
        expect(headings).to_contain_text(["Fruit", "Vegetables"])

    def test_arrow_keys_move_the_highlight_while_focus_stays_in_the_field(
        self, page, live_server
    ):
        open_page(page, live_server)
        search_for(page, "apr")
        options = page.locator("#mvp-search-results [role=option]")
        field = page.locator("#mvp-search input[name=q]")

        page.keyboard.press("ArrowDown")

        expect(options.nth(0)).to_have_attribute("aria-selected", "true")
        active = field.get_attribute("aria-activedescendant")
        assert active == options.nth(0).get_attribute("id")
        page.keyboard.press("ArrowDown")
        expect(options.nth(0)).to_have_attribute("aria-selected", "false")
        expect(options.nth(1)).to_have_attribute("aria-selected", "true")
        assert field.get_attribute("aria-activedescendant") == (
            options.nth(1).get_attribute("id")
        )
        page.keyboard.press("ArrowUp")
        expect(options.nth(0)).to_have_attribute("aria-selected", "true")
        expect(field).to_be_focused()

    def test_the_highlight_passes_through_the_links_after_the_results(
        self, page, live_server
    ):
        open_page(page, live_server)
        search_for(page, "apr")
        hits = page.locator("#mvp-search-results [data-mvp-search-hit]")
        last = hits.count() - 1

        for _ in range(hits.count() + 2):
            page.keyboard.press("ArrowDown")

        expect(hits.nth(last)).to_have_attribute("aria-selected", "true")
        expect(page.locator("#mvp-search-results .mvp-search-all")).to_have_attribute(
            "aria-selected", "true"
        )

    def test_enter_on_a_highlight_opens_that_result(self, page, live_server):
        open_page(page, live_server)
        search_for(page, "apr")

        page.keyboard.press("ArrowDown")
        page.keyboard.press("Enter")

        page.wait_for_url("**/components/?hit=apple")

    def test_enter_with_nothing_highlighted_opens_the_results_page(
        self, page, live_server
    ):
        open_page(page, live_server)
        search_for(page, "apr")

        page.keyboard.press("Enter")

        page.wait_for_url("**/search/?q=apr")

    def test_a_newer_answer_replaces_an_older_one(self, page, live_server):
        open_page(page, live_server)
        page.keyboard.press("Control+k")

        page.keyboard.type("ap")
        page.wait_for_timeout(300)
        page.keyboard.type("r")

        expect(page.locator("#mvp-search-results")).to_contain_text("about apr")
        # The slow answer to "ap" lands after this wait, if it is not dropped.
        page.wait_for_timeout(1000)
        passages = page.locator(".mvp-search-hit-passage").all_inner_texts()
        assert set(passages) == {"about apr"}


@pytest.mark.django_db(transaction=True)
class TestClosing:
    def test_one_escape_with_text_closes_and_returns_focus(self, page, live_server):
        open_page(page, live_server)
        page.evaluate(
            """() => {
                const button = document.createElement('button');
                button.id = 'before';
                document.body.prepend(button);
                button.focus();
            }"""
        )
        page.keyboard.press("Control+k")
        page.keyboard.type("apr")

        page.keyboard.press("Escape")

        assert not dialog_is_open(page)
        assert focused(page) == "before"
