"""django-filter integration: filterable list views.

Usage::

    from mvp.integrations.django_filters.views import MVPFilteredListView


    class ProductListView(MVPFilteredListView):
        model = Product
        filterset_class = ProductFilter
"""

from mvp.integrations import missing_dependency
from mvp.views.list import MVPListViewMixin

try:
    from django_filters.views import FilterView
except ImportError as e:
    raise missing_dependency("django_filters", "django-filter") from e


class MVPFilteredListView(MVPListViewMixin, FilterView):
    """List view combining MVP list behavior with django-filter's FilterView.

    The filter chrome — the button's applied-count badge and the modal's
    "Clear filters" link — comes from ``FilterContextMixin``, which
    ``MVPListViewMixin`` carries. Composing that mixin with ``FilterView``
    yourself gets the same behavior; this class is the shorthand.
    """
