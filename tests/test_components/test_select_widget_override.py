"""Tests for the ``tailwind/layout/select.html`` override (#337).

crispy-tailwind's own ``tailwind/layout/select.html`` writes the ``<select>``
element itself, from the field's choices and ``build_attrs``, instead of
asking the widget to render. Any widget whose behaviour lives in its own
template — django-tomselect is the reported case — arrives as a bare select
carrying the right attributes and nothing else, because the widget is never
actually rendered.

Renders a whole form through ``cotton/form/render.html`` (the ``{{ form|crispy }}``
path), the same seam ``test_form_render.py`` uses, so these tests exercise
the override exactly as a project's form does.
"""

from django import forms
from django.template.loader import render_to_string


class ProbeTemplateSelect(forms.Select):
    """A ``Select`` subclass whose own template is the only thing that
    should end up in the rendered output when it carries a widget of its
    own — standing in for django-tomselect's widget."""

    template_name = "tests/probe_select_widget.html"


class OwnTemplateWidgetForm(forms.Form):
    choice = forms.ChoiceField(
        choices=[("a", "Alpha"), ("b", "Beta")], widget=ProbeTemplateSelect
    )


class OrdinaryChoiceForm(forms.Form):
    choice = forms.ChoiceField(choices=[("a", "Alpha"), ("b", "Beta")])


class OrdinaryMultipleChoiceForm(forms.Form):
    choices = forms.MultipleChoiceField(choices=[("a", "Alpha"), ("b", "Beta")])


class TestSelectOverrideRendersAWidgetsOwnTemplate:
    def test_a_widget_with_its_own_template_renders_its_own_output(self):
        html = render_to_string(
            "cotton/form/render.html", {"form": OwnTemplateWidgetForm()}
        )

        assert 'data-probe-select-widget="yes"' in html
        assert "PROBE-WIDGET-OUTPUT" in html

    def test_the_probe_widget_does_not_also_get_crispys_markup(self):
        """The whole point of the override: crispy's own select shell must
        not additionally wrap a widget that renders itself."""
        html = render_to_string(
            "cotton/form/render.html", {"form": OwnTemplateWidgetForm()}
        )

        assert "appearance-none" not in html  # crispy's own <select> classes


class TestSelectOverrideKeepsCrispysMarkupForOrdinaryWidgets:
    def test_an_ordinary_choicefield_still_renders_crispys_markup(self):
        html = render_to_string(
            "cotton/form/render.html", {"form": OrdinaryChoiceForm()}
        )

        assert 'appearance-none' in html  # pinned from crispy's own select.html
        assert '<option value="a"' in html
        assert ">Alpha<" in html
        assert '<option value="b"' in html
        assert ">Beta<" in html

    def test_a_multiplechoicefield_still_takes_the_crispy_path(self):
        html = render_to_string(
            "cotton/form/render.html", {"form": OrdinaryMultipleChoiceForm()}
        )

        assert 'appearance-none' in html
        assert '<option value="a"' in html
        assert ">Alpha<" in html
