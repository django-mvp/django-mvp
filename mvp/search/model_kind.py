"""The kind that searches the records of one model modelsearch indexes."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.http import HttpRequest
from modelsearch.backends import get_search_backend

from mvp.search.kinds import Kind, Result


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
        if not found.count() and indexed.get_autocomplete_search_fields():
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
