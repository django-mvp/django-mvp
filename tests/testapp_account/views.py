"""Fixture pages proving a page outside ``mvp`` can extend the Account
Center's layout and pick up its trail (US-2).

Extend ``MVPTemplateView`` alone for now — T019 adds ``AccountPageMixin`` to
these bases once it exists, which is what turns their ``page.breadcrumbs``
from the default empty list into the trail ``TestAccountSectionTrail`` (T017)
asserts. Not gated with ``LoginRequiredMixin`` either: the area imposes no
access rule of its own (D4, FR-004), and these pages exist only to prove the
layout/menu/trail integration, so they stay reachable by an anonymous test
client.
"""

from mvp.views.extra import MVPTemplateView


class FixturePlainView(MVPTemplateView):
    """The page ``fixture_plain`` points at."""

    template_name = "testapp_account/plain.html"


class FixtureGroupedView(MVPTemplateView):
    """The page ``fixture_grouped_item`` points at — a section's own address."""

    template_name = "testapp_account/grouped.html"


class FixtureGroupedDetailView(MVPTemplateView):
    """A page below the section's address, naming no entry of its own.

    Its URL name, ``grouped-detail``, starts with the ``grouped`` prefix
    ``fixture_grouped_item`` declares in ``extra_context["url_names"]`` —
    that's the declaration ``get_active_section`` resolves it through.
    """

    template_name = "testapp_account/grouped_detail.html"
