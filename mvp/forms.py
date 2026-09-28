"""Forms the package's own views use."""

from typing import TYPE_CHECKING, Any

from django import forms
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from django_stubs_ext import StrOrPromise


class DeleteConfirmForm(forms.Form):
    """Single-field form used by MVPDeleteView when require_confirmation=True.

    Args:
        *args: Passed to ``forms.Form``.
        confirmation_value: The text the person must type to confirm. ``None``
            accepts any non-empty entry.
        confirmation_label: A label to replace the field's default one.
        **kwargs: Passed to ``forms.Form``.

    Attributes:
        confirmation: The field the person types the confirmation value into.
    """

    confirmation = forms.CharField(
        label=_("Confirmation"),
        widget=forms.TextInput(attrs={"autocomplete": "off"}),
    )

    def __init__(
        self,
        *args: Any,
        confirmation_value: str | None = None,
        confirmation_label: "StrOrPromise | None" = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self._confirmation_value = confirmation_value
        if confirmation_label:
            self.fields["confirmation"].label = confirmation_label

    def clean_confirmation(self):
        """Refuse an entry that does not match the confirmation value."""
        value = self.cleaned_data["confirmation"].strip()
        if self._confirmation_value is not None and value != self._confirmation_value:
            raise forms.ValidationError(
                _("The value you entered does not match. Please try again.")
            )
        return value
