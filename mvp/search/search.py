"""The module-level search over the site's registry."""

from __future__ import annotations

from django.http import HttpRequest

from mvp.search import registry
from mvp.search.kinds import Group


def search(request: HttpRequest, query: str, limit: int) -> list[Group]:
    """Search the site's active kinds.

    Args:
        request: The request the search is for.
        query: What the visitor typed.
        limit: The most results to put in each group.

    Returns:
        One group per active kind, in order, or an empty list for an empty query.
    """
    return registry.default_registry.search(request, query, limit)
