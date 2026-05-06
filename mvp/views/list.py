"""Views and view mixins for django-mvp."""

from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView

from .base import BaseTemplateNameMixin, PageMixin
from .detail import CRUDDirectoryMixin


class SearchMixin:
    """Django admin-style multi-word OR text search for list views.

    Reads ``?q=`` and applies case-insensitive substring (``icontains``) matching
    across all declared ``search_fields``. Multi-word queries use OR semantics —
    a record is included if any word matches any field. Calls ``.distinct()`` to
    deduplicate records that match via multiple fields.

    When ``search_fields`` is ``None`` or empty the mixin is a complete no-op:
    the queryset is returned unmodified. The context sentinels ``is_searchable``
    and ``search_query`` are **always** injected regardless of configuration.

    Config:
        search_fields (list[str] | None): ORM field paths to search across.
            Supports relationship traversal (e.g. ``"category__name"``).
            Default: ``None`` (mixin is a no-op).

    Override hooks:
        get_search_fields(): Return the effective field list dynamically.

    Context (always injected):
        is_searchable (bool): ``True`` when ``search_fields`` is configured.
        search_query (str): Raw ``?q=`` value, or ``""`` if absent.

    Query parameters:
        ?q: Search term. Stripped before filtering; split on whitespace for
            multi-word OR matching.

    Example::

        class ProductListView(SearchMixin, ListView):
            model = Product
            search_fields = ["name", "description", "category__name"]
    """

    search_fields = None

    def get_search_fields(self):
        """Return the list of fields to search across.

        Returns:
            list[str] or None: List of field names for search
        """
        return self.search_fields

    def get_queryset(self):
        """Apply search filtering to the queryset.

        Returns:
            QuerySet: Filtered queryset
        """
        queryset = super().get_queryset()

        # Apply search filtering
        search_term = self.request.GET.get("q", "").strip()
        if search_term and self.get_search_fields():
            queryset = self._apply_search(queryset, search_term)

        return queryset

    def _apply_search(self, queryset, search_term):
        """Apply search filtering across search_fields.

        Similar to Django admin's search functionality, this builds an OR query
        across all specified fields using case-insensitive contains lookups.
        For multi-word searches, applies OR matching across all words and fields.

        Args:
            queryset: The queryset to filter
            search_term: The search string (can contain multiple words)

        Returns:
            QuerySet: Filtered queryset
        """
        search_query = Q()

        # Split search term by any whitespace to support multi-word OR matching
        words = search_term.split()

        for word in words:
            for field in self.get_search_fields():
                search_query |= Q(**{f"{field}__icontains": word})

        return queryset.filter(search_query).distinct()

    def get_context_data(self, **kwargs):
        """Add search data to the template context.

        Adds:
            search_query (str): Current search term
        """
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")
        context["is_searchable"] = bool(self.search_fields)
        return context


class OrderMixin:
    """Whitelist-only safe column ordering for list views via ``?o=``.

    Each permitted ordering is declared as a three-tuple
    ``(public_key, label, orm_expression)``:

    * ``public_key`` — matched against the ``?o=`` query parameter; may be any
      URL-safe string and need not match a database column name.
    * ``label`` — human-readable display string for ordering UI controls.
    * ``orm_expression`` — the value passed to ``queryset.order_by()``. This is
      a developer-declared constant and is **never** exposed in the URL.

    **Security guarantee**: the raw ``?o=`` value is never passed to the ORM.
    Only the ``orm_expression`` of the matching whitelist entry is used.
    Unrecognised ``?o=`` values are silently ignored.

    When ``order_by`` is ``None`` or empty the mixin is a complete no-op.
    Context variables are only injected when ``order_by`` is configured.

    Config:
        order_by (list[tuple[str, str, str]] | None): Whitelist of permitted
            ordering options. Each entry is ``(public_key, label, orm_expression)``.
            Default: ``None`` (mixin is a no-op).

    Override hooks:
        get_order_by_choices(): Return the effective whitelist dynamically.

    Context (only when ``order_by`` is configured):
        order_by_choices (list[tuple[str, str, str]]): Full whitelist as declared.
        current_ordering (str): Matched public_key for the active ``?o=``, or
            ``""`` if absent or unrecognised.

    Query parameters:
        ?o: Public key of the desired ordering. Ignored if not in the whitelist.

    Example::

        class ProductListView(OrderMixin, ListView):
            model = Product
            order_by = [
                ("name_asc", "Name (A–Z)", "name"),
                ("name_desc", "Name (Z–A)", "-name"),
                ("newest", "Newest First", "-created_at"),
            ]
    """

    order_by = None

    def get_order_by_choices(self):
        """Return the list of ordering choices.

        Returns:
            list[tuple[str, str]] or None: List of (ordering, label) tuples
        """
        return self.order_by

    def get_queryset(self):
        """Apply ordering to the queryset.

        Returns:
            QuerySet: Ordered queryset
        """
        queryset = super().get_queryset()

        # Apply ordering
        ordering = self.request.GET.get("o", "")
        if ordering and self.get_order_by_choices():
            queryset = self._apply_ordering(queryset, ordering)

        return queryset

    def _apply_ordering(self, queryset, ordering):
        """Apply ordering to the queryset.

        Validates that the ordering value matches a public_key in the configured
        order_by choices before applying the corresponding orm_expression.
        The raw ``?o=`` value is NEVER passed directly to the ORM.

        Args:
            queryset: The queryset to order
            ordering: The public_key value from the ``?o=`` query parameter

        Returns:
            QuerySet: Ordered queryset
        """
        for choice in self.get_order_by_choices():
            if choice[0] == ordering:
                return queryset.order_by(choice[2])

        return queryset

    def get_context_data(self, **kwargs):
        """Add ordering data to the template context.

        Adds (only when ``order_by`` is configured):
            order_by_choices (list[tuple[str, str, str]]): Full three-tuple list of
                available ordering options.
            current_ordering (str): The matched public_key for the current ``?o=``
                parameter value, or ``""`` if the value is absent or unrecognised.
        """
        context = super().get_context_data(**kwargs)

        order_by_choices = self.get_order_by_choices()
        if order_by_choices:
            context["order_by_choices"] = order_by_choices
            raw_o = self.request.GET.get("o", "")
            valid_keys = {choice[0] for choice in order_by_choices}
            context["current_ordering"] = raw_o if raw_o in valid_keys else ""

        return context


class SearchOrderMixin(SearchMixin, OrderMixin):
    """Combined text search and safe column ordering for list views.

    Composes ``SearchMixin`` (``?q=``) and ``OrderMixin`` (``?o=``) into a
    single convenience mixin. Both parameters work independently and combine
    transparently: ``?q=foo&o=name_asc`` returns filtered and ordered results.

    **MRO evaluation order** (``SearchMixin`` left of ``OrderMixin`` is fixed):

    1. ``OrderMixin.get_queryset()`` runs first (innermost ``super()`` call),
       applying the ORM ordering expression.
    2. ``SearchMixin.get_queryset()`` runs second, applying the search filter
       and ``.distinct()`` on top of the ordered queryset.

    This ordering avoids the PostgreSQL ``SELECT DISTINCT + ORDER BY on JOIN
    columns`` error that would occur if distinct were applied before ordering.

    When positioned left of ``django_filters.views.FilterView`` in the MRO
    (e.g. ``class MyView(SearchOrderMixin, FilterView)``), both mixins compose
    correctly: the filterset's ``qs`` is built from the search + ordering
    queryset returned by ``get_queryset()``.

    Config:
        search_fields (list[str] | None): See ``SearchMixin``. Default: ``None``.
        order_by (list[tuple[str, str, str]] | None): See ``OrderMixin``.
            Default: ``None``.

    Override hooks:
        get_search_fields(): Inherited from ``SearchMixin``.
        get_order_by_choices(): Inherited from ``OrderMixin``.

    Query parameters:
        ?q: Search term — see ``SearchMixin``.
        ?o: Ordering public_key — see ``OrderMixin``.

    Example::

        class ProductListView(SearchOrderMixin, ListView):
            model = Product
            search_fields = ["name", "description"]
            order_by = [
                ("name_asc", "Name (A–Z)", "name"),
                ("name_desc", "Name (Z–A)", "-name"),
            ]


        # With django_filters:
        class ProductFilteredListView(SearchOrderMixin, FilterView):
            model = Product
            filterset_fields = ["category"]
            search_fields = ["name"]
            order_by = [("name_asc", "Name (A–Z)", "name")]
    """

    pass


class ListItemTemplateMixin:
    """Mixin for providing list item template resolution for list views.

    This mixin automatically resolves the template to use for rendering
    individual list items in a list view. It follows Django's convention
    of app_label/model_name pattern.

    Attributes:
        list_item_template (str): Explicit template path for list items.
            If None, template is auto-generated via get_list_item_template().
            Default: None (auto-generate).

    Example:
        class MyListView(ListItemTemplateMixin, ListView):
            model = Product
            # Will automatically use: 'myapp/list_product_item.html'

        class CustomListView(ListItemTemplateMixin, ListView):
            model = Product
            list_item_template = 'custom/product_card.html'

        class OverrideListView(ListItemTemplateMixin, ListView):
            model = Product

            def get_list_item_template(self):
                # Custom logic for template selection
                if self.request.GET.get('compact'):
                    return 'myapp/compact_product_item.html'
                return 'myapp/full_product_item.html'

    Template Context:
        list_item_template (str): The resolved template path for list items
    """

    list_item_template = None

    def get_list_item_template(self):
        """Return the template path for rendering individual list items.

        If list_item_template is explicitly set, it is used.
        Otherwise, generates a template path following the pattern:
        '<app_label>/list_<model_name>_item.html'

        Returns:
            str: Template path for list item

        Raises:
            AttributeError: If model is not defined on the view
        """
        if self.list_item_template:
            return self.list_item_template

        # Auto-generate template name from model
        if not hasattr(self, "model") or self.model is None:
            msg = (
                f"{self.__class__.__name__} is missing a model. "
                "Define {0}.model or override "
                "{0}.get_list_item_template()."
            ).format(self.__class__.__name__)
            raise AttributeError(msg)

        opts = self.model._meta
        return f"{opts.app_label}/{opts.model_name}_list_item.html"

    def get_context_data(self, **kwargs):
        """Add list item template to the template context.

        Adds:
            list_item_template (str): Template path for rendering list items
        """
        context = super().get_context_data(**kwargs)
        context["list_item_template"] = self.get_list_item_template()
        return context


class MVPListViewMixin(BaseTemplateNameMixin, SearchOrderMixin, CRUDDirectoryMixin, PageMixin, ListItemTemplateMixin):
    """Foundation mixin for django-mvp list views with search, ordering, pagination, and AdminLTE styling.

    Composes ``SearchOrderMixin``, ``CRUDDirectoryMixin``, ``PageMixin``, and
    ``ListItemTemplateMixin`` into a single class. Renders to the
    ``list_view.html`` base template with optional card-grid layout, empty-state
    messaging, and breadcrumb auto-generation.

    Config:
        search_fields (list[str] | None): ORM field paths for ``?q=`` search.
            Default: ``None`` (search disabled).
        order_by (list[tuple[str, str, str]] | None): Three-tuple whitelist for
            ``?o=`` ordering. Each entry is ``(public_key, label, orm_expression)``.
            Default: ``None`` (ordering disabled).
        grid (dict): Bootstrap grid kwargs passed to the list template
            (e.g. ``{"cols": 1, "md": 2, "gap": 3}``). Default: ``{}``
            (single-column layout).
        paginate_by (int | None): Records per page. Default: ``None`` (no
            pagination; inherited from ``ListView``).
        create_view_name (str): URL name template for the "Add" button.
            Default: ``"{model_name}-create"``.
        empty_state_heading (str | None): Heading shown when the queryset is
            empty. Default: translatable "There's nothing here yet".
        empty_state_message (str | None): Body text for the empty state.
            Default: translatable prompt to add the first record.
        directory (list[str]): CRUD action names exposed in the ``CRUDDirectoryMixin``
            context. Default: ``["create"]``.

    Override hooks:
        get_grid_config(): Return the grid layout dict.
        get_empty_state_heading(): Return the empty-state heading string.
        get_empty_state_message(): Return the empty-state body string.
        get_page_title(): Return the page title (defaults to model verbose_name_plural).
        get_breadcrumbs(): Return the breadcrumb list.
        get_search_fields(): Inherited from ``SearchMixin``.
        get_order_by_choices(): Inherited from ``OrderMixin``.

    Example::

        class ProductListView(MVPListViewMixin, ListView):
            model = Product
            search_fields = ["name", "description"]
            order_by = [
                ("name_asc", "Name (A-Z)", "name"),
                ("name_desc", "Name (Z-A)", "-name"),
            ]
            grid = {"cols": 1, "md": 2, "xl": 3, "gap": 3}
            paginate_by = 24


        # With django_filters:
        class ProductFilteredListView(MVPListViewMixin, FilterView):
            model = Product
            filterset_fields = ["category"]
            search_fields = ["name"]
            order_by = [("name_asc", "Name (A-Z)", "name")]
    """

    grid: dict = {}
    base_template_name = "list_view.html"
    create_view_name: str = "{model_name}-create"
    empty_state_heading: str | None = _("There's nothing here yet")
    empty_state_message: str | None = _("You haven't added any records yet. Click the button below to get started.")
    directory = ["create"]

    def get_context_data(self, **kwargs):
        """Add grid configuration to the template context.

        Adds:
            grid_config (GridConfig): Configuration for grid layout
        """
        context = super().get_context_data(**kwargs)
        context["grid_config"] = self.get_grid_config()
        context["empty_state"] = {
            "heading": self.get_empty_state_heading(),
            "message": self.get_empty_state_message(),
        }
        return context

    def get_empty_state_heading(self) -> str | None:
        return self.empty_state_heading

    def get_empty_state_message(self) -> str | None:
        return self.empty_state_message

    def get_grid_config(self):
        return self.grid

    def get_page_title(self):
        if self.page_title:
            return self.page_title

        model = getattr(self, "model", None)
        if model:
            return model._meta.verbose_name_plural.title()

        return self.page_title

    def get_breadcrumbs(self):
        return super().get_breadcrumbs() + [
            {"text": _("Home"), "href": "/"},
            {"text": self.get_page_title()},
        ]


class MVPListView(MVPListViewMixin, ListView):
    """Default list view class for django-mvp, combining search, ordering, pagination, and AdminLTE styling."""

    pass


try:
    from django_filters.views import FilterView
except ImportError:
    pass
else:

    class MVPFilteredListView(MVPListViewMixin, FilterView):
        """List view class that combines MVPListView with django-filter's FilterView for advanced filtering capabilities."""

        pass
