"""Filtersets for the demo's list and table pages.

SKETCH (FS-041): one filterset serves the product list and the product table.
"""

import django_filters
from django.utils.translation import gettext_lazy as _
from mvp_forms.widgets import TomSelect, TomSelectMultiple

from mvp.filters import SearchFilter, SortFilter

from .models import Category, Product


def sku_choices():
    """Every SKU in the catalogue, read when the form is drawn."""
    skus = Product.objects.exclude(sku=None).order_by("sku").values_list("sku", flat=True)
    return [(sku, sku) for sku in skus]


class ProductFilter(django_filters.FilterSet):
    """Every way the product list can be narrowed or ordered."""

    q = SearchFilter(fields=["name", "description", "category__name"])
    status = django_filters.ChoiceFilter(choices=Product.STATUS_CHOICES, label=_("Status"))
    category = django_filters.ModelMultipleChoiceFilter(
        queryset=Category.objects.order_by("name"),
        label=_("Category"),
        widget=TomSelectMultiple(counted=True, none_text=_("Category")),
    )
    is_featured = django_filters.BooleanFilter(label=_("Featured only"))
    priority = django_filters.ChoiceFilter(
        choices=Product.PRIORITY_CHOICES,
        label=_("Priority"),
        widget=TomSelect(placeholder=_("Any priority"), clear_button=True),
    )
    sku = django_filters.MultipleChoiceFilter(
        method="filter_sku",
        label=_("SKU"),
        help_text=_("Type to find a SKU. The control counts the ones chosen."),
        widget=TomSelectMultiple(counted=True, none_text=_("Any SKU")),
    )
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

    def __init__(self, *args, **kwargs):
        """Read the SKUs on offer for this request."""
        super().__init__(*args, **kwargs)
        self.filters["sku"].extra["choices"] = sku_choices()

    def filter_sku(self, queryset, name, value):
        """Keep the products whose SKU was chosen."""
        return queryset.filter(sku__in=value) if value else queryset


class ProductQuickFilter(django_filters.FilterSet):
    """A short filterset: everything fits in the toolbar, so there is no modal."""

    q = SearchFilter(fields=["name", "description"])
    status = django_filters.ChoiceFilter(choices=Product.STATUS_CHOICES, label=_("Status"))
    is_featured = django_filters.BooleanFilter(label=_("Featured only"))
    o = ProductFilter.base_filters["o"]

    class Meta:
        model = Product
        fields: list[str] = []
