"""Fixture pages proving a page outside ``mvp`` can extend the Account
Center's layout and pick up its menu (US-2).

Not gated with ``LoginRequiredMixin``: the area imposes no access rule of its
own (D4, FR-004), and these pages exist only to prove the layout/menu
integration, so they stay reachable by an anonymous test client. Each
declares its own ``breadcrumbs`` through ``PageMixin``, the way any other
page built on this package does (Refined 2026-09-14) — the area supplies no
mixin for it.
"""

from mvp.views.extra import MVPTemplateView


class FixturePlainView(MVPTemplateView):
    """The page ``fixture_plain`` points at."""

    template_name = "testapp_account/plain.html"


class FixtureGroupedView(MVPTemplateView):
    """The page ``fixture_grouped_item`` points at — a grouped entry's own
    address (FR-008)."""

    template_name = "testapp_account/grouped.html"
