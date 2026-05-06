from django import forms
from django.utils.translation import gettext_lazy as _


class DeleteConfirmForm(forms.Form):
    """Single-field form used by MVPDeleteView when require_confirmation=True."""

    confirmation = forms.CharField(
        label=_("Confirmation"),
        widget=forms.TextInput(attrs={"autocomplete": "off"}),
    )

    def __init__(self, *args, confirmation_value=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._confirmation_value = confirmation_value

    def clean_confirmation(self):
        value = self.cleaned_data["confirmation"].strip()
        if self._confirmation_value is not None and value != self._confirmation_value:
            raise forms.ValidationError(_("The value you entered does not match. Please try again."))
        return value
