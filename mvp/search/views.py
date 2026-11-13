"""The search's two pages: the dialog's partial and the results page."""

from __future__ import annotations

from typing import Any

from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from mvp.search import registry
from mvp.search.registry import QUERY_MAX
from mvp.views import MVPTemplateView

PANEL_LIMIT = 4
RESULTS_LIMIT = 6
PAGE_SIZE = 20


def clean_query(request: HttpRequest) -> str:
    """Read the request's query the way :func:`mvp.search.search` cleans it.

    Args:
        request: The request, whose ``q`` parameter holds the query.

    Returns:
        The query, stripped and cut to the longest the search allows.
    """
    return request.GET.get("q", "").strip()[:QUERY_MAX].strip()


def search_panel(request: HttpRequest) -> HttpResponse:
    """Render what the search dialog shows as the reader types.

    Args:
        request: The request, whose ``q`` parameter holds the query.

    Returns:
        The hints for an empty query, otherwise the groups that found something
        or the nothing-found state.
    """
    query = clean_query(request)
    groups = registry.default_registry.search(request, query, PANEL_LIMIT)
    return render(
        request,
        "mvp/search/panel.html",
        {
            "q": query,
            "kinds": registry.default_registry.active(),
            "groups": [group for group in groups if group.total],
        },
    )


class SearchView(MVPTemplateView):
    """The results page: every kind with what it found, or one kind in full."""

    template_name = "mvp/search/results.html"
    page_title = _("Search")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add the query, the narrowing links and the results to show."""
        context = super().get_context_data(**kwargs)
        query = clean_query(self.request)
        active = registry.default_registry.active()
        groups = registry.default_registry.search(self.request, query, RESULTS_LIMIT)
        narrowed = next(
            (kind for kind in active if kind.name == self.request.GET.get("kind")),
            None,
        )
        context.update(
            q=query,
            kinds=active,
            kind=narrowed,
            chips=[(group.kind, group.total) for group in groups],
            total=sum(group.total for group in groups),
        )
        if narrowed is None:
            context["groups"] = [group for group in groups if group.total]
        elif query:
            page = Paginator(narrowed.find(query, self.request), PAGE_SIZE).get_page(
                self.request.GET.get("page")
            )
            context["page_obj"] = page
            context["results"] = [narrowed.result(item) for item in page.object_list]
        return context
