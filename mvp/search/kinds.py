"""The shapes a search is built from: a result, a group of results and a kind.

A *kind* is one sort of thing a site can search for, such as its pages or its
people. Each kind answers a query for one request and returns what it found.
The search puts the answers side by side, one :class:`Group` per kind.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from django.core.paginator import Paginator
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _


@dataclass(frozen=True)
class Result:
    """One thing a search found.

    Attributes:
        title: What the result is called.
        url: Where the result lives.
        where: A short line saying where it comes from, such as a section name.
        passage: A line of text around the match, or an empty string.
    """

    title: str
    url: str
    where: str
    passage: str = ""


@dataclass(frozen=True)
class Group:
    """What one kind found for one query.

    Attributes:
        kind: The kind that answered.
        results: The results to show, at most the limit asked for.
        total: How many results the kind found in all.
        more_url: Where to see all of them, or ``None`` when the kind gives none.
    """

    kind: Kind
    results: Sequence[Any]
    total: int
    more_url: str | None

    @property
    def more(self) -> int:
        """How many results are found but not shown."""
        return self.total - len(self.results)


class Kind:
    """One kind of result a site can be searched for.

    Subclass it, set the class attributes and define :meth:`find`. Register an
    instance with :func:`mvp.search.register`.

    Attributes:
        name: The kind's identifier. Unique among registered kinds, and the
            value ``MVP_CONFIG["search"]["kinds"]`` and the ``kind`` query
            parameter use.
        label: The human name of the kind, a lazy translation.
        icon: The icon name shown beside the kind's results.
        description: An optional sentence about what the kind finds, a lazy
            translation.
    """

    name: str
    label: Any
    icon: str
    description: Any = ""

    def find(self, query: str, request: HttpRequest) -> Sequence[Any]:
        """Find what matches the query.

        Args:
            query: The cleaned query, never empty.
            request: The request the search is for. Decide what it may see from it.

        Returns:
            A sliceable sequence, best match first. One with a ``count()``
            method is counted by it, and never measured with ``len()``.

        Raises:
            NotImplementedError: Always, until a subclass defines it.
        """
        raise NotImplementedError(f"{type(self).__name__} must define find().")

    def result(self, item: Any) -> Result:
        """Turn one item :meth:`find` returned into a :class:`Result`.

        Args:
            item: One item from :meth:`find`.

        Returns:
            The item as a result. The default expects it to be one already.
        """
        return item

    def more_url(self, query: str) -> str | None:
        """Return where to see every result for the query, if this kind knows.

        Args:
            query: The cleaned query.

        Returns:
            An address, or ``None`` to let the results page stand in.
        """
        return None

    def group(self, query: str, request: HttpRequest, limit: int) -> Group:
        """Build the group of results for a query.

        Args:
            query: The cleaned query.
            request: The request the search is for.
            limit: The most results to put in the group.

        Returns:
            The group, holding at most ``limit`` results and the full total.
        """
        found = self.find(query, request)
        total = Paginator(found, limit).count
        return Group(
            kind=self,
            results=[self.result(item) for item in found[:limit]] if total else [],
            total=total,
            more_url=self.more_url(query),
        )


class FunctionKind(Kind):
    """A kind answered by a plain function.

    The function takes ``(query, request)`` and returns a list of
    :class:`Result`.
    """

    def __init__(
        self,
        function: Callable[[str, HttpRequest], Sequence[Result]],
        name: str,
        label: Any,
        icon: str,
        description: Any = "",
    ) -> None:
        """Wrap a function as a kind.

        Args:
            function: Called with the query and the request.
            name: The kind's identifier.
            label: The human name of the kind.
            icon: The icon name for the kind's results.
            description: An optional sentence about what the kind finds.
        """
        self.function = function
        self.name = name
        self.label = _(label)
        self.icon = icon
        self.description = _(description)

    def find(self, query: str, request: HttpRequest) -> Sequence[Result]:
        """Call the wrapped function."""
        return self.function(query, request)
