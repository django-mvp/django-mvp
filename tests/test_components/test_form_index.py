"""Tests for the <c-form> component (mvp/templates/cotton/form/index.html).

The `<form>` wrapper that hosts a single form's rendering (<c-form.render>)
and, from this story on, an optional formset's rendering
(<c-form.formset>). Sources are compiled through the Cotton compiler so the
tests exercise the component exactly as a template invocation would, per
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


class PlainForm(forms.Form):
    """A form with no file field — not multipart."""

    name = forms.CharField()


class FileRowForm(forms.Form):
    """A formset row form with a file field — multipart."""

    upload = forms.FileField()


FileFormSet = forms.formset_factory(FileRowForm, extra=1)


class TestFormEnctype:
    """enctype is multipart when either form_obj or formset needs it."""

    def test_enctype_is_multipart_when_only_the_formset_is_multipart(self):
        form_obj = PlainForm()
        formset = FileFormSet()
        html = render(
            '<c-form :form-obj="form_obj" :formset="formset" method="post"></c-form>',
            form_obj=form_obj,
            formset=formset,
        )
        assert 'enctype="multipart/form-data"' in html

    def test_enctype_is_multipart_when_only_a_row_set_is(self):
        html = render(
            '<c-form :form-obj="form_obj" :inlines="inlines" method="post"></c-form>',
            form_obj=PlainForm(),
            inlines=[FileFormSet()],
        )
        assert 'enctype="multipart/form-data"' in html

    def test_enctype_is_emitted_once_when_several_row_sets_are_multipart(self):
        """Two multipart sets must not put the attribute on the tag twice.

        FR-012 decides the encoding from the parent form and every set
        together, so the answer is one attribute however many sets need it.
        Emitting it per set produces a duplicate attribute, which browsers
        tolerate and the markup contract does not.
        """
        html = render(
            '<c-form :form-obj="form_obj" :inlines="inlines" method="post"></c-form>',
            form_obj=PlainForm(),
            inlines=[FileFormSet(), FileFormSet()],
        )
        assert html.count('enctype="multipart/form-data"') == 1

    def test_enctype_is_absent_when_nothing_needs_it(self):
        html = render(
            '<c-form :form-obj="form_obj" :inlines="inlines" method="post"></c-form>',
            form_obj=PlainForm(),
            inlines=[forms.formset_factory(PlainForm, extra=1)()],
        )
        assert "enctype=" not in html
