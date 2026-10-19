"""A user narrows a list from the toolbar and the filter modal, in a real browser (FS-041 US-3, US-4).

What these tests settle happens only in a browser: a pick or a toggle that
submits the form, the address a GET form builds once list_view.js has
dropped the fields nobody set, the filter modal putting its fields back
when it closes without applying, and a toolbar field of several values, or
a developer's own widget, applying once when focus leaves it changed. The
context and markup behind them are tested without a browser in
tests/test_views/test_list.py and tests/test_components/test_list_filter_field.py.
"""

from urllib.parse import parse_qs, urlparse

import django_filters
import pytest
from django.urls import path
from playwright.sync_api import expect

from demo.filters import ProductFilter
from demo.models import Category, Product
from demo.urls import urlpatterns as demo_patterns
from demo.views import ProductListView
from tests.conftest import requires_browser, urlconf_of
from tests.factories import CategoryFactory, ProductFactory

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


class SeveralValuesFilter(ProductFilter):
    """The demo's filterset with its category on the default multi-select widget."""

    category = django_filters.ModelMultipleChoiceFilter(
        queryset=Category.objects.order_by("name"), label="Category"
    )


class SeveralValuesListView(ProductListView):
    """The product list with a default multi-select in the toolbar."""

    filterset_class = SeveralValuesFilter


SEVERAL_VALUES_PAGE = "/several-values/"
SEVERAL_VALUES_URLCONF = urlconf_of(
    path(SEVERAL_VALUES_PAGE.strip("/") + "/", SeveralValuesListView.as_view()),
    *demo_patterns,
)


@pytest.fixture
def categories(db):
    found = CategoryFactory.create_batch(3)
    for category in found:
        ProductFactory.create_batch(2, category=category, status="published")
    return found


def _count_page_loads(page):
    """Return a list that gains an entry for every time the list is fetched from now on.

    A filter swaps the list in place with htmx, so a fetch counts as well as a
    page load.
    """
    loads = []
    page.on(
        "request",
        lambda request: loads.append(request.url)
        if request.resource_type in ("document", "xhr", "fetch")
        else None,
    )
    return loads


def _settle(page):
    page.wait_for_load_state("networkidle")
    # A submit is queued a task after focus leaves; give it the time to have fired.
    page.wait_for_timeout(300)
    page.wait_for_load_state("networkidle")


def _move_focus_away(page):
    page.locator("h1").first.click()


@pytest.mark.urls(SEVERAL_VALUES_URLCONF)
class TestSeveralValuesApplyOnClose:
    def _dropdown(self, page):
        return page.locator('[data-mvp-toolbar-field="category"]')

    def test_ticking_two_values_and_leaving_updates_the_address_once(
        self, page, live_server, categories
    ):
        _open(page, live_server, SEVERAL_VALUES_PAGE)
        loads = _count_page_loads(page)
        dropdown = self._dropdown(page)
        dropdown.locator("[role=button]").click()
        first, second = categories[0], categories[2]

        dropdown.locator(f"input[name=category][value='{first.pk}']").check()
        dropdown.locator(f"input[name=category][value='{second.pk}']").check()
        _move_focus_away(page)

        page.wait_for_url(
            lambda url: sorted(parse_qs(urlparse(url).query).get("category", []))
            == sorted([str(first.pk), str(second.pk)])
        )
        assert set(_query(page)) == {"category"}
        _settle(page)
        assert len(loads) == 1
        ticked = self._dropdown(page).locator("input[name=category]:checked")
        expect(ticked).to_have_count(2)

    def test_opening_and_leaving_without_a_change_does_not_update(
        self, page, live_server, categories
    ):
        _open(page, live_server, f"{SEVERAL_VALUES_PAGE}?category={categories[1].pk}")
        address = page.url
        loads = _count_page_loads(page)
        dropdown = self._dropdown(page)
        dropdown.locator("[role=button]").click()
        expect(dropdown.locator("input[name=category]").first).to_be_visible()

        _move_focus_away(page)

        _settle(page)
        assert loads == []
        assert page.url == address

    def test_ticking_and_unticking_the_same_value_does_not_update(
        self, page, live_server, categories
    ):
        _open(page, live_server, SEVERAL_VALUES_PAGE)
        loads = _count_page_loads(page)
        dropdown = self._dropdown(page)
        dropdown.locator("[role=button]").click()
        box = dropdown.locator(f"input[name=category][value='{categories[0].pk}']")

        box.check()
        box.uncheck()
        _move_focus_away(page)

        _settle(page)
        assert loads == []


class TestDevelopersWidgetAppliesOnLeave:
    def _widget(self, page):
        return page.locator('[data-mvp-toolbar-field="category"]')

    def test_a_changed_widget_updates_the_address_once_when_focus_leaves(
        self, page, live_server, categories
    ):
        _open(page, live_server, LIST_PAGE)
        loads = _count_page_loads(page)
        chosen = categories[1]
        self._widget(page).locator(".ts-control").click()

        page.locator(".ts-dropdown .option", has_text=chosen.name).first.click()
        _move_focus_away(page)

        _wait_for_query(page, {"category": [str(chosen.pk)]})
        _settle(page)
        assert len(loads) == 1

    def test_leaving_the_widget_unchanged_does_not_update(
        self, page, live_server, categories
    ):
        _open(page, live_server, LIST_PAGE)
        address = page.url
        loads = _count_page_loads(page)
        self._widget(page).locator(".ts-control").click()
        expect(page.locator(".ts-dropdown .option").first).to_be_visible()

        _move_focus_away(page)

        _settle(page)
        assert loads == []
        assert page.url == address


class TwoTextFilters(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains", label="Name")
    description = django_filters.CharFilter(
        lookup_expr="icontains", label="Description"
    )

    class Meta:
        model = Product
        fields: list[str] = []


class TwoTextFiltersListView(ProductListView):
    """Two text filters in the toolbar and nothing else: no search, no modal."""

    filterset_class = TwoTextFilters
    toolbar_filters = ["name", "description"]


TWO_TEXT_FILTERS_PAGE = "/two-text-filters/"
TWO_TEXT_FILTERS_URLCONF = urlconf_of(
    path(TWO_TEXT_FILTERS_PAGE.strip("/") + "/", TwoTextFiltersListView.as_view()),
    *demo_patterns,
)


@pytest.mark.urls(TWO_TEXT_FILTERS_URLCONF)
class TestEnterInAToolbarTextField:
    def test_enter_updates_the_address_when_nothing_else_submits_the_form(
        self, page, live_server, products
    ):
        _open(page, live_server, TWO_TEXT_FILTERS_PAGE)

        field = page.locator("#filterForm input[name=name]")
        field.fill("lamp")
        field.press("Enter")

        _wait_for_query(page, {"name": ["lamp"]})


def _mark_the_document(page):
    page.evaluate("window.mvpProbe = true")


def _same_document(page):
    return page.evaluate("window.mvpProbe === true")


class TestTheListUpdatesInPlace:
    """A filter, the pager or a column heading swaps the list region, never the page (#557)."""

    def test_a_search_updates_the_list_without_loading_the_page(
        self, page, live_server, products
    ):
        ProductFactory(name="Lamp", status="published")
        _open(page, live_server, LIST_PAGE)
        _mark_the_document(page)

        field = page.locator("#filterForm input[name=q]")
        field.fill("lamp")
        field.press("Enter")

        _wait_for_query(page, {"q": ["lamp"]})
        expect(page.locator(".mvp-list-refinements li")).to_have_count(1)
        assert _same_document(page)

    def test_the_back_button_returns_to_the_list_before_the_filter(
        self, page, live_server, products
    ):
        _open(page, live_server, LIST_PAGE)
        _pick(page, "status", STATUS_LABELS["draft"])
        _wait_for_query(page, {"status": ["draft"]})

        page.go_back()

        _wait_for_query(page, {})
        expect(page.locator(".mvp-list-refinements")).to_have_count(0)

    def test_a_column_heading_sorts_the_table_without_loading_the_page(
        self, page, live_server, products
    ):
        _open(page, live_server, TABLE_PAGE)
        _mark_the_document(page)

        page.locator("thead a").first.click()

        page.wait_for_url(lambda url: "sort=" in url)
        assert _same_document(page)
