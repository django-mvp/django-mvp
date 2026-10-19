"""Tests for ``<c-mvp.page.list.filters.modal>``: the Filter button and the filter modal.

``part="button"`` draws the Filter button, badged with how many of the modal's
filters are applied. ``part="dialog"`` draws the modal holding the filterset
fields it is given; it sits inside the list page's filter form, so it draws no
form of its own.

The badge is a daisyUI ``indicator-item`` (issue #287): positioned outside its
own box by design, half above the top edge. ``mvp/tailwind/base.css`` raises its
``z-index`` above the sticky header's, scoped to ``.mvp-page-fill``, the layout a
table view renders inside, where no vertical space separates the bar from the
header.

Source: mvp/templates/cotton/mvp/page/list/filters/modal.html
"""

import re
from pathlib import Path

import django_filters
import pytest

import mvp
from demo.models import Product
from mvp.filters import SearchFilter, SortFilter
from mvp.fixtures import _beautiful_soup
from mvp.views.list import MVPListView

MVP_ROOT = Path(next(iter(mvp.__path__))).resolve()
BASE_CSS = MVP_ROOT / "tailwind" / "base.css"
HEADER_TEMPLATE = MVP_ROOT / "templates" / "cotton" / "app" / "header.html"


class ModalProductFilter(django_filters.FilterSet):
    q = SearchFilter(fields=["name"])
    price = django_filters.RangeFilter()
    o = SortFilter(options=[("name", "Name", ["name", "pk"])])

    class Meta:
        model = Product
        fields = ["name", "status"]


# The inputs ModalProductFilter's form draws: a range filter draws two.
FIELD_INPUTS = ["q", "name", "status", "price_min", "price_max", "o"]


def _fields():
    return list(ModalProductFilter(queryset=Product.objects.none()).form)


@pytest.fixture
def render(cotton_render_string_soup):
    def render(source, **context):
        return cotton_render_string_soup(source, context=context)

    return render


class TestFilterButton:
    def test_it_is_a_button_that_opens_the_dialog_and_submits_nothing(self, render):
        soup = render(
            '<c-mvp.page.list.filters.modal part="button" :fields="fields" />',
            fields=_fields(),
        )

        button = soup.find("button")
        assert button["type"] == "button"
        assert "filterModal.showModal()" in button["@click"]
        assert button["aria-haspopup"] == "dialog"

    def test_the_badge_counts_the_applied_filters_beside_the_button(self, render):
        soup = render(
            '<c-mvp.page.list.filters.modal part="button" :fields="fields" '
            ':applied_count="2" />',
            fields=_fields(),
        )

        badge = soup.find(class_="indicator-item")
        assert badge.get_text(strip=True) == "2"

    def test_no_badge_when_no_filter_is_applied(self, render):
        soup = render(
            '<c-mvp.page.list.filters.modal part="button" :fields="fields" '
            ':applied_count="0" />',
            fields=_fields(),
        )

        assert soup.find("button") is not None
        assert soup.find(class_="indicator-item") is None


class TestFilterDialog:
    def test_every_field_it_is_given_is_drawn_once(self, render):
        soup = render(
            '<c-mvp.page.list.filters.modal part="dialog" :fields="fields" />',
            fields=_fields(),
        )

        dialog = soup.find("dialog", id="filterModal")
        for name in FIELD_INPUTS:
            assert len(dialog.find_all(attrs={"name": name})) == 1, name

    def test_only_the_fields_it_is_given_are_drawn(self, render):
        fields = [field for field in _fields() if field.name == "status"]

        soup = render(
            '<c-mvp.page.list.filters.modal part="dialog" :fields="fields" />',
            fields=fields,
        )

        dialog = soup.find("dialog", id="filterModal")
        assert {el["name"] for el in dialog.find_all(attrs={"name": True})} == {
            "status"
        }

    def test_it_draws_no_form_inside_the_filter_form(self, render):
        soup = render(
            '<form id="filterForm">'
            '<c-mvp.page.list.filters.modal part="dialog" :fields="fields" />'
            "</form>",
            fields=_fields(),
        )

        assert soup.find(id="filterForm").find("form") is None

    def test_it_submits_the_filter_form(self, render):
        soup = render(
            '<form id="filterForm">'
            '<c-mvp.page.list.filters.modal part="dialog" :fields="fields" />'
            "</form>",
            fields=_fields(),
        )

        submits = soup.find(id="filterModal").find_all(
            "button", attrs={"type": "submit"}
        )
        assert len(submits) == 1


class TestNothingToFilter:
    @pytest.mark.parametrize("part", ["button", "dialog"])
    def test_nothing_is_drawn_with_no_fields(self, render, part):
        soup = render(
            f'<c-mvp.page.list.filters.modal part="{part}" :fields="fields" />',
            fields=[],
        )

        assert soup.find("button") is None
        assert soup.find("dialog") is None


def _list_page(rf, query="", **attrs):
    view_cls = type(
        "StubModalListView",
        (MVPListView,),
        {
            "model": Product,
            "list_item_template": "cards/product_card.html",
            "filterset_class": ModalProductFilter,
            **attrs,
        },
    )
    view = view_cls()
    view.setup(rf.get(f"/products/{query}"))
    response = view.get(view.request)
    response.render()
    return _beautiful_soup()(response.content.decode(), "html.parser")


class TestTheListPagesModal:
    def test_with_no_toolbar_filters_the_modal_holds_every_field(self, rf, product):
        soup = _list_page(rf)

        dialog = soup.find("dialog", id="filterModal")
        for name in FIELD_INPUTS:
            assert len(dialog.find_all(attrs={"name": name})) == 1, name

    def test_the_modal_sits_inside_the_filter_form(self, rf, product):
        soup = _list_page(rf)

        assert soup.find("dialog", id="filterModal").find_parent(
            "form", id="filterForm"
        )

    def test_the_badge_is_not_inside_a_filled_page(self, rf, product):
        soup = _list_page(rf, "?name=Widget")

        badge = soup.find(class_="indicator-item")
        assert badge is not None, "no applied-filter badge on the list view"
        assert badge.find_parent(class_="mvp-page-fill") is None


class TestTheOverrideBeatsTheHeader:
    def test_the_badges_z_index_override_outranks_the_headers(self):
        css = BASE_CSS.read_text(encoding="utf-8")
        override = re.search(
            r"\.mvp-page-fill \.indicator-item\s*\{\s*z-index:\s*(\d+)", css
        )
        assert override is not None, (
            "no z-index override for .mvp-page-fill .indicator-item in "
            "mvp/tailwind/base.css"
        )
        badge_z = int(override.group(1))

        header_html = HEADER_TEMPLATE.read_text(encoding="utf-8")
        header_class = re.search(r"\bz-(\d+)\b", header_html)
        assert header_class is not None, (
            "the header's own z-index utility class moved out of "
            "cotton/app/header.html"
        )
        header_z = int(header_class.group(1))

        assert badge_z > header_z, (
            f"the override (z-index: {badge_z}) no longer outranks the "
            f"header (z-index: {header_z})"
        )
