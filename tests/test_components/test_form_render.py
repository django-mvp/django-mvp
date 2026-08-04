"""Tests for the <c-form.render> component.

Renders a whole Django form through crispy-tailwind (the "helper-less" path
`{{ form|crispy }}` takes, exercised via `cotton/form/render.html`) — as
opposed to <c-form.field>, which renders one control from explicit
attributes and is covered in test_form_field.py.
"""

import pytest
from django import forms
from django.template.loader import render_to_string


class HelpTextForm(forms.Form):
    """A field whose help text carries an actionable link, e.g. allauth's
    "Forgot your password?" reset link on the password field."""

    password = forms.CharField(
        widget=forms.PasswordInput,
        help_text="Forgot your password?",
    )


@pytest.mark.django_db
class TestCrispyHelpTextSpacing:
    """Help text must read as separate from its control, not flush against it."""

    def test_help_text_is_block_level_with_top_margin(self):
        """Regression for #125: crispy-tailwind's default (non-inline) help
        text renders as a bare <small>, an inline element whose vertical
        margin is not rendered — so a top-margin utility alone is not
        enough. The element also needs `block` before the margin can create
        any visible gap from the control above it."""
        html = render_to_string("cotton/form/render.html", {"form": HelpTextForm()})

        assert 'id="id_password_helptext"' in html
        help_text_tag = html.split('id="id_password_helptext"')[1].split(">")[0]
        assert "block" in help_text_tag
        assert "mt-2" in help_text_tag
