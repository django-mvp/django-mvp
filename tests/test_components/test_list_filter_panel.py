"""Tests for ``<c-mvp.page.list.filters.panel>``: the filter panel.

The panel draws the filterset fields the toolbar does not inside a
``<c-mvp.page.side>``. It draws no form of its own: its fields join the
toolbar's ``<form id="filterForm">`` through the HTML ``form`` attribute, which
the view sets on each widget, and Apply names the same form. The panel's
alignment, widths and stickiness are decided by eye and are not tested.

Source: mvp/templates/cotton/mvp/page/list/filters/panel.html
"""

import django_filters
import pytest

from demo.models import Product
from mvp.filters import SearchFilter, SortFilter

VIEW_DEFAULTS = {"position": "start", "align": "content"}


class PanelProductFilter(django_filters.FilterSet):
    q = SearchFilter(fields=["name"])
    price = django_filters.RangeFilter()
    o = SortFilter(options=[("name", "Name", ["name", "pk"])])

    class Meta:
        model = Product
        fields = ["name", "status"]


# The inputs PanelProductFilter's form draws: a range filter draws two.
FIELD_INPUTS = ["q", "name", "status", "price_min", "price_max", "o"]


def _fields():
    return list(PanelProductFilter(queryset=Product.objects.none()).form)


@pytest.fixture
def render(cotton_render_string_soup):
    def render(source, **context):
        return cotton_render_string_soup(source, context=context)

    return render


def _root(soup):
    return soup.find(class_="mvp-page-side")


class TestFilterPanelFields:
    def test_every_field_it_is_given_is_drawn_once(self, render):
        soup = render(
            '<c-mvp.page.list.filters.panel :fields="fields" />', fields=_fields()
        )

        aside = _root(soup).find("aside")
        for name in FIELD_INPUTS:
            assert len(aside.find_all(attrs={"name": name})) == 1, name

    def test_only_the_fields_it_is_given_are_drawn(self, render):
        fields = [field for field in _fields() if field.name == "status"]

        soup = render(
            '<c-mvp.page.list.filters.panel :fields="fields" />', fields=fields
        )

        aside = _root(soup).find("aside")
        assert {el["name"] for el in aside.find_all(attrs={"name": True})} == {
            "status"
        }

    def test_it_draws_no_form_of_its_own(self, render):
        soup = render(
            '<form id="filterForm">'
            '<c-mvp.page.list.filters.panel :fields="fields" />'
            "</form>",
            fields=_fields(),
        )

        assert _root(soup).find("form") is None

    def test_nothing_is_drawn_with_no_fields(self, render):
        soup = render('<c-mvp.page.list.filters.panel :fields="fields" />', fields=[])

        assert soup.find(class_="mvp-page-side") is None
        assert soup.find("aside") is None
        assert soup.get_text(strip=True) == ""


class TestFilterPanelIsASidePanel:
    def test_it_is_a_side_panel_with_a_name(self, render):
        soup = render(
            '<c-mvp.page.list.filters.panel :fields="fields" />', fields=_fields()
        )

        aside = _root(soup).find("aside")
        label = soup.find(id=aside["aria-labelledby"])
        assert label.get_text(strip=True)

    def test_its_id_is_filters_unless_given(self, render):
        fields = _fields()

        default = render(
            '<c-mvp.page.list.filters.panel :fields="fields" />', fields=fields
        )
        named = render(
            '<c-mvp.page.list.filters.panel :fields="fields" id="refine" />',
            fields=fields,
        )

        assert _root(default)["id"] == "filters"
        assert _root(named)["id"] == "refine"
        assert _root(named).find("aside")["id"] == "refine-panel"

    def test_the_views_default_dict_puts_it_at_the_start_level_with_the_content(
        self, render
    ):
        soup = render(
            '<c-mvp.page.list.filters.panel :fields="fields" :attrs="attrs" />',
            fields=_fields(),
            attrs=VIEW_DEFAULTS,
        )

        root = _root(soup)
        assert root["data-mvp-side-position"] == "start"
        assert root["data-mvp-side-align"] == "content"

    @pytest.mark.parametrize(
        ("attrs", "attribute", "value"),
        [
            ({"width": "lg"}, "data-mvp-side-width", "lg"),
            ({"position": "end"}, "data-mvp-side-position", "end"),
            ({"align": "title"}, "data-mvp-side-align", "title"),
            ({"breakpoint": "2xl"}, "data-mvp-side-breakpoint", "2xl"),
            ({"collapse": "stack"}, "data-mvp-side-collapse", "stack"),
        ],
    )
    def test_it_follows_the_side_panel_attributes_it_is_given(
        self, render, attrs, attribute, value
    ):
        soup = render(
            '<c-mvp.page.list.filters.panel :fields="fields" :attrs="attrs" />',
            fields=_fields(),
            attrs=attrs,
        )

        assert _root(soup)[attribute] == value

    def test_a_breakpoint_of_false_keeps_it_a_drawer_at_every_width(self, render):
        soup = render(
            '<c-mvp.page.list.filters.panel :fields="fields" :attrs="attrs" />',
            fields=_fields(),
            attrs={**VIEW_DEFAULTS, "breakpoint": False},
        )

        assert not _root(soup).has_attr("data-mvp-side-breakpoint")


class TestFilterPanelActions:
    def test_apply_submits_the_toolbar_form_from_outside_it(self, render):
        soup = render(
            '<c-mvp.page.list.filters.panel :fields="fields" />', fields=_fields()
        )

        submits = _root(soup).find_all("button", attrs={"type": "submit"})
        assert len(submits) == 1
        assert submits[0]["form"] == "filterForm"

    def test_clear_is_drawn_only_with_a_clear_url(self, render):
        fields = _fields()

        without = render(
            '<c-mvp.page.list.filters.panel :fields="fields" />', fields=fields
        )
        with_url = render(
            '<c-mvp.page.list.filters.panel :fields="fields" '
            'clear_url="/products/?o=name" />',
            fields=fields,
        )

        assert without.find("a", href=True) is None
        assert _root(with_url).find("a", href="/products/?o=name") is not None

    def test_clear_swaps_the_list_region_and_refreshes_the_panel(self, render):
        soup = render(
            '<c-mvp.page.list.filters.panel :fields="fields" '
            'clear_url="/products/" region="results" id="refine" />',
            fields=_fields(),
        )

        clear = _root(soup).find("a", href="/products/")
        assert clear["hx-target"] == "#results"
        assert clear["hx-select"] == "#results"
        assert clear["hx-select-oob"] == "#refine"

    def test_clear_is_a_plain_link_without_a_region(self, render):
        soup = render(
            '<c-mvp.page.list.filters.panel :fields="fields" '
            'clear_url="/products/" />',
            fields=_fields(),
        )

        clear = _root(soup).find("a", href="/products/")
        assert not clear.has_attr("hx-target")

    def test_the_actions_sit_in_one_foot_after_the_fields(self, render):
        soup = render(
            '<c-mvp.page.list.filters.panel :fields="fields" '
            'clear_url="/products/" />',
            fields=_fields(),
        )

        foot = _root(soup).find(class_="mvp-filter-panel-foot")
        assert foot.find("button", attrs={"type": "submit"}) is not None
        assert foot.find("a", href="/products/") is not None
        assert foot.find(attrs={"name": True}) is None
        last_field = _root(soup).find_all(attrs={"name": "o"})[-1]
        assert last_field in foot.find_all_previous()
