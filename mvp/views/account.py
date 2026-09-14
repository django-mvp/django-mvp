"""Views for the Account Center — the account area any installed app can add
a page to.

Source: mvp/menus.py (AccountCenterMenu), mvp/urls.py (the area's URLconf).
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext_lazy as _

from .extra import MVPTemplateView


class AccountCenterView(LoginRequiredMixin, MVPTemplateView):
    """The Account Center's landing page.

    Requires a signed-in user and sends an anonymous visitor to the project's
    configured sign-in location (decision D4); a page a contributing app adds
    to the area decides its own access rules rather than inheriting one from
    here.
    """

    template_name = "mvp/account/overview.html"
    page_title = _("Account Center")
    page_subtitle = _("Manage your account and see what's available to you here.")
