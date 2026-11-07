"""A preference group declared by an installed app, as a third-party package would."""

from django import forms
from django.contrib.auth import get_user_model
from object_preferences.registry import register


@register(get_user_model(), name="reminders")
class ReminderPreferences(forms.Form):
    """How often a person hears from the app, and how many items they see."""

    digest = forms.ChoiceField(
        label="Digest",
        choices=[("daily", "Daily"), ("weekly", "Weekly")],
        initial="weekly",
    )
    page_size = forms.IntegerField(
        label="Items per page", min_value=5, max_value=100, initial=20
    )
