"""Management command to create the demo's sign-in accounts."""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from object_preferences.registry import registry

#: One account per role the demo shows, all with the password ``password``.
ACCOUNTS = [
    ("regular.user", {}),
    ("staff.user", {"is_staff": True}),
    ("super.user", {"is_staff": True, "is_superuser": True}),
]

#: The locale choices of the one account that has made some, so the demo shows
#: the preferences page and the signed-in site with a person who has chosen.
CHOSEN_LOCALE = {
    "regular.user": {"timezone": "Europe/Berlin", "language": "de"},
}


class Command(BaseCommand):
    """Create or reset the demo's regular, staff and superuser accounts.

    Each signs in with the username shown (the email's local part) and the
    password ``password``. The regular account also gets a stored timezone and
    language; the other two keep the defaults. For local development only.
    """

    help = "Create the demo's sign-in accounts (password: password)"

    def handle(self, *args, **options):
        """Create each account, or reset it to its role and password."""
        user_model = get_user_model()
        for username, flags in ACCOUNTS:
            user, _created = user_model.objects.update_or_create(
                username=username,
                defaults={"email": f"{username}@example.com", **flags},
            )
            user.set_password("password")
            user.save()
            if username in CHOSEN_LOCALE:
                preferences = registry.get_preferences(user)
                preferences.change("locale", **CHOSEN_LOCALE[username])
                preferences.save()
            self.stdout.write(f"{username} / password")
