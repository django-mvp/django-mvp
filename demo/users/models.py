"""The demo's user model."""

from django.contrib.auth.models import AbstractUser

from mvp.models import PreferencesMixin


class User(PreferencesMixin, AbstractUser):
    """A demo account: Django's user plus the preferences django-mvp stores on it."""

    class Meta(AbstractUser.Meta):
        verbose_name = "user"
        verbose_name_plural = "users"
        swappable = "AUTH_USER_MODEL"
