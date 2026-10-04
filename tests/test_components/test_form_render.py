"""Tests for the <c-form.render> component.

Renders a whole Django form through the daisyUI template pack, on the path
``{{ form|crispy }}`` takes for a form with no helper, as opposed to
<c-form.field>, which renders one control from explicit attributes and is
covered in test_form_field.py.
"""

from django import forms
from django.template.loader import render_to_string

from mvp.fixtures import _beautiful_soup


class HelpTextForm(forms.Form):
    """A field whose help text carries an actionable link, e.g. allauth's
    "Forgot your password?" reset link on the password field."""

    password = forms.CharField(
        widget=forms.PasswordInput,
        help_text="Forgot your password?",
    )


class TestFormRender:
    def test_the_control_is_described_by_its_help_text(self):
        html = render_to_string("cotton/form/render.html", {"form": HelpTextForm()})
        soup = _beautiful_soup()(html, "html.parser")

        control = soup.find(id="id_password")
        help_text = soup.find(id="id_password_helptext")
        assert help_text is not None
        assert "id_password_helptext" in control["aria-describedby"].split()
