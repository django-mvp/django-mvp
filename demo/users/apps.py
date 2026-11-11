"""App configuration for the demo's own user model."""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Hold the demo's user model, which carries each person's preferences."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "demo.users"
    label = "users"
    verbose_name = "Users"
