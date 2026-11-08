"""The preferences django-mvp declares for the user model.

It declares one group, ``locale``: the timezone and language a signed-in person
sees the site in.

django-object-preferences imports this module while apps load. It first checks
that the user model carries a preferences field, so a project that has not given
it one stops at startup with a message saying how.
"""

import zoneinfo
from functools import cache

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _
from mvp_forms.widgets import TomSelect
from object_preferences.registry import register, registry


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

    timezone = forms.ChoiceField(label=_("Timezone"), widget=TomSelect)
    language = forms.ChoiceField(label=_("Language"), required=False)

    def __init__(self, *args, **kwargs):
        """Fill in the choices and defaults from the project's settings."""
        super().__init__(*args, **kwargs)
        self.fields["timezone"].choices = self.timezone_choices()
        self.fields["timezone"].initial = settings.TIME_ZONE
        if len(settings.LANGUAGES) < 2:
            del self.fields["language"]
            return
        self.fields["language"].choices = [
            ("", _("Automatic")),
            *settings.LANGUAGES,
        ]
        self.fields["language"].initial = ""

    @staticmethod
    @cache
    def timezone_choices() -> list[tuple[str, list[tuple[str, str]]]]:
        """List the timezones ``zoneinfo`` knows, grouped by region.

        Built from ``zoneinfo`` once per process: it costs a few milliseconds
        and the form is built on every signed-in request. A name without a
        region, such as ``UTC``, goes under "Other".

        Returns:
            Each region's label with its ``(name, name)`` choices, sorted.
        """
        regions: dict[str, list[tuple[str, str]]] = {}
        for name in sorted(zoneinfo.available_timezones()):
            region = name.split("/", 1)[0] if "/" in name else "Other"
            regions.setdefault(region, []).append((name, name))
        return sorted(regions.items(), key=lambda item: (item[0] == "Other", item[0]))
