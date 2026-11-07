"""The Account Center's preferences page.

Source: mvp/preferences.py (the groups it shows), mvp/views/account.py (its route).
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Model
from django.urls import reverse
from django.utils.functional import Promise
from django.utils.translation import gettext_lazy as _
from object_preferences.views import PreferencesView

from .base import PageMixin


class AccountPreferencesView(LoginRequiredMixin, PageMixin, PreferencesView):
    """Show the signed-in person's preferences and save them.

    Requires sign-in. The page is always about the person making the request:
    nothing in the URL or the submission can name another, so it needs no
    further access rule. It shows every preference group registered for the
    user model, each as a fieldset, with one Save button.
    """

    template_name = "mvp/account/preferences.html"
    page_title = _("Preferences")
    page_lead = _("Choose how the site looks and reads for you.")

    def get_breadcrumbs(self) -> list[dict[str, str | Promise]]:
        """Return the Account Center, linked, then this page."""
        return [
            {"text": _("Account Center"), "href": reverse("account-center")},
            {"text": _("Preferences")},
        ]

    def get_object(self, queryset=None) -> Model:
        """Return the signed-in person, whatever the request names.

        Args:
            queryset: Unused; the person is not looked up.

        Returns:
            The request's user.
        """
        return self.request.user
