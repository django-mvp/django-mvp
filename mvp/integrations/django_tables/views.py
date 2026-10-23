"""django-tables2 integration: table-rendering list views.

Usage::

    from mvp.integrations.django_tables.views import MVPTableView


    class ProductTableView(MVPTableView):
        model = Product
        table_class = ProductTable
"""

from django.core.paginator import InvalidPage
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from django.views.generic.list import ListView

from mvp.filters import SortFilter
from mvp.integrations import missing_dependency
from mvp.views.list import MVPListViewMixin

try:
    from django_tables2.views import SingleTableMixin
except ImportError as e:
    raise missing_dependency("django_tables", "django-tables2") from e


class MVPTableViewMixin(MVPListViewMixin, SingleTableMixin):
    """Combines MVP list behavior (filterset/pagination) with django-tables2 rendering.

    Ordering belongs to the table: a table already has its own whitelisted
    ``order_by`` mechanism and sortable column headers. A view that declares
    ``order_by`` is refused by ``MVPListViewMixin`` with a message pointing at
    the table class's own ``order_by`` or ``Meta.order_by``. A ``SortFilter``
    on the view's filterset is dropped without an error, so the filterset a
    list page uses serves the table page unchanged.

    Pagination follows the same rule. The table paginates; the list view does
    not, and the page context the footer reads is republished from the table's
    own page. ``paginate_by`` is the one control: it sets the page size, and
    leaving it unset means no pagination rather than a size nobody chose.
    """

    base_template_name = "table_view.html"
    page_type = "table"

    def get_table_pagination(self, table):
        """Let the view's own configuration decide, including against.

        django-tables2 falls back to a page size of its own when a view names
        none, so a view that set neither ``paginate_by`` nor
        ``table_pagination`` was paginated at a size it had never chosen.
        Here that means no pagination at all.
        """
        if self.table_pagination is None and self.get_paginate_by(table.data) is None:
            return False
        pagination = super().get_table_pagination(table)
        if not isinstance(pagination, dict):  # table_pagination = False
            return False
        # Report an out-of-range page rather than landing quietly on the last
        # one — get_table turns that into the 404 a list view in this package
        # answers the same URL with.
        pagination["silent"] = False
        return pagination

    def get_table(self, **kwargs):
        """Build the table, answering a page that cannot exist with a 404.

        Left to itself, django-tables2 ignores a page number it cannot read
        and falls back to the last page for one past the end, where a list
        view in this package raises 404 for both. An absent or empty ``page``
        is page one, as it is anywhere else.
        """
        page = self.request.GET.get(getattr(self, "page_kwarg", "page"))
        if page and not page.isdigit():
            raise Http404(_("Page %(page)s is not a page number.") % {"page": page})
        try:
            return super().get_table(**kwargs)
        except InvalidPage as e:
            raise Http404(str(e)) from e

    def paginate_queryset(self, queryset, page_size):
        """Leave the queryset whole — the table is the only paginator here.

        Two paginators over one queryset means two slices, and a slice is a
        new queryset with an empty result cache: the row query and every
        prefetch on it run again for the second slice. The table's page is
        also the ordered one, since a column sort is applied when the table
        is built, after the list view would have taken its slice.
        """
        return None, None, queryset, False

    def get_result_count(self, context):
        """Count the table's rows without fetching them.

        The list view hands its queryset over whole and never paginates it,
        so measuring that queryset would load every row of the table to
        count them. The table counts its own data with one query, and its
        paginator reuses the answer.
        """
        return len(context["table"].rows)

    def get_filterset(self, filterset_class=None):
        """Return this request's filterset with every sort filter taken out.

        The table's column headers sort the rows, so a ``SortFilter`` on the
        filterset is neither drawn nor applied, and raises nothing: one
        filterset can serve a list page and a table page. The sort filters are
        removed from this instance before its form is built, and their names
        kept on ``dropped_filters`` so ``toolbar_filters`` can name them.

        Args:
            filterset_class: The class to build. Defaults to
                ``get_filterset_class()``.

        Returns:
            The bound filterset without its sort filters, or ``None`` when the
            view has none.
        """
        if hasattr(self, "_filterset"):
            return self._filterset
        filterset = super().get_filterset(filterset_class)
        self.dropped_filters = []
        if filterset is not None:
            self.dropped_filters = [
                name
                for name, flt in filterset.filters.items()
                if isinstance(flt, SortFilter)
            ]
            for name in self.dropped_filters:
                del filterset.filters[name]
        return filterset

    def get_context_data(self, **kwargs):
        """Republish the table's page under the names the page chrome reads.

        Also publishes ``table_sort``, the order the column headings chose for
        this request, or ``""``. The filter form submits only its own fields,
        so the page carries the order in it to keep a search or a filter from
        dropping it.
        """
        context = super().get_context_data(**kwargs)
        table = context["table"]
        context["table_sort"] = self.request.GET.get(table.prefixed_order_by_field, "")
        # A table with pagination turned off has no page, and then neither does the view.
        page = getattr(table, "page", None)
        if page is not None:
            context["paginator"] = page.paginator
            context["page_obj"] = page
            context["is_paginated"] = page.has_other_pages()
        return context


class MVPTableView(MVPTableViewMixin, ListView):
    """Concrete table view — subclass with ``model`` and ``table_class``."""
