"""Views for the Account Center, the account area any installed app can add a page to.

Source: mvp/menus.py (AccountCenterMenu), mvp/urls.py (the area's URLconf).
"""

from django.conf import global_settings, settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _

from ..menus import AccountCenterMenu
from ..mounted import MountedApp
from .extra import MVPTemplateView


class AccountCenterView(LoginRequiredMixin, MVPTemplateView):
    """The Account Center's landing page.

    Requires a signed-in user and sends an anonymous visitor to the project's
    configured sign-in location; a page a contributing app adds to the area
    decides its own access rules rather than inheriting one from here.
    Declares its own single, unlinked breadcrumb through ``PageMixin`` —
    the way any other page built on this package declares one — rather than
    resolving a trail from the menu.

    Its template, ``mvp/account/overview.html``, declares an empty
    ``{% block account.cards %}``. An installed app contributes a card by
    shipping its own copy of that template, extending the same name, and
    adding to the block through ``{{ block.super }}`` — Django resolves a
    same-name ``{% extends %}`` to the next template in the loader path, so
    several apps chain (FR-018, FR-019, FR-020). This view declares no
    attribute, no registry and no template tag for it.
    """

    template_name = "mvp/account/overview.html"
    page_title = _("Account Center")
    page_subtitle = _("Manage your account and see what's available to you here.")
    breadcrumbs = [{"text": _("Account Center")}]


#: The Account Center as a mounted app: ``mvp/urls.py`` mounts it at
#: ``account/``. Its landing name stays un-namespaced (FS-028), so the
#: declaration carries no ``app_name``. Sign-in and sign-out stay outside it.
class AccountCenterApp(MountedApp):
    """The Account Center, declared the way any package declares its app."""

    name = _("Account Center")
    icon = "account_center"
    menu = AccountCenterMenu
    urls = [path("", AccountCenterView.as_view(), name="account-center")]
    landing = "account-center"


account_center = AccountCenterApp()


class SignInView(LoginView):
    """The Account Center's sign-in page, registered as ``account_login``.

    For development only — see docs/account-center.md.
    """

    template_name = "mvp/account/login.html"
    redirect_authenticated_user = True

    def get_default_redirect_url(self):
        """Land on the Account Center when the project set no redirect preference."""
        # Compared against Django's own global default, not the literal
        # "/accounts/profile/", so this stays true if Django ever changes it.
        if settings.LOGIN_REDIRECT_URL == global_settings.LOGIN_REDIRECT_URL:
            return reverse("account-center")
        return super().get_default_redirect_url()


class SignOutView(LogoutView):
    """The Account Center's sign-out page, registered as ``account_logout``.

    For development only — see docs/account-center.md. Renders
    ``template_name`` rather than redirecting (no ``next_page``).
    POST-only is Django's own, since 5.0.
    """

    template_name = "mvp/account/logout.html"
