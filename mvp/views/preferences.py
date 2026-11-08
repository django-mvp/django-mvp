"""The Account Center's preferences page.

Source: mvp/preferences.py (the groups it shows), mvp/views/account.py (its route).
"""

from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Model
from django.forms import Media
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.functional import Promise
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.views.i18n import set_language as django_set_language
from object_preferences.registry import registry
from object_preferences.views import PreferencesView

from .base import PageMixin


@require_POST
@csrf_protect
def set_language(request: HttpRequest) -> HttpResponse:
    """Save a signed-in person's language choice, then do what Django's view does.

    The shell's language switcher posts here for a signed-in person. The chosen
    language becomes their stored ``locale`` language when the project offers it
    and the group has a language field (it has none when the project offers a
    single language). Anything else stores nothing. Django's ``set_language``
    then sets the cookie and follows ``next`` as it does for a visitor.
    ``csrf_protect`` is explicit because Django's view relies on the project's
    CSRF middleware rather than enforcing it.

    Args:
        request: The POST carrying ``language`` and, optionally, ``next``.

    Returns:
        Django's ``set_language`` response.
    """
    code = request.POST.get("language", "")
    user = request.user
    if user.is_authenticated and code in dict(settings.LANGUAGES):
        group = registry.get_group(get_user_model(), "locale")
        if "language" in group.form_class().fields:
            preferences = registry.get_preferences(user)
            preferences.change("locale", language=code)
            preferences.save()
    return django_set_language(request)


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

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add ``media``, every group form's media merged, so each asset loads once."""
        context = super().get_context_data(**kwargs)
        context["media"] = sum(
            (form.media for form in context["forms"].values()), Media()
        )
        return context
