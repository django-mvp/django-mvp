"""Filters the package ships for a list page's filterset.

A list view takes its search, its sort and its filters from one django-filter
filterset. These are the two a filterset declares its search and its sort with.

Example::

    import django_filters
    from mvp.filters import SearchFilter, SortFilter


    class ProductFilter(django_filters.FilterSet):
        q = SearchFilter(fields=["name", "description", "category__name"])
        o = SortFilter(
            options=[
                ("name", "Name (A-Z)", ["name", "pk"]),
                ("-price", "Price, highest first", ["-price", "pk"]),
            ]
        )

        class Meta:
            model = Product
            fields = ["status"]
"""

from collections.abc import Sequence
from typing import Any

import django_filters
from django.db.models import Q, QuerySet
from django.utils.translation import gettext_lazy as _


class SearchFilter(django_filters.CharFilter):
    """Match any word of the term against any of the named fields.

    Ignoring case, a record in which some word of the term appears in some
    named field is kept, once, however many fields or joined rows it matched.
    Only the first ``max_words`` words are searched: one condition is built per
    word per field, and the term comes from the address, so without a bound the
    reader would choose how deep the query is.

    Args:
        *args: Passed to ``CharFilter``.
        fields: The ORM paths to search, such as ``"category__name"``.
        max_words: How many words of the term are searched.
        **kwargs: Passed to ``CharFilter``. ``label`` defaults to "Search".
    """

    def __init__(
        self,
        *args: Any,
        fields: Sequence[str] = (),
        max_words: int = 10,
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("label", _("Search"))
        super().__init__(*args, **kwargs)
        self.search_fields = list(fields)
        self.max_words = max_words

    def filter(self, qs: QuerySet, value: str) -> QuerySet:
        """Keep the records that match some word of ``value``.

        Args:
            qs: The queryset to narrow.
            value: The search term.

        Returns:
            The matching records, each once, or ``qs`` unchanged for an empty
            term or a filter with no fields.
        """
        words = (value or "").split()[: self.max_words]
        if not words or not self.search_fields:
            return qs
        query = Q()
        for word in words:
            for field in self.search_fields:
                query |= Q(**{f"{field}__icontains": word})
        return qs.filter(query).distinct()


class SortFilter(django_filters.ChoiceFilter):
    """Order the list by one of a fixed set of options.

    Each option is ``(key, label, columns)``. The key is what the address
    carries, the label is what the reader picks, and ``columns`` is one
    ordering expression or a sequence of them, the later ones deciding ties.
    A single column is not a total order unless it is unique, so an option
    meant to survive pagination ends with a unique column, usually ``"pk"``.

    The columns never come from the address. A value that is not one of the
    keys fails the field's choice validation, so it never reaches ``filter()``
    and the list keeps its default order. A list view never counts the sort
    as an applied filter.

    Args:
        *args: Passed to ``ChoiceFilter``.
        options: The ``(key, label, columns)`` triples, in the order offered.
        **kwargs: Passed to ``ChoiceFilter``. ``label`` defaults to "Sort";
            ``choices`` comes from ``options`` and there is no empty choice.
    """

    def __init__(
        self,
        *args: Any,
        options: Sequence[tuple[str, Any, Any]] = (),
        **kwargs: Any,
    ) -> None:
        self.options = list(options)
        kwargs.setdefault("label", _("Sort"))
        kwargs["choices"] = [(key, label) for key, label, _columns in self.options]
        kwargs.setdefault("empty_label", None)
        super().__init__(*args, **kwargs)

    def filter(self, qs: QuerySet, value: str) -> QuerySet:
        """Order ``qs`` by the columns of the option ``value`` names.

        Args:
            qs: The queryset to order.
            value: An option's key, already validated against the choices.

        Returns:
            The ordered queryset, or ``qs`` unchanged when no option is chosen.
        """
        for key, _label, columns in self.options:
            if key == value:
                if isinstance(columns, (list, tuple)):
                    return qs.order_by(*columns)
                return qs.order_by(columns)
        return qs
