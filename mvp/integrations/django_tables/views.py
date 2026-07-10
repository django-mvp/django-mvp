"""django-tables2 integration: table-rendering list views.

Usage::

    from mvp.integrations.django_tables.views import MVPTableView


    class ProductTableView(MVPTableView):
        model = Product
        table_class = ProductTable
"""

from django.views.generic.list import ListView

from mvp.integrations import missing_dependency
from mvp.views.list import MVPListViewMixin

try:
    from django_tables2.views import SingleTableMixin
except ImportError as e:
    raise missing_dependency("django_tables", "django-tables2") from e


class MVPTableViewMixin(MVPListViewMixin, SingleTableMixin):
    """Combines MVP list behavior (search/order/pagination) with django-tables2 rendering."""

    base_template_name = "table_view.html"


class MVPTableView(MVPTableViewMixin, ListView):
    """Concrete table view — subclass with ``model`` and ``table_class``."""
