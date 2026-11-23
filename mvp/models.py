"""The one model piece django-mvp ships: the mixin that gives a user model its preferences."""

from django.db import models
from object_preferences.fields import PreferencesField


class PreferencesMixin(models.Model):
    """Give a user model the field django-mvp stores each person's preferences in.

    Add it to the project's user model, then run ``makemigrations``. A model
    that already has an attribute called ``preferences`` can carry a
    ``PreferencesField`` under another name instead.

    Attributes:
        preferences: The preferences the person has changed from their defaults.
    """

    preferences = PreferencesField()

    class Meta:
        abstract = True
