"""Views and view mixins for django-mvp."""

from django.db.models import Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView

from .generic import BaseTemplateNameMixin, PageMixin


class SearchMixin:
    """Mixin for handling search functionality on list views.

    This mixin provides search functionality similar to Django admin's
    search_fields, using the 'q' query parameter.

    Attributes:
        search_fields (list[str]): List of model field names to search across.
            Supports relationship lookups (e.g., 'descriptions__value').
            Default: None (no search).

    Example:
        class MyListView(SearchMixin, ListView):
            model = MyModel
            search_fields = ['name', 'description', 'related__field']

    Query Parameters:
        q (str): Search term to filter results across search_fields
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
    """Mixin for handling ordering functionality on list views.

    This mixin provides ordering capabilities using the 'o' query parameter.

    Attributes:
        order_by (list[tuple[str, str]]): List of (ordering, label) tuples
            defining available ordering options. The ordering value should be
            a field name with optional '-' prefix for descending order.
            Default: None (no ordering).

    Example:
        class MyListView(OrderMixin, ListView):
            model = MyModel
            order_by = [
                ('name', 'Name A-Z'),
                ('-name', 'Name Z-A'),
                ('created', 'Oldest First'),
                ('-created', 'Newest First'),
            ]

    Query Parameters:
        o (str): Ordering value from the order_by choices
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

        Validates that the ordering value exists in the configured order_by
        choices before applying it to prevent arbitrary field ordering.

        Args:
            queryset: The queryset to order
            ordering: The ordering field name (with optional '-' prefix)

        Returns:
            QuerySet: Ordered queryset
        """
        # Validate ordering is in allowed choices
        valid_orderings = [choice[0] for choice in self.get_order_by_choices()]
        if ordering in valid_orderings:
            return queryset.order_by(ordering)

        return queryset

    def get_context_data(self, **kwargs):
        """Add ordering data to the template context.

        Adds:
            order_by_choices (list): Available ordering options
            current_ordering (str): Currently active ordering
        """
        context = super().get_context_data(**kwargs)

        # Add ordering context
        order_by_choices = self.get_order_by_choices()
        if order_by_choices:
            context["order_by_choices"] = order_by_choices
            context["current_ordering"] = self.request.GET.get("o", "")

        return context


class SearchOrderMixin(SearchMixin, OrderMixin):
    """Combined mixin for handling both search and ordering on list views.

    This mixin combines SearchMixin and OrderMixin to provide both search
    and ordering functionality using query parameters 'q' for search and 'o'
    for ordering.

    Attributes:
        search_fields (list[str]): List of model field names to search across.
            Supports relationship lookups (e.g., 'descriptions__value').
            Default: None (no search).
        order_by (list[tuple[str, str]]): List of (ordering, label) tuples
            defining available ordering options. The ordering value should be
            a field name with optional '-' prefix for descending order.
            Default: None (no ordering).

    Example:
        class MyListView(SearchOrderMixin, ListView):
            model = MyModel
            search_fields = ['name', 'description', 'related__field']
            order_by = [
                ('name', 'Name A-Z'),
                ('-name', 'Name Z-A'),
                ('created', 'Oldest First'),
                ('-created', 'Newest First'),
            ]

    Query Parameters:
        q (str): Search term to filter results across search_fields
        o (str): Ordering value from the order_by choices
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


class MVPListViewMixin(BaseTemplateNameMixin, SearchOrderMixin, PageMixin, ListItemTemplateMixin):
    grid: dict = {}
    base_template_name = "list_view.html"
    create_view_name: str = "{model_name}-create"
    empty_state_heading: str | None = _("There's nothing here yet")
    empty_state_message: str | None = _("You haven't added any records yet. Click the button below to get started.")

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
        context["create_url"] = self.get_create_url()
        return context

    def get_create_view_name(self) -> str:
        if not getattr(self, "model", None):
            return ""
        app_name, model_name = self.model._meta.app_label, self.model._meta.model_name
        return self.create_view_name.format(app_name=app_name, model_name=model_name)

    def get_create_url(self):
        create_view_name = self.get_create_view_name()
        if create_view_name:
            return reverse(create_view_name)
        return ""

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
    import django_filters  # noqa
except ImportError:
    pass
else:
    from django_filters.views import FilterView

    class MVPFilteredListView(MVPListViewMixin, FilterView):
        """List view class that combines MVPListView with django-filter's FilterView for advanced filtering capabilities."""

        pass
