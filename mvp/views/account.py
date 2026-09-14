"""Views for the Account Center — the account area any installed app can add
a page to.

Source: mvp/menus.py (AccountCenterMenu, get_active_section), mvp/urls.py (the
area's URLconf).
"""

from django.apps import apps
from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from ..menus import get_active_section
from .extra import MVPTemplateView


class AccountPageMixin:
    """Supplies ``page.breadcrumbs`` for a page in the Account Center.

    Compose it with your own access-control mixin and a ``PageMixin`` view
    (:class:`~mvp.views.extra.MVPTemplateView` or similar) — the area itself
    imposes no access rule of its own (D4, FR-004), so this mixin never gates
    who reaches the view it's mixed into::

        from django.contrib.auth.mixins import LoginRequiredMixin

        from mvp.views.account import AccountPageMixin
        from mvp.views.extra import MVPTemplateView


        class NotificationsView(LoginRequiredMixin, AccountPageMixin, MVPTemplateView):
            template_name = "yourapp/notifications.html"

    The trail names the area, then the active section
    :func:`~mvp.menus.get_active_section` resolves for the request, with the
    last crumb carrying no link. A page the menu names no section for — the
    area's own landing page, or a page no entry points at — gets the single,
    unlinked area crumb (FR-015).
    """

    def get_breadcrumbs(self):
        section = get_active_section(self.request)
        if section is None:
            return [{"text": _("Account Center")}]
        crumbs = [{"text": _("Account Center"), "href": reverse("account-center")}]
        if section["is_current"]:
            crumbs.append({"text": section["label"]})
        else:
            crumbs.append({"text": section["label"], "href": section["url"]})
        return crumbs


class AccountCenterView(LoginRequiredMixin, AccountPageMixin, MVPTemplateView):
    """The Account Center's landing page.

    Requires a signed-in user and sends an anonymous visitor to the project's
    configured sign-in location (decision D4); a page a contributing app adds
    to the area decides its own access rules rather than inheriting one from
    here. ``AccountPageMixin`` yields the single, unlinked area crumb here,
    since ``get_active_section`` excludes the area's own landing page from
    section resolution.

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
