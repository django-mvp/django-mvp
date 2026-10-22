"""Tests for ``<c-mvp.page.list.filters.field>``: one filterset field in the list toolbar.

The component draws the dict a list view's ``get_toolbar_field()`` returns,
by its ``kind``. Each control is named by its filter's label, never shows the
value chosen in it, and never submits the filter form by a button of its own.

Source: mvp/templates/cotton/mvp/page/list/filters/field.html
"""

import django_filters
import pytest
from django import forms

from demo.models import Category, Product
from mvp.filters import SearchFilter, SortFilter
from mvp.views.list import MVPListView


class OwnSelect(forms.Select):
    """A widget a developer chose in place of the filter's default."""


class FieldProductFilter(django_filters.FilterSet):
    q = SearchFilter(fields=["name"])
    name = django_filters.CharFilter(lookup_expr="icontains")
    status = django_filters.ChoiceFilter(choices=Product.STATUS_CHOICES)
    # Whose empty value means something of the filter's own, so it offers no empty item.
    stage = django_filters.ChoiceFilter(
        field_name="status", choices=Product.STATUS_CHOICES, empty_label=None
    )
    # Whose empty item the filter names itself.
    phase = django_filters.ChoiceFilter(
        field_name="status", choices=Product.STATUS_CHOICES, empty_label="Every status"
    )
    is_featured = django_filters.BooleanFilter()
    statuses = django_filters.MultipleChoiceFilter(
        field_name="status", choices=Product.STATUS_CHOICES
    )
    shelf = django_filters.ModelChoiceFilter(
        field_name="category", queryset=Category.objects.all(), widget=OwnSelect
    )
    o = SortFilter(
        options=[
            ("name", "By name", ["name", "pk"]),
            ("-name", "By name, reversed", ["-name", "-pk"]),
        ]
    )

    class Meta:
        model = Product
        fields: list[str] = []


# A request that sets every field, so a control that showed its value would show it.
CHOSEN = {
    "q": "lamp",
    "name": "oak",
    "status": "published",
    "is_featured": "true",
    "statuses": ["draft", "archived"],
    "o": "-name",
}

# The label of what each choice-like field above chose.
CHOSEN_LABELS = {
    "status": "Published",
    "statuses": "Draft",
    "o": "By name, reversed",
}

KINDS = ["q", "name", "status", "is_featured", "statuses", "shelf", "o"]


def _field(name, data=None):
    filterset = FieldProductFilter(data=data, queryset=Product.objects.none())
    return MVPListView().get_toolbar_field(filterset, name)


@pytest.fixture
def render(cotton_render_string_soup):
    def render(field):
        return cotton_render_string_soup(
            '<form id="filterForm">'
            '<c-mvp.page.list.filters.field :field="field" />'
            "</form>",
            context={"field": field},
        )

    return render


def _accessible_name(soup, control):
    """Return the name a screen reader gives ``control``, as far as the markup decides it."""
    if control.get("aria-label"):
        return control["aria-label"]
    if control.get("aria-labelledby"):
        return soup.find(id=control["aria-labelledby"]).get_text(" ", strip=True)
    if control.name == "button":
        return control.get_text(" ", strip=True)
    label = control.find_parent("label")
    return label.get_text(" ", strip=True) if label else ""


def _control(soup, name):
    """Return the one control the reader operates for field ``name``."""
    trigger = soup.find(attrs={"role": "button"})
    if trigger is not None:
        return trigger
    return soup.find(attrs={"name": name}, type=lambda t: t != "hidden")


class TestToolbarFieldName:
    @pytest.mark.parametrize("name", KINDS)
    def test_the_control_is_named_by_the_filters_label(self, render, db, name):
        field = _field(name)

        soup = render(field)

        assert _accessible_name(soup, _control(soup, name)) == field["label"]

    def test_a_multichoice_list_is_named_by_the_filters_label(self, render, db):
        field = _field("statuses")

        soup = render(field)

        fieldset = soup.find("fieldset")
        assert fieldset.find("legend").get_text(strip=True) == field["label"]


class TestToolbarFieldHidesItsValue:
    @pytest.mark.parametrize("name", sorted(CHOSEN_LABELS))
    def test_the_button_never_shows_the_value_chosen(self, render, db, name):
        soup = render(_field(name, CHOSEN))

        trigger = soup.find(attrs={"role": "button"})
        assert CHOSEN_LABELS[name] not in trigger.get_text(" ", strip=True)

    @pytest.mark.parametrize("name", sorted(CHOSEN_LABELS))
    def test_the_button_is_the_same_whatever_is_chosen(self, render, db, name):
        chosen = render(_field(name, CHOSEN)).find(attrs={"role": "button"})
        untouched = render(_field(name)).find(attrs={"role": "button"})

        assert str(chosen) == str(untouched)

    def test_each_value_chosen_is_ticked_in_the_list(self, render, db):
        soup = render(_field("statuses", CHOSEN))

        ticked = {box["value"] for box in soup.find_all("input", checked=True)}
        assert ticked == {"draft", "archived"}

    def test_a_toggle_set_is_on(self, render, db):
        soup = render(_field("is_featured", CHOSEN))

        assert soup.find("input", attrs={"name": "is_featured"}).has_attr("checked")

    def test_a_toggle_not_set_is_off(self, render, db):
        soup = render(_field("is_featured"))

        assert not soup.find("input", attrs={"name": "is_featured"}).has_attr(
            "checked"
        )


class TestToolbarFieldButtons:
    @pytest.mark.parametrize("name", ["status", "statuses", "o"])
    def test_no_button_submits_the_form(self, render, db, name):
        soup = render(_field(name, CHOSEN))

        buttons = soup.find_all("button")
        assert buttons
        assert {button.get("type") for button in buttons} == {"button"}

    def test_the_search_submits_the_form_by_its_one_submit_button(self, render, db):
        soup = render(_field("q", CHOSEN))

        assert len(soup.find_all("button", attrs={"type": "submit"})) == 1
        assert soup.find("input", attrs={"name": "q"})["value"] == "lamp"


class TestToolbarFieldMultichoice:
    def test_the_list_offers_every_value(self, render, db):
        soup = render(_field("statuses"))

        offered = {
            box["value"] for box in soup.find_all("input", attrs={"name": "statuses"})
        }
        assert offered == {key for key, _ in Product.STATUS_CHOICES}

    def test_nothing_is_ticked_when_nothing_is_chosen(self, render, db):
        soup = render(_field("statuses"))

        assert soup.find_all("input", checked=True) == []

    def test_the_dropdown_is_a_toolbar_field_named_for_its_filter(self, render, db):
        soup = render(_field("statuses"))

        wrapper = soup.find(attrs={"data-mvp-toolbar-field": True})
        assert wrapper["data-mvp-toolbar-field"] == "statuses"
        assert wrapper.find(attrs={"role": "button"}) is not None
        assert len(wrapper.find_all("input", attrs={"name": "statuses"})) == len(
            Product.STATUS_CHOICES
        )


class TestToolbarFieldDevelopersWidget:
    def test_the_wrapper_is_named_for_its_filter(self, render, db):
        soup = render(_field("shelf"))

        wrapper = soup.find(attrs={"data-mvp-toolbar-field": True})
        assert wrapper["data-mvp-toolbar-field"] == "shelf"

    def test_the_widget_is_drawn_in_a_toolbar_field_wrapper(self, render, db):
        soup = render(_field("shelf"))

        wrapper = soup.find(attrs={"data-mvp-toolbar-field": True})
        assert wrapper is not None
        assert wrapper.find("select", attrs={"name": "shelf"}) is not None

    def test_the_widget_is_drawn_once(self, render, db):
        soup = render(_field("shelf"))

        assert len(soup.find_all(attrs={"name": "shelf"})) == 1


class TestToolbarFieldEmptyChoice:
    """A choice filter's dropdown follows the filter's own empty choice (#559)."""

    def _items(self, soup):
        return [li.get_text(" ", strip=True) for li in soup.find_all("li")]

    def test_a_filter_with_no_empty_choice_offers_only_its_choices(self, render, db):
        items = self._items(render(_field("stage")))

        assert items == [label for _, label in Product.STATUS_CHOICES]

    def test_a_filter_that_names_its_empty_choice_offers_it_first(self, render, db):
        items = self._items(render(_field("phase")))

        assert items == ["Every status"] + [label for _, label in Product.STATUS_CHOICES]

    def test_a_filter_left_at_the_default_offers_one_empty_item_first(
        self, render, db
    ):
        items = self._items(render(_field("status")))

        assert len(items) == len(Product.STATUS_CHOICES) + 1
        assert items[1:] == [label for _, label in Product.STATUS_CHOICES]


class TestToolbarFieldSize:
    """A project's dense toolbar passes ``size`` to every control (#560)."""

    @pytest.fixture
    def render_sized(self, cotton_render_string_soup):
        def render(field):
            return cotton_render_string_soup(
                '<form id="filterForm">'
                '<c-mvp.page.list.filters.field :field="field" size="sm" />'
                "</form>",
                context={"field": field},
            )

        return render

    @pytest.mark.parametrize("name", ["q", "status", "statuses", "o"])
    def test_every_button_is_drawn_at_the_size_given(self, render_sized, db, name):
        buttons = render_sized(_field(name)).find_all(class_="btn")

        assert buttons
        assert all("btn-sm" in button["class"] for button in buttons)

    @pytest.mark.parametrize("name", ["q", "name"])
    def test_a_text_box_is_drawn_at_the_size_given(self, render_sized, db, name):
        box = render_sized(_field(name)).find(class_="input")

        assert "input-sm" in box["class"]

    def test_a_switch_is_drawn_at_the_size_given(self, render_sized, db):
        switch = render_sized(_field("is_featured")).find("input", attrs={"name": "is_featured"})

        assert "toggle-sm" in switch["class"]
