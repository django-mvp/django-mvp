"""Views for the Account Center — the account area any installed app can add
a page to.

Source: mvp/menus.py (AccountCenterMenu), mvp/urls.py (the area's URLconf).
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.utils.translation import gettext_lazy as _

from .extra import MVPTemplateView


class AccountCenterView(LoginRequiredMixin, MVPTemplateView):
    """The Account Center's landing page.

    Requires a signed-in user and sends an anonymous visitor to the project's
    configured sign-in location (decision D4); a page a contributing app adds
    to the area decides its own access rules rather than inheriting one from
    here. Declares its own single, unlinked breadcrumb through ``PageMixin``
    — the way any other page built on this package declares one — rather than
    resolving a trail from the menu.

    Its template, ``mvp/account/overview.html``, declares an empty
    ``{% block account.cards %}``. An installed app contributes a card by
    shipping its own copy of that template, extending the same name, and
    adding to the block through ``{{ block.super }}`` — Django resolves a
    same-name ``{% extends %}`` to the next template in the loader path, so
    several apps chain (Refined 2026-09-14, US-3, FR-018, FR-019, FR-020).
    This view declares no attribute, no registry and no template tag for it.
    """

    template_name = "mvp/account/overview.html"
    page_title = _("Account Center")
    page_subtitle = _("Manage your account and see what's available to you here.")
    breadcrumbs = [{"text": _("Account Center")}]


class SignInView(LoginView):
    """The Account Center's sign-in page, registered as ``account_login``.

    A project that installs account management (``allauth.account``) gets
    that package's own sign-in page instead — see ``mvp/urls.py``.
    """

    template_name = "mvp/account/login.html"
