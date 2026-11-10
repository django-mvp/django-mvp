"""The preferences django-mvp declares for the user model.

It declares one group, ``locale``: the timezone and language a signed-in person
sees the site in.

django-object-preferences imports this module while apps load. It first checks
that the user model carries a preferences field, so a project that has not given
it one stops at startup with a message saying how.
"""

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _
from mvp_forms.widgets import TimeZoneSelect
from object_preferences.registry import register, registry
from timezone_field import TimeZoneFormField


def require_preferences_field() -> None:
    """Stop startup when the user model has no preferences field.

    Raises:
        ImproperlyConfigured: If the user model does not carry exactly one
            ``PreferencesField``. The message names the model, the mixin that
            adds the field, and the alternative of a field under another name.
    """
    user_model = get_user_model()
    try:
        registry.get_field(user_model)
    except ImproperlyConfigured as error:
        raise ImproperlyConfigured(
            f"django-mvp stores each person's preferences on the user model, and "
            f"{user_model._meta.label} does not have exactly one. Add "
            f"mvp.models.PreferencesMixin to {user_model.__name__}, or give it a "
            f"PreferencesField under another name if it already has an attribute "
            f"called preferences. Then run makemigrations."
        ) from error


require_preferences_field()


@register(get_user_model(), name="locale", verbose_name=_("Timezone and language"))
class LocalePreferences(forms.Form):
    """A person's timezone and language.

    The timezone defaults to ``settings.TIME_ZONE`` and the language to
    automatic, which leaves Django's own language negotiation in charge. A
    project that offers a single language has nothing to choose, so the
    language field is left out.
    """

    timezone = TimeZoneFormField(label=_("Timezone"), widget=TimeZoneSelect)
    language = forms.ChoiceField(label=_("Language"), required=False)

    def __init__(self, *args, **kwargs):
        """Fill in the choices and defaults from the project's settings."""
        super().__init__(*args, **kwargs)
        self.fields["timezone"].initial = settings.TIME_ZONE
        if len(settings.LANGUAGES) < 2:
            del self.fields["language"]
            return
        self.fields["language"].choices = [
            ("", _("Automatic")),
            *settings.LANGUAGES,
        ]
        self.fields["language"].initial = ""
