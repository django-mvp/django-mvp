"""A user narrows a list from the toolbar and the filter panel, in a real browser (FS-041 US-3, US-4; FS-042 US-3).

What these tests settle happens only in a browser: a pick or a toggle that
submits the form, the address a GET form builds once list_view.js has
dropped the fields nobody set, the filter panel's fields joining the
toolbar's form from outside it and the panel showing each response's state,
and a toolbar field of several values, or
a developer's own widget, applying once when focus leaves it changed. The
context and markup behind them are tested without a browser in
tests/test_views/test_list.py and tests/test_components/test_list_filter_field.py.
"""

from urllib.parse import parse_qs, urlparse

import django_filters
import pytest
from django import forms
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


NARROW = {"width": 390, "height": 844}


def _panel(page):
    return page.locator("#filters")


def _apply(page):
    _panel(page).locator("button[type=submit]").click()


def _clear(page):
    return _panel(page).locator(".mvp-filter-panel-foot a")


class PanelBehindTheButtonListView(ProductListView):
    """The product list with the filter panel a drawer at every width."""

    filter_panel_attrs = {"position": "start", "align": "content", "breakpoint": False}


BEHIND_THE_BUTTON_PAGE = "/behind-the-button/"
BEHIND_THE_BUTTON_URLCONF = urlconf_of(
    path(
        BEHIND_THE_BUTTON_PAGE.strip("/") + "/", PanelBehindTheButtonListView.as_view()
    ),
    *demo_patterns,
)


class DevelopersInput(forms.TextInput):
    """A widget a developer chose for a text filter, in place of its default."""


class DevelopersWidgetFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        lookup_expr="icontains", label="Name", widget=DevelopersInput
    )

    class Meta:
        model = Product
        fields: list[str] = []


class DevelopersWidgetPanelListView(ProductListView):
    """A filter with the developer's own widget, in the panel."""

    filterset_class = DevelopersWidgetFilter
    toolbar_filters: list[str] = []


DEVELOPERS_WIDGET_PAGE = "/developers-widget/"
DEVELOPERS_WIDGET_URLCONF = urlconf_of(
    path(
        DEVELOPERS_WIDGET_PAGE.strip("/") + "/", DevelopersWidgetPanelListView.as_view()
    ),
    *demo_patterns,
)


@pytest.fixture
def lamps(db):
    ProductFactory(name="Lamp cheap", price="3.00", status="published")
    return ProductFactory.create_batch(
        11, name="Lamp dear", price="20.00", status="published"
    )


class TestFilterPanel:
    def test_applying_narrows_the_list_and_keeps_the_search_and_the_sort(
        self, page, live_server, lamps
    ):
        _open(page, live_server, f"{LIST_PAGE}?q=lamp&o=price")
        expect(page.locator("#mvp-list").get_by_text("Lamp cheap")).to_have_count(1)

        page.locator("#filters input[name=price_min]").fill("10")
        _apply(page)

        _wait_for_query(page, {"q": ["lamp"], "o": ["price"], "price_min": ["10"]})
        expect(page.locator("#mvp-list").get_by_text("Lamp cheap")).to_have_count(0)

    def test_applying_on_page_two_lands_on_page_one(self, page, live_server, lamps):
        _open(page, live_server, f"{LIST_PAGE}?q=lamp&o=price&page=2")

        page.locator("#filters input[name=price_min]").fill("10")
        _apply(page)

        _wait_for_query(page, {"q": ["lamp"], "o": ["price"], "price_min": ["10"]})

    def test_a_toolbar_change_keeps_the_panels_values(
        self, page, live_server, products
    ):
        _open(page, live_server, LIST_PAGE)
        page.locator("#filters input[name=price_min]").fill("10")

        page.locator("#filterForm input[name=is_featured]").click()

        _wait_for_query(page, {"price_min": ["10"], "is_featured": ["true"]})

    def test_the_panels_clear_removes_its_filters_and_keeps_the_toolbar_and_the_sort(
        self, page, live_server, lamps
    ):
        _open(page, live_server, f"{LIST_PAGE}?q=lamp&o=-price&price_min=5")

        _clear(page).click()

        _wait_for_query(page, {"q": ["lamp"], "o": ["-price"]})

    def test_the_panel_shows_the_state_of_each_response(
        self, page, live_server, products
    ):
        _open(page, live_server, LIST_PAGE)
        expect(_clear(page)).to_have_count(0)

        page.locator("#filters input[name=price_min]").fill("5")
        _apply(page)

        _wait_for_query(page, {"price_min": ["5"]})
        expect(_clear(page)).to_have_count(1)

        _clear(page).click()

        _wait_for_query(page, {})
        expect(_clear(page)).to_have_count(0)
        expect(page.locator("#filters input[name=price_min]")).to_have_value("")

    @pytest.mark.urls(BEHIND_THE_BUTTON_URLCONF)
    def test_a_breakpoint_of_false_puts_the_filters_behind_the_button_at_a_wide_width(
        self, page, live_server, products
    ):
        _open(page, live_server, BEHIND_THE_BUTTON_PAGE)
        button = page.locator("button[aria-controls=filters]")
        expect(page.locator("#filters-panel")).to_be_hidden()

        button.click()

        expect(page.locator("#filters-panel")).to_be_visible()
        expect(button).to_have_attribute("aria-expanded", "true")

    def test_scrolling_the_panel_keeps_apply_and_clear_in_view(
        self, page, live_server, products
    ):
        page.set_viewport_size({"width": 1440, "height": 500})
        page.goto(f"{live_server.url}{LIST_PAGE}?price_min=1")
        page.wait_for_load_state("networkidle")
        aside = page.locator("#filters-panel")
        assert aside.evaluate("el => el.scrollHeight > el.clientHeight"), (
            "the filters fit, so this proves nothing"
        )
        page.evaluate("window.scrollTo(0, 300)")

        for position in ("0", "el.scrollHeight / 2", "el.scrollHeight"):
            aside.evaluate(f"el => {{ el.scrollTop = {position} }}")

            expect(_panel(page).locator("button[type=submit]")).to_be_in_viewport()
            expect(_clear(page)).to_be_in_viewport()

    @pytest.mark.urls(DEVELOPERS_WIDGET_URLCONF)
    def test_a_developers_own_widget_in_the_panel_is_submitted(
        self, page, live_server, products
    ):
        _open(page, live_server, DEVELOPERS_WIDGET_PAGE)

        page.locator("#filters input[name=name]").fill("lamp")
        _apply(page)

        _wait_for_query(page, {"name": ["lamp"]})

    def test_a_tom_select_control_in_the_panel_is_submitted(
        self, page, live_server, products
    ):
        _open(page, live_server, LIST_PAGE)

        _panel(page).locator("select[name=priority] + .ts-wrapper .ts-control").click()
        page.locator(".ts-dropdown .option", has_text="High").click()
        _apply(page)

        _wait_for_query(page, {"priority": ["high"]})

    def test_applying_from_an_open_drawer_leaves_it_closed_and_nothing_inert(
        self, page, live_server, products
    ):
        page.set_viewport_size(NARROW)
        page.goto(f"{live_server.url}{LIST_PAGE}")
        page.wait_for_load_state("networkidle")
        page.locator("button[aria-controls=filters]").click()
        expect(page.locator("#filters-panel")).to_be_visible()
        page.locator("#filters input[name=price_min]").fill("5")

        _apply(page)

        _wait_for_query(page, {"price_min": ["5"]})
        expect(page.locator("button[aria-controls=filters]")).to_have_attribute(
            "aria-expanded", "false"
        )
        expect(page.locator("#filters-panel")).to_be_hidden()
        expect(page.locator("[inert]")).to_have_count(0)

    def test_on_a_table_page_a_sort_chosen_after_applying_survives_clear(
        self, page, live_server, products
    ):
        _open(page, live_server, TABLE_PAGE)
        page.locator("#filters input[name=price_min]").fill("5")
        _apply(page)
        _wait_for_query(page, {"price_min": ["5"]})

        page.locator("thead a").first.click()
        page.wait_for_url(lambda url: "sort=" in url)
        sort = _query(page)["sort"]
        _clear(page).click()

        _wait_for_query(page, {"sort": sort})


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
