"""Tests for a formset built with ``can_order`` rendered by <c-mvp.form.formset>.

The server's half of reordering a row set: which rows are marked as needing an
``ORDER`` value, how a submitted-but-invalid set is put back in the person's
order, and the markup the browser behaviour hooks onto. What the browser does
with it is covered in ``test_form_formset_order_e2e.py``.
"""

from bs4 import BeautifulSoup
from django import forms
from django.template import Template
from django.template.context import Context
from django_cotton.compiler_regex import CottonCompiler

from mvp.templatetags.mvp import (
    formset_columns,
    formset_grid_style,
    formset_row_keeps_order,
    formset_rows,
)

compiler = CottonCompiler()


class NameForm(forms.Form):
    """A row with one required field and one optional one."""

    name = forms.CharField()
    note = forms.CharField(required=False)


OrderedFormSet = forms.formset_factory(NameForm, can_order=True, can_delete=True)
PlainFormSet = forms.formset_factory(NameForm, can_delete=True)


def render(source, **context):
    """Compile a Cotton source string and render it."""
    return Template(compiler.process(source)).render(Context(context))


def soup_of(formset, layout="stacked"):
    """The formset rendered by the component, parsed."""
    html = render(
        f'<c-mvp.form.formset :formset="formset" layout="{layout}" />',
        formset=formset,
    )
    return BeautifulSoup(html, "html.parser")


def submitted(rows, *, initial=None, prefix="form"):
    """POST data for a set whose ``rows`` are ``(name, order)`` pairs.

    Args:
        rows: One ``(name, order)`` pair per submitted row, in row-index order.
        initial: How many of the rows were saved; all of them by default.
        prefix: The formset prefix.

    Returns:
        The data dict a browser would post.
    """
    data = {
        f"{prefix}-TOTAL_FORMS": str(len(rows)),
        f"{prefix}-INITIAL_FORMS": str(len(rows) if initial is None else initial),
        f"{prefix}-MIN_NUM_FORMS": "0",
        f"{prefix}-MAX_NUM_FORMS": "1000",
    }
    for index, (name, order) in enumerate(rows):
        data[f"{prefix}-{index}-name"] = name
        data[f"{prefix}-{index}-ORDER"] = order
    return data


def names_in_order(formset):
    """The rows' names in the order ``formset_rows`` yields them."""
    return [form["name"].value() for form in formset_rows(formset)]


class TestFormsetRows:
    def test_a_bound_set_is_sorted_by_its_submitted_order(self):
        formset = OrderedFormSet(submitted([("a", "3"), ("b", "1"), ("c", "2")]))

        assert names_in_order(formset) == ["b", "c", "a"]

    def test_blank_and_unreadable_orders_come_last_and_keep_their_places(self):
        formset = OrderedFormSet(
            submitted([("a", ""), ("b", "x"), ("c", "2"), ("d", "1"), ("e", "")])
        )

        assert names_in_order(formset) == ["d", "c", "a", "b", "e"]

    def test_an_unbound_set_is_returned_unchanged(self):
        formset = OrderedFormSet(initial=[{"name": "a"}, {"name": "b"}])

        assert list(formset_rows(formset)) == list(formset.forms)

    def test_a_set_without_can_order_is_returned_unchanged(self):
        formset = PlainFormSet(submitted([("a", "3"), ("b", "1")]))

        assert list(formset_rows(formset)) == list(formset.forms)


class TestFormsetRowKeepsOrder:
    def test_a_saved_row_keeps_its_order(self):
        formset = OrderedFormSet(
            submitted([("a", "1"), ("b", ""), ("c", "")], initial=2)
        )

        assert formset_row_keeps_order(formset.forms[1], formset)

    def test_an_untouched_extra_row_does_not(self):
        formset = OrderedFormSet(submitted([("a", "1"), ("", "")], initial=1))

        assert not formset_row_keeps_order(formset.forms[1], formset)

    def test_an_extra_row_with_a_value_keeps_its_order(self):
        formset = OrderedFormSet(submitted([("a", "1"), ("b", "2")], initial=1))

        assert formset_row_keeps_order(formset.forms[1], formset)


class TestRowsKeepOrderWhateverTheirDisplayPlace:
    """A view's ``sort_forms`` can put forms in a different place in the list."""

    def reversed_set(self):
        formset = OrderedFormSet(
            submitted([("a", "1"), ("b", "2"), ("", "")], initial=2)
        )
        formset.forms = list(reversed(formset.forms))
        return formset

    def test_an_extra_row_shown_first_is_not_taken_for_a_saved_one(self):
        formset = self.reversed_set()
        extra = next(form for form in formset.forms if form.prefix.endswith("-2"))

        assert formset.forms[0] is extra
        assert not formset_row_keeps_order(extra, formset)

    def test_a_saved_row_shown_last_is_still_saved(self):
        formset = self.reversed_set()
        saved = next(form for form in formset.forms if form.prefix.endswith("-0"))

        assert formset_row_keeps_order(saved, formset)


class TestOrderedFormsetRows:
    def test_order_is_a_hidden_input_on_every_row(self):
        soup = soup_of(OrderedFormSet(initial=[{"name": "a"}, {"name": "b"}]))

        hidden = soup.select('input[type="hidden"][data-mvp-reorder-order]')

        assert [field["name"] for field in hidden] == [
            "form-0-ORDER",
            "form-1-ORDER",
            "form-2-ORDER",
        ]

    def test_saved_rows_are_marked_and_extra_rows_are_not(self):
        soup = soup_of(OrderedFormSet(initial=[{"name": "a"}, {"name": "b"}]))

        marked = soup.select("input[data-mvp-reorder-saved]")

        assert [field["name"] for field in marked] == ["form-0-ORDER", "form-1-ORDER"]

    def test_the_typed_order_field_is_only_offered_without_scripts(self):
        soup = soup_of(OrderedFormSet(initial=[{"name": "a"}]))

        typed = soup.select('input[type="number"][name$="-ORDER"]')

        assert typed
        assert all(field.find_parent("noscript") for field in typed)

    def test_each_row_has_one_typed_field_after_its_hidden_input(self):
        soup = soup_of(OrderedFormSet(initial=[{"name": "a"}]))
        row = soup.select_one("[data-mvp-reorder-row]")

        controls = row.select('input[name="form-0-ORDER"]')

        assert [field["type"] for field in controls] == ["hidden", "number"]

    def test_the_rows_sit_in_a_reorderable_container(self):
        soup = soup_of(OrderedFormSet(initial=[{"name": "a"}, {"name": "b"}]))

        rows = soup.select("[data-mvp-reorder-list] > [data-mvp-reorder-row]")

        assert len(rows) == 3
        assert soup.select_one("[data-mvp-reorder-list] > template")

    def test_a_set_without_can_order_renders_no_reorder_hooks(self):
        html = render(
            '<c-mvp.form.formset :formset="formset" />',
            formset=PlainFormSet(initial=[{"name": "a"}]),
        )

        assert "data-mvp-reorder" not in html
        assert "ORDER" not in html


class TestFormsetOrderInvalidRerender:
    def test_rows_return_in_the_persons_order_with_every_value_kept(self):
        formset = OrderedFormSet(
            submitted(
                [("a", "3"), ("b", "1"), ("", "2"), ("d", "")],
                initial=2,
            )
        )
        assert not formset.is_valid()

        soup = soup_of(formset)
        rows = soup.select("[data-mvp-reorder-list] > [data-mvp-reorder-row]")
        shown = [
            (
                row.select_one('input[name$="-name"]').get("value", ""),
                row.select_one('input[type="hidden"][name$="-ORDER"]')["value"],
            )
            for row in rows
        ]

        assert shown == [("b", "1"), ("", "2"), ("a", "3"), ("d", "")]

    def test_an_extra_row_the_person_filled_in_is_marked_to_keep_its_place(self):
        formset = OrderedFormSet(
            submitted([("a", "2"), ("b", "1")], initial=1),
        )
        formset.is_valid()

        soup = soup_of(formset)

        marked = [
            field["name"] for field in soup.select("input[data-mvp-reorder-saved]")
        ]
        assert marked == ["form-1-ORDER", "form-0-ORDER"]


class TestFormsetOrderLayout:
    def test_order_is_not_a_column_of_a_tabular_set(self):
        formset = OrderedFormSet()

        assert [field.name for field in formset_columns(formset)] == ["name", "note"]

    def test_a_tabular_set_that_can_order_has_a_trailing_track_for_it(self):
        plain = formset_grid_style(PlainFormSet())
        ordered = formset_grid_style(OrderedFormSet())

        assert ordered.count("auto") == plain.count("auto") + 1
        assert ordered.count("minmax") == plain.count("minmax")

    def test_each_stacked_row_header_holds_one_move_cluster(self):
        soup = soup_of(OrderedFormSet(initial=[{"name": "a"}]))
        row = soup.select_one("[data-mvp-reorder-row]")

        assert len(row.select("[data-mvp-reorder-moves]")) == 1

    def test_each_tabular_row_holds_a_cluster_for_each_width(self):
        soup = soup_of(OrderedFormSet(initial=[{"name": "a"}]), layout="tabular")
        row = soup.select_one("[data-mvp-reorder-row]")

        assert len(row.select("[data-mvp-reorder-moves]")) == 2
        assert len(row.select("noscript")) == 1
