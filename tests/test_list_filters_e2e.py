"""A user narrows a list from the toolbar and the filter modal, in a real browser (FS-041 US-3).

What these tests settle happens only in a browser: a pick or a toggle that
submits the form, the address a GET form builds once list_view.js has
dropped the fields nobody set, and the filter modal putting its fields back
when it closes without applying. The context and markup behind them are
tested without a browser in tests/test_views/test_list.py.
"""

from urllib.parse import parse_qs, urlparse

import pytest
from playwright.sync_api import expect

from demo.filters import ProductFilter
from demo.models import Product
from tests.conftest import requires_browser
from tests.factories import ProductFactory

pytestmark = [pytest.mark.e2e, requires_browser, pytest.mark.django_db]

DESKTOP = {"width": 1440, "height": 900}
LIST_PAGE = "/products/"
TABLE_PAGE = "/django-tables2/"
STATUS_LABELS = dict(Product.STATUS_CHOICES)
SORT_LABELS = {key: str(label) for key, label, _ in ProductFilter.base_filters["o"].options}


def _open(page, live_server, path):
    page.set_viewport_size(DESKTOP)
    page.goto(f"{live_server.url}{path}")
    page.wait_for_load_state("networkidle")


def _query(page):
    return parse_qs(urlparse(page.url).query, keep_blank_values=True)


def _wait_for_query(page, expected):
    page.wait_for_url(
        lambda url: parse_qs(urlparse(url).query, keep_blank_values=True) == expected
    )


def _pick(page, name, text):
    dropdown = page.locator(
        "[data-mvp-dropdown]", has=page.locator(f"input[type=hidden][name={name}]")
    )
    dropdown.locator("[role=button]").first.click()
    dropdown.locator(".dropdown-content").get_by_text(text, exact=True).click()


def _filter_modal(page):
    page.locator("button[aria-haspopup=dialog]").click()
    modal = page.locator("dialog#filterModal")
    expect(modal).to_be_visible()
    return modal


@pytest.fixture
def products(db):
    return ProductFactory.create_batch(15, status="published", is_featured=False)


class TestToolbarApplies:
    def test_picking_a_choice_updates_the_address(self, page, live_server, products):
        _open(page, live_server, LIST_PAGE)

        _pick(page, "status", STATUS_LABELS["draft"])

        _wait_for_query(page, {"status": ["draft"]})

    def test_the_toggle_updates_the_address(self, page, live_server, products):
        _open(page, live_server, LIST_PAGE)

        page.locator("input[name=is_featured]").click()

        _wait_for_query(page, {"is_featured": ["true"]})

    def test_choosing_a_sort_updates_the_address(self, page, live_server, products):
        _open(page, live_server, LIST_PAGE)

        _pick(page, "o", SORT_LABELS["-price"])

        _wait_for_query(page, {"o": ["-price"]})

    def test_enter_in_the_search_submits_it(self, page, live_server, products):
        _open(page, live_server, LIST_PAGE)

        page.locator("input[name=q]").fill("lamp")
        page.locator("input[name=q]").press("Enter")

        _wait_for_query(page, {"q": ["lamp"]})

    def test_a_search_for_the_word_unknown_reaches_the_address(
        self, page, live_server, products
    ):
        _open(page, live_server, LIST_PAGE)

        page.locator("input[name=q]").fill("unknown")
        page.locator("input[name=q]").press("Enter")

        _wait_for_query(page, {"q": ["unknown"]})

    def test_a_change_on_page_two_lands_on_page_one(self, page, live_server, products):
        _open(page, live_server, f"{LIST_PAGE}?page=2")

        page.locator("input[name=is_featured]").click()

        _wait_for_query(page, {"is_featured": ["true"]})


CLOSERS = {
    "close button": lambda modal: modal.get_by_role("button", name="Close").first.click(),
    "backdrop": lambda modal: modal.locator(".modal-backdrop button").click(),
    "escape": lambda modal: modal.page.keyboard.press("Escape"),
}


class TestFilterModalCloses:
    @pytest.mark.parametrize("path", [LIST_PAGE, TABLE_PAGE])
    @pytest.mark.parametrize("closer", CLOSERS.values(), ids=list(CLOSERS))
    def test_closing_leaves_the_address_and_restores_the_fields(
        self, page, live_server, products, path, closer
    ):
        _open(page, live_server, f"{path}?q=lamp&price_min=2")
        address = page.url
        modal = _filter_modal(page)
        modal.locator("input[name=price_min]").fill("5")
        modal.locator("input[name=price_max]").fill("9")
        modal.locator("select[name=is_available]").select_option("true")

        closer(modal)

        expect(modal).to_be_hidden()
        assert page.url == address
        expect(modal.locator("input[name=price_min]")).to_have_value("2")
        expect(modal.locator("input[name=price_max]")).to_have_value("")
        expect(modal.locator("select[name=is_available]")).to_have_value("unknown")


class TestFilterModalApplies:
    @pytest.mark.parametrize("path", [LIST_PAGE, TABLE_PAGE])
    def test_apply_sends_the_modal_and_the_toolbar_and_no_empty_fields(
        self, page, live_server, products, path
    ):
        _open(page, live_server, f"{path}?q=lamp")
        modal = _filter_modal(page)
        modal.locator("input[name=price_min]").fill("5")

        modal.locator("button[type=submit]").click()

        _wait_for_query(page, {"q": ["lamp"], "price_min": ["5"]})

    def test_a_chosen_no_from_a_select_is_sent(self, page, live_server, products):
        _open(page, live_server, LIST_PAGE)
        modal = _filter_modal(page)
        modal.locator("select[name=is_available]").select_option("false")

        modal.locator("button[type=submit]").click()

        _wait_for_query(page, {"is_available": ["false"]})
