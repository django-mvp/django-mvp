"""The preferences django-mvp declares for the user model.

django-object-preferences imports this module while apps load. It first checks
that the user model carries a preferences field, so a project that has not given
it one stops at startup with a message saying how.
"""

from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from object_preferences.registry import registry


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
