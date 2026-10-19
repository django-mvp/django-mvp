"""Filtersets for the demo's list and table pages.

SKETCH (FS-041): one filterset serves the product list and the product table.
"""

import django_filters
from django.utils.translation import gettext_lazy as _

from mvp.filters import SearchFilter, SortFilter

from .models import Category, Product


class ProductFilter(django_filters.FilterSet):
    """Every way the product list can be narrowed or ordered."""

    q = SearchFilter(fields=["name", "description", "category__name"])
    status = django_filters.ChoiceFilter(choices=Product.STATUS_CHOICES, label=_("Status"))
    category = django_filters.ModelMultipleChoiceFilter(
        queryset=Category.objects.order_by("name"), label=_("Category")
    )
    is_featured = django_filters.BooleanFilter(label=_("Featured only"))
    priority = django_filters.ChoiceFilter(choices=Product.PRIORITY_CHOICES, label=_("Priority"))
    price = django_filters.RangeFilter(label=_("Price"))
    stock = django_filters.RangeFilter(label=_("Stock"))
    release_date = django_filters.DateFromToRangeFilter(label=_("Release date"))
    is_available = django_filters.BooleanFilter(label=_("Available"))
    o = SortFilter(
        options=[
            ("name", _("Name (A–Z)"), ["name", "pk"]),
            ("-name", _("Name (Z–A)"), ["-name", "-pk"]),
            ("price", _("Price, lowest first"), ["price", "pk"]),
            ("-price", _("Price, highest first"), ["-price", "-pk"]),
            ("-release_date", _("Newest first"), ["-release_date", "-pk"]),
        ]
    )

    class Meta:
        model = Product
        fields: list[str] = []


class ProductQuickFilter(django_filters.FilterSet):
    """A short filterset: everything fits in the toolbar, so there is no modal."""

    q = SearchFilter(fields=["name", "description"])
    status = django_filters.ChoiceFilter(choices=Product.STATUS_CHOICES, label=_("Status"))
    is_featured = django_filters.BooleanFilter(label=_("Featured only"))
    o = ProductFilter.base_filters["o"]

    class Meta:
        model = Product
        fields: list[str] = []
