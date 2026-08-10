"""Tests for <c-form.formset> and <c-form.formset.row>.

Renders a whole Django formset with the same per-field presentation a single
form's fields already get from <c-form.field> / <c-form.render> — one row per
form, the management form, and the inert empty-form template used to clone
new rows client-side. Sources are compiled through the Cotton compiler so the
tests exercise each component exactly as a template invocation would, per
tests/test_components/test_form_field.py.
"""

import importlib.util
from importlib import import_module
from pathlib import Path

import mvp
import pytest
from bs4 import BeautifulSoup
from django import forms
from django.conf import settings
from django.template import Template
from django.template.context import Context
from django.test import override_settings
from django.urls import path
from django_cotton.compiler_regex import CottonCompiler

from demo.models import OrderLine
from tests.factories import OrderLineFactory, ProductFactory
from tests.test_views.test_inline import (
    _dispatch,
    _field_value,
    _inline_create_view_class,
    _inline_update_view_class,
    _rendered_html,
)

compiler = CottonCompiler()


def render(source, **context):
    """Compile a Cotton source string and render it."""
    return Template(compiler.process(source)).render(Context(context))


class RowForm(forms.Form):
    """A representative row form: one hidden bookkeeping field, one visible one."""

    row_id = forms.IntegerField(widget=forms.HiddenInput, required=False)
    name = forms.CharField()


class RowFormWithNonFieldError(RowForm):
    def clean(self):
        super().clean()
        raise forms.ValidationError("Something is wrong with this row.")


RowFormSet = forms.formset_factory(RowForm, can_delete=True, extra=2)
ErrorRowFormSet = forms.formset_factory(
    RowFormWithNonFieldError, can_delete=True, extra=0
)


def _error_row_form():
    """A single formset row that failed validation with a non-field error."""
    data = {
        "form-TOTAL_FORMS": "1",
        "form-INITIAL_FORMS": "0",
        "form-MIN_NUM_FORMS": "0",
        "form-MAX_NUM_FORMS": "1000",
        "form-0-row_id": "",
        "form-0-name": "Widget",
    }
    formset = ErrorRowFormSet(data)
    formset.is_valid()
    return formset.forms[0]


# ---------------------------------------------------------------------------
# <c-form.formset.row>
# ---------------------------------------------------------------------------


class TestFormsetRowFields:
    """Hidden fields, visible fields and DELETE get their contracted treatment."""

    def test_hidden_fields_render_directly(self):
        form = RowFormSet().forms[0]
        html = render('<c-form.formset.row :form="form" />', form=form)
        assert 'type="hidden"' in html
        assert 'name="form-0-row_id"' in html

    def test_visible_fields_render_through_crispy(self):
        form = RowFormSet().forms[0]
        html = render('<c-form.formset.row :form="form" />', form=form)
        # crispy-tailwind's field wrapper div, proving the field went through
        # the same |as_crispy_field path a single form's field takes.
        assert 'id="div_id_form-0-name"' in html
        assert 'name="form-0-name"' in html

    def test_delete_renders_as_hidden_input_not_a_checkbox(self):
        form = RowFormSet().forms[0]
        html = render('<c-form.formset.row :form="form" />', form=form)
        assert 'name="form-0-DELETE"' in html
        assert 'type="checkbox"' not in html


class TestFormsetRowErrors:
    """A row's own non-field errors render inside the row."""

    def test_non_field_errors_render_inside_the_row(self):
        form = _error_row_form()
        html = render('<c-form.formset.row :form="form" />', form=form)
        assert "Something is wrong with this row." in html


class TestFormsetRowFieldErrorPlacement:
    """A field-level error renders inside the row containing that field, in
    the same crispy field markup a single form's field error uses, and no
    other row carries it (FR-016, FR-019). This placement is inherited from
    crispy's field template rather than written here; these tests turn that
    inheritance from an assumption into a fact."""

    def test_field_error_renders_inside_its_own_row_only(self):
        formset = RowFormSet(
            data={
                "form-TOTAL_FORMS": "2",
                "form-INITIAL_FORMS": "2",
                "form-MIN_NUM_FORMS": "0",
                "form-MAX_NUM_FORMS": "1000",
                "form-0-row_id": "",
                "form-0-name": "",
                "form-1-row_id": "",
                "form-1-name": "Valid",
            }
        )
        formset.is_valid()
        html = render('<c-form.formset :formset="formset" />', formset=formset)
        soup = BeautifulSoup(html, "html.parser")
        row0 = soup.find(attrs={"id": "div_id_form-0-name"})
        row1 = soup.find(attrs={"id": "div_id_form-1-name"})
        assert "This field is required." in row0.get_text()
        assert "This field is required." not in row1.get_text()

    def test_errors_on_two_different_rows_each_carry_their_own_message(self):
        formset = RowFormSet(
            data={
                "form-TOTAL_FORMS": "2",
                "form-INITIAL_FORMS": "2",
                "form-MIN_NUM_FORMS": "0",
                "form-MAX_NUM_FORMS": "1000",
                "form-0-row_id": "",
                "form-0-name": "",
                "form-1-row_id": "",
                "form-1-name": "",
            }
        )
        formset.is_valid()
        html = render('<c-form.formset :formset="formset" />', formset=formset)
        soup = BeautifulSoup(html, "html.parser")
        row0 = soup.find(attrs={"id": "div_id_form-0-name"})
        row1 = soup.find(attrs={"id": "div_id_form-1-name"})
        assert "This field is required." in row0.get_text()
        assert "This field is required." in row1.get_text()


# ---------------------------------------------------------------------------
# <c-form.formset>
# ---------------------------------------------------------------------------


class TestFormsetManagementForm:
    def test_management_form_is_present(self):
        formset = RowFormSet()
        html = render('<c-form.formset :formset="formset" />', formset=formset)
        assert 'name="form-TOTAL_FORMS"' in html
        assert 'name="form-INITIAL_FORMS"' in html


class TestFormsetRows:
    def test_one_row_per_form_in_formset_order(self):
        formset = forms.formset_factory(RowForm, extra=0)(
            initial=[{"name": "Alpha"}, {"name": "Bravo"}]
        )
        html = render('<c-form.formset :formset="formset" />', formset=formset)
        assert 'name="form-0-name"' in html
        assert 'name="form-1-name"' in html
        assert html.index("form-0-name") < html.index("form-1-name")

    def test_blank_extra_rows_look_identical_to_populated_ones(self):
        formset = forms.formset_factory(RowForm, extra=1)(initial=[{"name": "Alpha"}])
        html = render('<c-form.formset :formset="formset" />', formset=formset)
        # form-0 is populated (from initial), form-1 is a blank extra row —
        # both must go through the same row wrapper markup.
        assert 'id="div_id_form-0-name"' in html
        assert 'id="div_id_form-1-name"' in html


class TestFormsetEmptyForm:
    def test_empty_form_appears_once_inside_a_template_element(self):
        formset = RowFormSet()
        html = render('<c-form.formset :formset="formset" />', formset=formset)
        assert html.count("<template>") == 1
        assert html.count("</template>") == 1

    def test_empty_form_carries_the_literal_prefix(self):
        formset = RowFormSet()
        html = render('<c-form.formset :formset="formset" />', formset=formset)
        assert "__prefix__" in html
        assert 'name="form-__prefix__-name"' in html


class NonFormErrorFormSet(forms.BaseFormSet):
    """A formset whose own ``clean()`` raises a set-level error — the
    developer-authored counterpart to Django's built-in ``validate_min`` /
    ``validate_max`` rules exercised in TestFormsetBuiltinSetLevelErrors."""

    def clean(self):
        if any(self.errors):
            return
        names = [form.cleaned_data.get("name") for form in self.forms]
        if len(names) != len(set(names)):
            raise forms.ValidationError("Rows must not repeat the same name.")


DuplicateNameFormSet = forms.formset_factory(
    RowForm, formset=NonFormErrorFormSet, can_delete=True, extra=0
)


def _duplicate_name_formset():
    """A bound, invalid formset carrying a non-form error."""
    data = {
        "form-TOTAL_FORMS": "2",
        "form-INITIAL_FORMS": "0",
        "form-MIN_NUM_FORMS": "0",
        "form-MAX_NUM_FORMS": "1000",
        "form-0-row_id": "",
        "form-0-name": "Widget",
        "form-1-row_id": "",
        "form-1-name": "Widget",
    }
    formset = DuplicateNameFormSet(data)
    formset.is_valid()
    return formset


class TestFormsetNonFormErrors:
    """``formset.non_form_errors`` renders above the rows, inside an element
    structurally distinct from a row's own error, and only when non-empty
    (FR-017)."""

    def test_non_form_errors_render_inside_an_alert_above_the_rows(self):
        formset = _duplicate_name_formset()
        html = render('<c-form.formset :formset="formset" />', formset=formset)
        soup = BeautifulSoup(html, "html.parser")
        alert = soup.find(attrs={"role": "alert"})
        assert alert is not None
        assert "Rows must not repeat the same name." in alert.get_text()
        assert html.index("Rows must not repeat the same name.") < html.index(
            'name="form-0-name"'
        )

    def test_no_alert_rendered_when_there_are_no_non_form_errors(self):
        formset = RowFormSet()
        html = render('<c-form.formset :formset="formset" />', formset=formset)
        soup = BeautifulSoup(html, "html.parser")
        assert soup.find(attrs={"role": "alert"}) is None


class TestFormsetBuiltinSetLevelErrors:
    """Django's own set-level validation rules — ``validate_min`` and
    ``validate_max`` — surface through ``non_form_errors`` exactly like a
    developer-authored ``formset.clean()`` error, and render above the set.
    These are the two rules the framework generates rather than the
    developer writing (T029); US3's TestInlineMaxNumCap already proves
    ``validate_max`` lands in ``formset.non_form_errors()`` — this proves the
    rendered page shows it."""

    def test_too_few_rows_renders_above_the_set(self):
        MinFormSet = forms.formset_factory(
            RowForm, extra=0, min_num=2, validate_min=True
        )
        formset = MinFormSet(
            data={
                "form-TOTAL_FORMS": "1",
                "form-INITIAL_FORMS": "0",
                "form-MIN_NUM_FORMS": "2",
                "form-MAX_NUM_FORMS": "1000",
                "form-0-row_id": "",
                "form-0-name": "Widget",
            }
        )
        formset.is_valid()
        html = render('<c-form.formset :formset="formset" />', formset=formset)
        soup = BeautifulSoup(html, "html.parser")
        alert = soup.find(attrs={"role": "alert"})
        assert alert is not None
        assert "Please submit at least 2 forms." in alert.get_text()
        assert html.index("Please submit at least 2 forms.") < html.index(
            'name="form-0-name"'
        )

    def test_too_many_rows_renders_above_the_set(self):
        MaxFormSet = forms.formset_factory(
            RowForm, extra=0, max_num=1, validate_max=True
        )
        formset = MaxFormSet(
            data={
                "form-TOTAL_FORMS": "2",
                "form-INITIAL_FORMS": "0",
                "form-MIN_NUM_FORMS": "0",
                "form-MAX_NUM_FORMS": "1000",
                "form-0-row_id": "",
                "form-0-name": "Widget",
                "form-1-row_id": "",
                "form-1-name": "Gadget",
            }
        )
        formset.is_valid()
        html = render('<c-form.formset :formset="formset" />', formset=formset)
        soup = BeautifulSoup(html, "html.parser")
        alert = soup.find(attrs={"role": "alert"})
        assert alert is not None
        assert "Please submit at most 1 form." in alert.get_text()
        assert html.index("Please submit at most 1 form.") < html.index(
            'name="form-0-name"'
        )


class TestFormsetAddRemoveControls:
    """The add and remove controls (US5, FR-026): no remove control when
    deletion is forbidden, each remove control carries an accessible name,
    neither control submits the form, and the add control is bound to the
    count of rows not marked for removal rather than the raw form count."""

    def test_no_remove_control_when_formset_forbids_deletion(self):
        NoDeleteFormSet = forms.formset_factory(RowForm, can_delete=False, extra=1)
        formset = NoDeleteFormSet()
        html = render('<c-form.formset :formset="formset" />', formset=formset)
        soup = BeautifulSoup(html, "html.parser")
        assert soup.find(attrs={"aria-label": "Remove"}) is None

    def test_each_row_remove_control_carries_an_accessible_name(self):
        formset = RowFormSet()
        html = render('<c-form.formset :formset="formset" />', formset=formset)
        soup = BeautifulSoup(html, "html.parser")
        # Exclude the inert empty-form template's own remove control - only
        # the rendered rows count here. RowFormSet has extra=2, can_delete=True.
        remove_buttons = [
            button
            for button in soup.find_all(attrs={"aria-label": "Remove"})
            if button.find_parent("template") is None
        ]
        assert len(remove_buttons) == 2

    def test_neither_control_submits_the_form(self):
        formset = RowFormSet()
        html = render('<c-form.formset :formset="formset" />', formset=formset)
        soup = BeautifulSoup(html, "html.parser")
        add_button = soup.find("button", attrs={"type": "button"})
        assert add_button is not None
        remove_button = soup.find(attrs={"aria-label": "Remove"})
        assert remove_button.name == "button"
        assert remove_button.get("type") == "button"

    def test_add_control_is_bound_to_visible_not_the_raw_form_count(self):
        formset = RowFormSet()
        html = render('<c-form.formset :formset="formset" />', formset=formset)
        soup = BeautifulSoup(html, "html.parser")
        add_button = soup.find(attrs={"aria-label": "Add row"}) or soup.find(
            lambda tag: tag.name == "button" and "Add row" in tag.get_text()
        )
        assert add_button is not None
        disabled_binding = add_button.get(":disabled") or add_button.get(
            "x-bind:disabled"
        )
        assert disabled_binding == "!canAddRow"

        # The comparison itself is in the component, so assert it there: the
        # cap is measured against the rows the user can see, never against the
        # monotonic counter, or a removed row would forfeit its slot.
        source = (
            Path(mvp.__path__[0]) / "static" / "js" / "formset.js"
        ).read_text()
        assert "return this.visible < this.maxNum;" in source


class TestFormsetAddRemoveLabels:
    """Add and remove control labels default per the contract and are
    overridable through the add-label and remove-label attributes,
    Article VIII (T034)."""

    def test_default_labels_match_the_contract(self):
        formset = RowFormSet()
        html = render('<c-form.formset :formset="formset" />', formset=formset)
        assert "Add row" in html
        soup = BeautifulSoup(html, "html.parser")
        assert soup.find(attrs={"aria-label": "Remove"}) is not None

    def test_labels_are_overridable_through_attributes(self):
        formset = RowFormSet()
        html = render(
            '<c-form.formset :formset="formset" '
            'add-label="Add item" remove-label="Take off" />',
            formset=formset,
        )
        assert "Add item" in html
        assert "Add row" not in html
        soup = BeautifulSoup(html, "html.parser")
        removed = [
            button
            for button in soup.find_all(attrs={"aria-label": "Take off"})
            if button.find_parent("template") is None
        ]
        assert len(removed) == 2
        assert soup.find(attrs={"aria-label": "Remove"}) is None

    def test_row_remove_label_is_overridable_directly(self):
        form = RowFormSet().forms[0]
        html = render(
            '<c-form.formset.row :form="form" can-delete="true" '
            'remove-label="Take off" />',
            form=form,
        )
        soup = BeautifulSoup(html, "html.parser")
        assert soup.find(attrs={"aria-label": "Take off"}) is not None
        assert soup.find(attrs={"aria-label": "Remove"}) is None


# ---------------------------------------------------------------------------
# Rendered through a view — proves the re-render is genuine, not just a
# compiled-source rendering (FR-018, US4 scenario 4)
# ---------------------------------------------------------------------------


class TestFormsetPageLevelErrorPlacement:
    """An invalid submission never collapses its error into a page-level
    summary distinct from where it belongs, and every submitted value
    survives the re-render (FR-018, US4 scenario 4). Reuses the invalid-row
    dispatch already exercised end to end by US3's
    tests/test_views/test_inline.py rather than rebuilding it."""

    @pytest.mark.django_db
    def test_invalid_submission_avoids_a_page_level_summary_and_preserves_values(self):
        view_cls = _inline_create_view_class(success_url="list")
        data = {
            "name": "Valid Parent Name",
            "order_lines-TOTAL_FORMS": "1",
            "order_lines-INITIAL_FORMS": "0",
            "order_lines-MIN_NUM_FORMS": "0",
            "order_lines-MAX_NUM_FORMS": "1000",
            "order_lines-0-quantity": "-1",  # PositiveIntegerField rejects negatives
        }

        _, response = _dispatch(view_cls, method="POST", data=data)

        assert response.status_code == 200
        html = _rendered_html(response)
        # Submitted values survive the re-render.
        assert _field_value(html, "name") == "Valid Parent Name"
        assert _field_value(html, "order_lines-0-quantity") == "-1"
        # The error appears exactly once, and that occurrence is inside the
        # row-scoped container — not additionally hoisted to a page-level
        # summary.
        assert html.count("greater than or equal to 0") == 1
        soup = BeautifulSoup(html, "html.parser")
        row_error_container = soup.find(attrs={"id": "div_id_order_lines-0-quantity"})
        assert row_error_container is not None
        assert "greater than or equal to 0" in row_error_container.get_text()


# ---------------------------------------------------------------------------
# T035 — the one browser test: adding and removing rows in the client, and a
# submission that matches what the page showed (SC-004, US5 scenario 3).
#
# Scoped to the class below, not the module: a module-level importorskip or
# pytestmark would skip and re-mark this module's unit tests too, per
# tests/test_views/test_error.py lines 185-235.
# ---------------------------------------------------------------------------

_HAS_PLAYWRIGHT = importlib.util.find_spec("playwright") is not None


def _row_locator(page, quantity_input_name):
    """Return the row wrapper for a given row's quantity input.

    Rows are the only elements initialising ``mvpFormsetRow`` (the set's own
    root initialises ``mvpFormset`` instead), so this scopes to the nearest
    such ancestor without any extra test-only markup in the row template.
    """
    return page.locator(f'input[name="{quantity_input_name}"]').locator(
        "xpath=ancestor::div[contains(@x-data, 'mvpFormsetRow')][1]"
    )


@pytest.mark.e2e
@pytest.mark.skipif(not _HAS_PLAYWRIGHT, reason="playwright not installed")
class TestFormsetAddRemoveRowsE2E:
    """Adding and removing rows happens entirely in the browser, and a
    submission afterwards matches what the page showed."""

    @pytest.mark.django_db
    def test_add_remove_and_submit_matches_the_database(self, page, live_server):
        product = ProductFactory(name="Existing")
        kept = OrderLineFactory(product=product, quantity=7)
        removed_existing = OrderLineFactory(product=product, quantity=5)
        view_cls = _inline_update_view_class(
            success_url="/formset-e2e/",
            show_detail_action=False,
            show_list_action=False,
            inline_extra=0,
        )
        # The packaged base template renders the demo menus, which reverse
        # demo view names, so the test URLconf extends the project's rather
        # than replacing it. With only the one path, every page raises
        # NoReverseMatch before the formset is ever reached.
        base_urlpatterns = import_module(settings.ROOT_URLCONF).urlpatterns
        urlconf = type(
            "_URLConf",
            (),
            {
                "urlpatterns": [
                    path("formset-e2e/<int:pk>/", view_cls.as_view()),
                    *base_urlpatterns,
                ]
            },
        )

        with override_settings(ROOT_URLCONF=urlconf):
            page.goto(f"{live_server.url}/formset-e2e/{product.pk}/")
            start_url = page.url

            total_forms = page.locator('input[name="order_lines-TOTAL_FORMS"]')
            assert total_forms.input_value() == "2"

            # Adding a row inserts a blank row with no reload and increments
            # TOTAL_FORMS.
            page.get_by_role("button", name="Add row").click()
            assert page.url == start_url
            assert total_forms.input_value() == "3"
            added_quantity = page.locator('input[name="order_lines-2-quantity"]')
            added_quantity.fill("9")

            # Removing a pre-rendered row hides it with no request. Django's
            # BaseInlineFormSet.get_queryset() orders an unordered queryset by
            # pk, so `removed_existing` (created second) is form-1.
            existing_row = _row_locator(page, "order_lines-1-quantity")
            existing_row.get_by_role("button", name="Remove").click()
            assert page.url == start_url
            assert not existing_row.is_visible()

            # Removing the row that was just added hides it and sets its
            # DELETE - the one behaviour no server-side test can reach.
            added_row = _row_locator(page, "order_lines-2-quantity")
            added_row.get_by_role("button", name="Remove").click()
            assert page.url == start_url
            assert not added_row.is_visible()
            assert (
                page.locator('input[name="order_lines-2-DELETE"]').input_value() == "on"
            )

            # By name and value, not by label: the page carries two submits
            # whose accessible names share this prefix.
            page.locator('button[name="default_next"][value="list"]').click()
            page.wait_for_url(lambda url: url != start_url)

        removed_existing_pk = removed_existing.pk
        assert not OrderLine.objects.filter(pk=removed_existing_pk).exists()
        kept.refresh_from_db()
        assert kept.quantity == 7
        assert OrderLine.objects.filter(product=product).count() == 1

    @pytest.mark.django_db
    def test_removing_a_row_gives_its_slot_back_under_the_cap(
        self, page, live_server
    ):
        """The whole reason there are two counters.

        ``visible`` lives on the set and a row has to reach it to decrement it.
        Alpine 3 has no ``$parent`` magic, and inside an ``Alpine.data`` method
        ``this`` is the row's own data rather than the merged scope chain, so
        the obvious spelling throws and the counter never moves. The page still
        hides the row, which is why nothing else here catches it: the only
        visible symptom is a set that stays at its cap after a removal.
        """
        product = ProductFactory(name="Capped")
        OrderLineFactory(product=product, quantity=1)
        OrderLineFactory(product=product, quantity=2)
        view_cls = _inline_update_view_class(
            success_url="/formset-cap/",
            show_detail_action=False,
            show_list_action=False,
            inline_extra=0,
            inline_max_num=2,
        )
        base_urlpatterns = import_module(settings.ROOT_URLCONF).urlpatterns
        urlconf = type(
            "_URLConf",
            (),
            {
                "urlpatterns": [
                    path("formset-cap/<int:pk>/", view_cls.as_view()),
                    *base_urlpatterns,
                ]
            },
        )

        with override_settings(ROOT_URLCONF=urlconf):
            page.goto(f"{live_server.url}/formset-cap/{product.pk}/")
            add = page.get_by_role("button", name="Add row")

            assert add.is_disabled(), "two rows against a cap of two"

            _row_locator(page, "order_lines-1-quantity").get_by_role(
                "button", name="Remove"
            ).click()

            assert not add.is_disabled(), (
                "a removed row must give its slot back, or the set is stuck at "
                "its cap for the rest of the page's life"
            )


# ---------------------------------------------------------------------------
# Review findings — see specs/024-formset-pages/decisions.md D41
# ---------------------------------------------------------------------------


class TestFormsetCountersAreNotLocalized:
    """The Alpine counters are JavaScript, not display text.

    Django runs every template variable through ``localize()``. A project with
    ``USE_THOUSAND_SEPARATOR`` on therefore renders the default ``max_num`` of
    1000 as ``1,000``, which turns the ``x-data`` object literal into a syntax
    error and kills the whole component silently — no server-side symptom, and
    every add and remove control dead.
    """

    @override_settings(USE_THOUSAND_SEPARATOR=True)
    def test_x_data_carries_no_grouped_numbers(self):
        formset = RowFormSet()
        html = render('<c-form.formset :formset="formset" />', formset=formset)

        x_data = BeautifulSoup(html, "html.parser").find(attrs={"x-data": True})
        assert x_data is not None
        expression = x_data["x-data"]

        assert expression == "mvpFormset(2, 1000)"
        assert "1,000" not in expression

    @override_settings(USE_THOUSAND_SEPARATOR=True)
    def test_total_forms_input_carries_no_grouped_number(self):
        formset = forms.formset_factory(RowForm, can_delete=True, extra=0)(
            initial=[{"name": f"Row {n}"} for n in range(1200)]
        )
        html = render('<c-form.formset :formset="formset" />', formset=formset)

        total_forms = BeautifulSoup(html, "html.parser").find(
            "input", attrs={"name": "form-TOTAL_FORMS"}
        )
        assert total_forms["value"] == "1200"


class TestFormsetRemoveControlNeedsADeleteField:
    """``formset.can_delete`` is set-wide; the DELETE field is per row.

    Under ``can_delete_extra=False`` Django gives DELETE only to the initial
    forms while ``formset.can_delete`` stays True. Gating the control on the
    set-wide flag alone would offer Remove on an extra row with no way to
    record the removal: the row hides and its data still saves.
    """

    def _formset(self):
        factory = forms.formset_factory(
            RowForm, can_delete=True, can_delete_extra=False, extra=1
        )
        return factory(initial=[{"name": "Alpha"}])

    def test_initial_row_keeps_its_remove_control(self):
        html = render('<c-form.formset :formset="formset" />', formset=self._formset())
        rows = BeautifulSoup(html, "html.parser").find_all(
            "div", attrs={"x-show": "!removed"}
        )
        assert rows[0].find("button", attrs={"aria-label": "Remove"}) is not None

    def test_extra_row_without_a_delete_field_offers_no_remove_control(self):
        formset = self._formset()
        html = render('<c-form.formset :formset="formset" />', formset=formset)
        soup = BeautifulSoup(html, "html.parser")

        delete_inputs = soup.find_all("input", attrs={"name": "form-1-DELETE"})
        assert delete_inputs == []

        rows = soup.find_all("div", attrs={"x-show": "!removed"})
        assert rows[1].find("button", attrs={"aria-label": "Remove"}) is None

    def test_the_empty_form_template_offers_no_remove_control_either(self):
        html = render('<c-form.formset :formset="formset" />', formset=self._formset())
        template = BeautifulSoup(html, "html.parser").find("template")
        assert template.find("button", attrs={"aria-label": "Remove"}) is None


class TestFormsetCounterContract:
    """The counter contract, pinned without a browser.

    The behaviour is in ``mvp/static/js/formset.js`` rather than in an x-data
    attribute, so it splits in two: the template's job is to load that file and
    seed the component with this set's counts, and the file's job is to hold a
    handler that increments both counters and never decrements ``total``. The
    test that drives ``addRow()`` for real is browser-gated and does not run
    here.
    """

    @staticmethod
    def _soup(formset):
        return BeautifulSoup(
            render('<c-form.formset :formset="formset" />', formset=formset),
            "html.parser",
        )

    @staticmethod
    def _component_source():
        return (Path(mvp.__path__[0]) / "static" / "js" / "formset.js").read_text()

    def test_the_component_is_registered_in_a_file_not_an_x_data_attribute(self):
        """The x-data attribute initialises; it does not define.

        An object literal in the attribute is unreadable in the page source,
        cannot be linted or covered, and puts the whole handler through
        Django's template escaping on every render.
        """
        soup = self._soup(RowFormSet())

        expression = soup.find(attrs={"x-data": True})["x-data"]
        assert expression.startswith("mvpFormset(")
        assert "{" not in expression

        script = soup.find("script", src=True)
        assert script is not None
        assert script["src"].endswith("js/formset.js")
        assert not script.has_attr("defer"), (
            "Alpine is deferred in the base template, so a deferred tag here "
            "would register the component after alpine:init had fired."
        )

    def test_counters_seed_from_the_server_side_form_count(self):
        formset = forms.formset_factory(RowForm, can_delete=True, extra=1)(
            initial=[{"name": "Alpha"}, {"name": "Beta"}]
        )
        assert formset.total_form_count() == 3

        expression = self._soup(formset).find(attrs={"x-data": True})["x-data"]
        assert expression == "mvpFormset(3, 1000)"

    def test_total_forms_input_is_bound_to_the_monotonic_counter(self):
        html = render('<c-form.formset :formset="formset" />', formset=RowFormSet())
        total_forms = BeautifulSoup(html, "html.parser").find(
            "input", attrs={"name": "form-TOTAL_FORMS"}
        )
        assert total_forms[":value"] == "total"

    def test_add_increments_both_counters_and_never_decrements_total(self):
        source = self._component_source()

        assert "this.total++" in source
        assert "this.visible++" in source
        assert "this.total--" not in source
        assert "total--" not in source

    def test_prefix_substitution_uses_the_monotonic_counter(self):
        assert '.replaceAll("__prefix__", this.total)' in self._component_source()

    def test_the_empty_form_template_is_found_from_the_component_root(self):
        """``$el`` is the add control, not the set.

        ``addRow()`` runs from the button's click handler, so ``$el`` is the
        button and the template is not inside it. Reading the template from
        ``$el`` throws on every click and the page ships an add control that
        does nothing.
        """
        source = self._component_source()

        assert 'this.$root.querySelector("template")' in source
        assert "$el.querySelector" not in source
