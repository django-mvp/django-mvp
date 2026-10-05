"""A widget with a template of its own is drawn by that template (#337).

A select whose behaviour lives in its own template (django-tomselect is the
reported case) must reach the page as that template's output. A form
template that writes the ``<select>`` element itself, from the field's
choices, leaves such a widget as a bare select with none of its behaviour.

Renders a whole form through ``cotton/mvp/form/render.html`` (the
``{{ form|crispy }}`` path), the same seam ``test_form_render.py`` uses, so
the test exercises the widget exactly as a project's form does.
"""

from django import forms
from django.template.loader import render_to_string


class ProbeTemplateSelect(forms.Select):
    """A ``Select`` subclass whose own template is the only thing that
    should end up in the rendered output, standing in for django-tomselect's
    widget."""

    template_name = "tests/probe_select_widget.html"


class OwnTemplateWidgetForm(forms.Form):
    choice = forms.ChoiceField(
        choices=[("a", "Alpha"), ("b", "Beta")], widget=ProbeTemplateSelect
    )


class TestAWidgetsOwnTemplateIsRendered:
    def test_a_widget_with_its_own_template_renders_its_own_output(self):
        html = render_to_string(
            "cotton/mvp/form/render.html", {"form": OwnTemplateWidgetForm()}
        )

        assert 'data-probe-select-widget="yes"' in html
        assert "PROBE-WIDGET-OUTPUT" in html
        assert "<select" not in html
