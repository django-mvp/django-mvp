"""Tests for <c-form.formset> and <c-form.formset.row>.

Renders a whole Django formset with the same per-field presentation a single
form's fields already get from <c-form.field> / <c-form.render> — one row per
form, the management form, and the inert empty-form template used to clone
new rows client-side. Sources are compiled through the Cotton compiler so the
tests exercise each component exactly as a template invocation would, per
tests/test_components/test_form_field.py.
"""

from django import forms
from django.template import Template
from django.template.context import Context
from django_cotton.compiler_regex import CottonCompiler

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
        cleaned_data = super().clean()
        raise forms.ValidationError("Something is wrong with this row.")
        return cleaned_data  # pragma: no cover - unreachable, clean() always raises


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
