"""django-tables2 integration: table-rendering list views.

Usage::

    from mvp.integrations.django_tables.views import MVPTableView


    class ProductTableView(MVPTableView):
        model = Product
        table_class = ProductTable
"""

from django.core.exceptions import ImproperlyConfigured
from django.views.generic.list import ListView

from mvp.integrations import missing_dependency
from mvp.views.list import MVPListViewMixin

try:
    from django_tables2.views import SingleTableMixin
except ImportError as e:
    raise missing_dependency("django_tables", "django-tables2") from e


class MVPTableViewMixin(MVPListViewMixin, SingleTableMixin):
    """Combines MVP list behavior (search/order/pagination) with django-tables2 rendering.

    Ordering is refused: a table already has its own whitelisted ``order_by``
    mechanism, and declaring one on the view too would be a second, competing
    surface for the same thing. The default action set drops sort for the
    same reason — the table's own sortable column headers already cover it.
    """

    base_template_name = "table_view.html"
    actions = ["search", "filter", "create"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.order_by:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} declares 'order_by', but a table "
                "view must not — ordering belongs on the table class, via its "
                "own 'order_by' or Meta.order_by."
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["actions"] = self.actions
        return context


class MVPTableView(MVPTableViewMixin, ListView):
    """Concrete table view — subclass with ``model`` and ``table_class``."""
