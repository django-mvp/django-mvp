"""Filters the package ships for a list page's filterset.

SKETCH (FS-041): prototype code, not tested. The build rewrites this test-first.
"""

from collections.abc import Sequence

import django_filters
from django.db.models import Q, QuerySet
from django.utils.translation import gettext_lazy as _


class SearchFilter(django_filters.CharFilter):
    """Match any word of the term against any of the named fields.

    The same rule the list page's search box has always followed: ignoring
    case, a record matching any word in any field is shown once, and only the
    first ``max_words`` words are searched.
    """

    def __init__(self, *args, fields: Sequence[str] = (), max_words: int = 10, **kwargs):
        kwargs.setdefault("label", _("Search"))
        super().__init__(*args, **kwargs)
        self.search_fields = list(fields)
        self.max_words = max_words

    def filter(self, qs: QuerySet, value: str) -> QuerySet:
        """Narrow ``qs`` to the records that match ``value``."""
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

    Each option is ``(key, label, columns)``. ``columns`` is one ordering
    expression or several, the later ones deciding ties. Only the key ever
    appears in the address; the columns never come from it.
    """

    def __init__(self, *args, options: Sequence[tuple] = (), **kwargs):
        self.options = list(options)
        kwargs.setdefault("label", _("Sort"))
        kwargs["choices"] = [(key, label) for key, label, _cols in self.options]
        kwargs.setdefault("empty_label", None)
        super().__init__(*args, **kwargs)

    def filter(self, qs: QuerySet, value: str) -> QuerySet:
        """Order ``qs`` by the option ``value`` names."""
        for key, _label, columns in self.options:
            if key == value:
                if isinstance(columns, (list, tuple)):
                    return qs.order_by(*columns)
                return qs.order_by(columns)
        return qs
