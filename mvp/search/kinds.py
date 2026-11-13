"""The shapes a search is built from: a result, a group of results and a kind.

A *kind* is one sort of thing a site can search for, such as its pages or its
people. Each kind answers a query for one request and returns what it found.
The search puts the answers side by side, one :class:`Group` per kind.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from modelsearch.backends import get_search_backend


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
            A sliceable, countable sequence, best match first.

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
        return Group(
            kind=self,
            results=[self.result(item) for item in found[:limit]],
            total=len(found),
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


class ModelKind(Kind):
    """A kind that searches the records of one model modelsearch indexes.

    Set :attr:`model` and define :meth:`get_queryset`. The model needs a
    ``FilterField`` on its primary key and no special manager. Override
    :meth:`title`, :meth:`url`, :meth:`where`, :meth:`passage` and
    :meth:`more_url` to change what each result carries.

    Attributes:
        model: The indexed model to search.
    """

    model: type[models.Model]

    def get_queryset(self, request: HttpRequest) -> models.QuerySet:
        """Return the records the request may see.

        Args:
            request: The request the search is for.

        Returns:
            A queryset of :attr:`model`. Any filter works, indexed or not.

        Raises:
            ImproperlyConfigured: Always, until a subclass defines it, so that
                no kind searches records nobody decided a request may see.
        """
        raise ImproperlyConfigured(
            f"{type(self).__name__} must define get_queryset(request), "
            "returning the records the request may see."
        )

    def find(self, query: str, request: HttpRequest) -> Sequence[models.Model]:
        """Search the visible records, by whole word and then by completion.

        Args:
            query: The cleaned query, never empty.
            request: The request the search is for.

        Returns:
            The matching records, best match first.

        Raises:
            ImproperlyConfigured: The kind does not define ``get_queryset``.
        """
        visible = self.get_queryset(request).values("pk")
        queryset = self.model._default_manager.filter(pk__in=visible)
        # modelsearch's SQLite backend passes a double quote into an FTS5 MATCH
        # and raises, so none reaches it.
        query = query.replace('"', "").strip()
        if not query:
            return []
        backend = get_search_backend()
        found = backend.search(query, queryset)
        indexed: Any = self.model
        if not found and indexed.get_autocomplete_search_fields():
            found = backend.autocomplete(query, queryset)
        return found

    def result(self, item: models.Model) -> Result:
        """Turn one record into a :class:`Result` from the methods below.

        Args:
            item: One record from :meth:`find`.

        Returns:
            The record as a result.
        """
        return Result(
            title=self.title(item),
            url=self.url(item),
            where=self.where(item),
            passage=self.passage(item),
        )

    def title(self, obj: models.Model) -> str:
        """Return what the record is called: ``str(obj)``."""
        return str(obj)

    def url(self, obj: models.Model) -> str:
        """Return where the record lives: ``obj.get_absolute_url()``."""
        return obj.get_absolute_url()  # type: ignore[attr-defined]

    def where(self, obj: models.Model) -> str:
        """Return the line saying where the record comes from: the model's name."""
        return str(obj._meta.verbose_name)

    def passage(self, obj: models.Model) -> str:
        """Return a line of text around the match: empty by default."""
        return ""
