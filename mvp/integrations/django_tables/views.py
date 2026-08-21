"""django-tables2 integration: table-rendering list views.

Usage::

    from mvp.integrations.django_tables.views import MVPTableView


    class ProductTableView(MVPTableView):
        model = Product
        table_class = ProductTable
"""

from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import InvalidPage
from django.http import Http404
from django.utils.translation import gettext_lazy as _
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
    surface for the same thing. The sort control disappears as a consequence
    rather than by a separate decision — it draws itself from
    ``order_by_choices``, which a view that cannot declare ``order_by`` never
    has. The table's own sortable column headers cover it.

    Pagination follows the same rule. The table paginates; the list view does
    not, and the page context the footer reads is republished from the table's
    own page. ``paginate_by`` is the one control: it sets the page size, and
    leaving it unset means no pagination rather than a size nobody chose.
    """

    base_template_name = "table_view.html"

    def __init_subclass__(cls, **kwargs):
        """Refuse a view-level ordering as the class is defined.

        Checking here rather than in ``__init__`` means Django raises while
        importing the module that declares the view, instead of on the first
        request to its URL.
        """
        super().__init_subclass__(**kwargs)
        if cls.order_by:
            raise ImproperlyConfigured(
                f"{cls.__name__} declares 'order_by', but a table "
                "view must not — ordering belongs on the table class, via its "
                "own 'order_by' or Meta.order_by."
            )

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Republish the table's page under the names the page chrome reads, so
        # the count and the pagination links describe the rows on screen. A
        # table with pagination turned off has no page, and then neither does
        # the view.
        page = getattr(context["table"], "page", None)
        if page is not None:
            context["paginator"] = page.paginator
            context["page_obj"] = page
            context["is_paginated"] = page.has_other_pages()
        return context


class MVPTableView(MVPTableViewMixin, ListView):
    """Concrete table view — subclass with ``model`` and ``table_class``."""
