"""Views for the Account Center — the account area any installed app can add
a page to.

Source: mvp/menus.py (AccountCenterMenu), mvp/urls.py (the area's URLconf).
"""

from django.apps import apps
from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.loader import render_to_string
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

    ``get_context_data`` walks every installed application configuration
    collecting ``account_center_card_template``, renders each one against the
    context its own ``account_center_card_context(request)`` returns, and hands
    the rendered cards to the page — an app declaring neither attribute
    contributes nothing (US-3, FR-018, FR-019, FR-020).

    **A card is rendered in a context of its own.** What one app's card
    context returns reaches that card and nothing else: not the page around
    it, and not another app's card. Merging every contributor's context into
    the page's own would let a card name ``user``, ``page`` or another card's
    key and silently replace it for the whole render, which is a card
    breaking the page that hosts it. Each card still gets the request and
    everything the project's context processors put there, because it is
    rendered with the request.
    """

    template_name = "mvp/account/overview.html"
    page_title = _("Account Center")
    page_subtitle = _("Manage your account and see what's available to you here.")
    breadcrumbs = [{"text": _("Account Center")}]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cards = []
        for app_config in apps.get_app_configs():
            template_name = getattr(app_config, "account_center_card_template", None)
            if not template_name:
                continue
            get_card_context = getattr(app_config, "account_center_card_context", None)
            card_context = get_card_context(self.request) if get_card_context else {}
            cards.append(
                render_to_string(template_name, card_context, request=self.request)
            )
        context["account_center_cards"] = cards
        return context
