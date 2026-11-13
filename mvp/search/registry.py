"""The kinds a site registers, and the search across them."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest

from mvp.config import MVP_CONFIG
from mvp.search.kinds import FunctionKind, Group, Kind, Result

QUERY_MAX = 100


class SearchRegistry:
    """The kinds registered for a site, in the order they were registered."""

    def __init__(self) -> None:
        """Start with no kinds."""
        self.kinds: dict[str, Kind] = {}

    def register(
        self,
        kind_or_function: Kind | Callable[[str, HttpRequest], Sequence[Result]],
        *,
        name: str | None = None,
        label: Any = None,
        icon: str | None = None,
        description: Any = "",
    ) -> Kind:
        """Register a kind, or wrap a function as one and register that.

        Args:
            kind_or_function: A :class:`~mvp.search.kinds.Kind` instance, or a
                function taking ``(query, request)`` and returning a list of
                :class:`~mvp.search.kinds.Result`.
            name: The kind's identifier. Required for a function.
            label: The kind's human name. Required for a function.
            icon: The icon name for the kind's results. Required for a function.
            description: An optional sentence about what the kind finds.

        Returns:
            The registered kind.

        Raises:
            ImproperlyConfigured: A kind is already registered under the name,
                or a function was given without a name, label and icon.
        """
        if isinstance(kind_or_function, Kind):
            kind = kind_or_function
        else:
            if not (name and label and icon):
                raise ImproperlyConfigured(
                    "Registering a search function needs a name, a label and an icon."
                )
            kind = FunctionKind(kind_or_function, name, label, icon, description)
        if kind.name in self.kinds:
            raise ImproperlyConfigured(
                f"A search kind named {kind.name!r} is already registered."
            )
        self.kinds[kind.name] = kind
        return kind

    def registered(self) -> list[Kind]:
        """Return every registered kind, in registration order."""
        return list(self.kinds.values())

    def active(self) -> list[Kind]:
        """Return the kinds a search uses.

        Returns:
            The kinds ``MVP_CONFIG["search"]["kinds"]`` names, in that order, or
            every registered kind when the setting is empty. A name no kind is
            registered under is skipped.
        """
        names = MVP_CONFIG["search"]["kinds"]  # type: ignore[index]
        if not names:
            return self.registered()
        return [self.kinds[name] for name in names if name in self.kinds]

    def search(self, request: HttpRequest, query: str, limit: int) -> list[Group]:
        """Search every active kind for a query.

        The query is stripped and cut to ``QUERY_MAX`` characters before any
        kind sees it. Nothing is ranked across kinds.

        Args:
            request: The request the search is for.
            query: What the visitor typed.
            limit: The most results to put in each group.

        Returns:
            One group per active kind, in order, or an empty list when the query
            is empty. An error raised by a kind is not caught.
        """
        query = query.strip()[:QUERY_MAX].strip()
        if not query:
            return []
        return [kind.group(query, request, limit) for kind in self.active()]


default_registry = SearchRegistry()


def register(
    kind_or_function: Kind | Callable[[str, HttpRequest], Sequence[Result]],
    *,
    name: str | None = None,
    label: Any = None,
    icon: str | None = None,
    description: Any = "",
) -> Kind:
    """Register a kind with the site's registry. See :meth:`SearchRegistry.register`."""
    return default_registry.register(
        kind_or_function,
        name=name,
        label=label,
        icon=icon,
        description=description,
    )


def registered() -> list[Kind]:
    """Return the site's registered kinds. See :meth:`SearchRegistry.registered`."""
    return default_registry.registered()
