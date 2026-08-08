"""Tests for <c-form.formset> and <c-form.formset.row>.

Renders a whole Django formset with the same per-field presentation a single
form's fields already get from <c-form.field> / <c-form.render> — one row per
form, the management form, and the inert empty-form template used to clone
new rows client-side. Sources are compiled through the Cotton compiler so the
tests exercise each component exactly as a template invocation would, per
tests/test_components/test_form_field.py.
"""

import importlib.util

import pytest
from bs4 import BeautifulSoup
from django import forms
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
        MinFormSet = forms.formset_factory(RowForm, extra=0, min_num=2, validate_min=True)
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
        MaxFormSet = forms.formset_factory(RowForm, extra=0, max_num=1, validate_max=True)
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
        assert disabled_binding is not None
        assert "visible" in disabled_binding
        assert "maxNum" in disabled_binding


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
        row_error_container = soup.find(
            attrs={"id": "div_id_order_lines-0-quantity"}
        )
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

    Rows are the only elements whose ``x-data`` mentions ``removed`` (the
    formset root's own ``x-data`` carries ``total``/``visible`` instead), so
    this scopes to the nearest such ancestor without any extra test-only
    markup in the row template.
    """
    return page.locator(f'input[name="{quantity_input_name}"]').locator(
        "xpath=ancestor::div[contains(@x-data, 'removed')][1]"
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
        urlconf = type(
            "_URLConf",
            (),
            {"urlpatterns": [path("formset-e2e/<int:pk>/", view_cls.as_view())]},
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
                page.locator('input[name="order_lines-2-DELETE"]').input_value()
                == "on"
            )

            page.get_by_role("button", name="Save & continue").click()
            page.wait_for_url(lambda url: url != start_url)

        removed_existing_pk = removed_existing.pk
        assert not OrderLine.objects.filter(pk=removed_existing_pk).exists()
        kept.refresh_from_db()
        assert kept.quantity == 7
        assert OrderLine.objects.filter(product=product).count() == 1
