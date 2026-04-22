from django import forms
from django.utils.translation import gettext_lazy as _


class DeleteConfirmForm(forms.Form):
    """Single-field form used by MVPDeleteView when require_confirmation=True."""

    confirmation = forms.CharField(
        label=_("Confirmation"),
        widget=forms.TextInput(attrs={"autocomplete": "off"}),
    )
