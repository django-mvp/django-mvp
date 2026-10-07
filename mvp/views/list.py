"""List views and the search, ordering and filter mixins they compose."""

from typing import Any

from django import forms
from django.db.models import Model, Q, QuerySet
from django.utils import formats
from django.utils.choices import flatten_choices
from django.utils.functional import Promise
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

    Only the first ``max_search_words`` words of a term are searched. One
    ``Q`` object is built per word per field, so an unbounded term lets the
    requester set the depth of the expression tree — deep enough, on SQLite,
    for the database to refuse the query outright.

    Config:
        search_fields (list[str] | None): ORM field paths to search across.
            Supports relationship traversal (e.g. ``"category__name"``).
            Default: ``None`` (mixin is a no-op).
        max_search_words (int): How many words of ``?q=`` are searched.
            Words past the limit are ignored. Default: ``10``.

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
    max_search_words = 10

    def get_search_fields(self):
        """Return the list of fields to search across.

        Returns:
            The ORM field paths to search, or ``None`` to disable search.
        """
        return self.search_fields

    def get_queryset(self):
        """Filter the queryset by the ``?q=`` search term."""
        queryset = super().get_queryset()

        search_term = self.request.GET.get("q", "").strip()
        if search_term and self.get_search_fields():
            queryset = self._apply_search(queryset, search_term)

        return queryset

    def _apply_search(self, queryset: QuerySet, search_term: str):
        """Apply search filtering across search_fields.

        Similar to Django admin's search functionality, this builds an OR query
        across all specified fields using case-insensitive contains lookups.
        For multi-word searches, applies OR matching across all words and fields.

        Only the first ``max_search_words`` words are used. The tree this
        builds is one branch per word per field, and the term arrives from the
        query string, so without a bound its depth belongs to the requester.

        Args:
            queryset: The queryset to filter.
            search_term: The search string (can contain multiple words).

        Returns:
            The filtered, de-duplicated queryset.
        """
        search_query = Q()

        words = search_term.split()[: self.max_search_words]

        for word in words:
            for field in self.get_search_fields():
                search_query |= Q(**{f"{field}__icontains": word})

        return queryset.filter(search_query).distinct()

    def get_context_data(self, **kwargs):
        """Add ``search_query`` and ``is_searchable`` to the context."""
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
    * ``orm_expression`` — the value passed to ``queryset.order_by()``. A
      sequence is unpacked into multiple ``order_by()`` arguments, which is
      how an entry declares a tiebreak. This is a developer-declared
      constant and is **never** exposed in the URL.

    **Security guarantee**: the raw ``?o=`` value is never passed to the ORM.
    Only the ``orm_expression`` of the matching whitelist entry is used.
    Unrecognised ``?o=`` values are silently ignored.

    When ``order_by`` is ``None`` or empty the mixin is a complete no-op.
    Context variables are only injected when ``order_by`` is configured.

    Config:
        order_by (list[tuple[str, str, str | Sequence[str]]] | None): Whitelist
            of permitted ordering options. Each entry is
            ``(public_key, label, orm_expression)``. Default: ``None`` (mixin
            is a no-op).

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
                ("name_asc", "Name (A-Z)", ["name", "pk"]),
                ("name_desc", "Name (Z-A)", ["-name", "-pk"]),
                ("newest", "Newest First", ["-created_at", "-pk"]),
            ]

    A single column is not a total order unless it is unique, so a stable
    default ordering — one that survives pagination without a row appearing
    on two pages or on neither — needs a tiebreak, usually the primary key.
    """

    order_by = None

    def get_order_by_choices(self):
        """Return the list of ordering choices.

        Returns:
            The ``(public_key, label, orm_expression)`` whitelist, or ``None``.
        """
        return self.order_by

    def get_queryset(self):
        """Order the queryset by the whitelisted ``?o=`` choice."""
        queryset = super().get_queryset()

        ordering = self.request.GET.get("o", "")
        if ordering and self.get_order_by_choices():
            queryset = self._apply_ordering(queryset, ordering)

        return queryset

    def _apply_ordering(self, queryset: QuerySet, ordering: str):
        """Apply ordering to the queryset.

        Validates that the ordering value matches a public_key in the configured
        order_by choices before applying the corresponding orm_expression.
        The raw ``?o=`` value is NEVER passed directly to the ORM.

        Args:
            queryset: The queryset to order.
            ordering: The public_key value from the ``?o=`` query parameter.

        Returns:
            The ordered queryset, or ``queryset`` unchanged for an unknown key.
        """
        for choice in self.get_order_by_choices():
            if choice[0] == ordering:
                expression = choice[2]
                if isinstance(expression, (list, tuple)):
                    return queryset.order_by(*expression)
                return queryset.order_by(expression)

        return queryset

    def get_context_data(self, **kwargs):
        """Add ``order_by_choices`` and ``current_ordering`` when ordering is set."""
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
                ("name_asc", "Name (A-Z)", "name"),
                ("name_desc", "Name (Z-A)", "-name"),
            ]


        # With django_filters:
        class ProductFilteredListView(SearchOrderMixin, FilterView):
            model = Product
            filterset_fields = ["category"]
            search_fields = ["name"]
            order_by = [("name_asc", "Name (A-Z)", "name")]
    """

    pass


class FilterContextMixin:
    """Publish the state of an active filterset to the filter control.

    A no-op unless something else in the MRO puts a filterset in the context
    as ``filter`` — which is what ``django_filters.views.FilterView`` does.
    That keeps django-filter an optional dependency: this mixin reads the
    context key and never imports the package.

    It lives here, rather than on the packaged filtered list view, because
    composing ``MVPListViewMixin`` with ``FilterView`` directly is a supported
    and documented way to build a filtered page. A view built that way is a
    filtered list view in every respect the reader can see, so it gets the
    same filter chrome.

    Context (only when a filterset is present):
        applied_filters (dict): Field name to value, for filters actually set.
        applied_filter_count (int): ``len(applied_filters)`` — the button badge.
        clear_filters_url (str): Present only when at least one filter is
            applied. The current URL with the filterset's own fields removed.

    Override hooks:
        get_active_filters(): Return the filters that are actually set.
        get_filter_params(): Return the query parameters one filter reads.
        get_filter_label(): Return the words that name one filter.
        get_filter_display(): Return one filter's value as the reader set it.
        get_clear_filters_url(): Return the URL with every filter removed.
    """

    def get_context_data(self, **kwargs):
        """Add the applied filters and a clear-filters URL when a filterset exists."""
        context = super().get_context_data(**kwargs)
        filterset = context.get("filter", None)
        if filterset is None:
            return context

        active = self.get_active_filters(filterset)
        context["applied_filters"] = active
        context["applied_filter_count"] = len(active)
        if active:
            context["clear_filters_url"] = self.get_clear_filters_url(filterset)
        return context

    def get_active_filters(self, filterset: Any):
        """Return the subset of the filterset's fields that are actually set.

        Empty, null and false-like values are what an untouched filter field
        cleans to, so they are not applied filters and are dropped here.

        Args:
            filterset: The django-filter ``FilterSet`` from the context.

        Returns:
            Field name to cleaned value, for each filter that is set.
        """
        active: dict[str, Any] = {}
        if not hasattr(filterset.form, "cleaned_data"):
            return active

        for name, value in filterset.form.cleaned_data.items():
            if value in (None, "", [], (), False):
                continue
            active[name] = value

        return active

    def get_clear_filters_url(self, filterset: Any):
        """Return the current URL with only the filterset's fields removed.

        Search (``?q=``) and ordering (``?o=``) are a separate concern from
        the filterset and share the same query string, so they're preserved.
        Clearing filters shouldn't also drop an unrelated search. Pagination
        is reset, since the cleared result set may not have as many pages.

        Args:
            filterset: The django-filter ``FilterSet`` from the context.

        Returns:
            The current path, with the remaining query string when there is one.
        """
        querydict = self.request.GET.copy()  # type: ignore[attr-defined]
        for name in filterset.form.fields:
            for param in self.get_filter_params(filterset, name):
                querydict.pop(param, None)
        querydict.pop(getattr(self, "page_kwarg", "page"), None)
        query_string = querydict.urlencode()
        return (
            f"{self.request.path}?{query_string}" if query_string else self.request.path  # type: ignore[attr-defined]
        )

    def get_filter_params(self, filterset: Any, name: str) -> list[str]:
        """Return the query parameters one filter reads its value from.

        Most filters read one parameter, named after the filter. A filter
        drawn with several inputs, such as a range, reads one per input.

        Args:
            filterset: The django-filter ``FilterSet`` from the context.
            name: The filter's name on the filterset.

        Returns:
            The parameter names, in the order the inputs are drawn.
        """
        if not isinstance(filterset.form.fields[name].widget, forms.MultiWidget):
            return [name]
        widget: Any = filterset.form.fields[name].widget
        if hasattr(widget, "suffixed"):
            return [widget.suffixed(name, suffix) for suffix in widget.suffixes]
        return [f"{name}{suffix}" for suffix in widget.widgets_names]

    def get_filter_label(self, filterset: Any, name: str) -> str:
        """Return the words that name one filter to the reader.

        Args:
            filterset: The django-filter ``FilterSet`` from the context.
            name: The filter's name on the filterset.

        Returns:
            The label of the filter's form field.
        """
        return filterset.form[name].label

    def get_filter_display(self, filterset: Any, name: str, value: Any) -> str:
        """Return one applied filter's value in the words the reader chose.

        A choice is shown by its label and a related record by its string
        form, never by the stored key. A range is shown by its bounds.

        Args:
            filterset: The django-filter ``FilterSet`` from the context.
            name: The filter's name on the filterset.
            value: The filter's cleaned value.

        Returns:
            The value as text.
        """
        if isinstance(value, slice):
            if value.start is None:
                return _("up to %(stop)s") % {"stop": formats.localize(value.stop)}
            if value.stop is None:
                return _("%(start)s or more") % {"start": formats.localize(value.start)}
            return _("%(start)s to %(stop)s") % {
                "start": formats.localize(value.start),
                "stop": formats.localize(value.stop),
            }

        if isinstance(value, (list, tuple, QuerySet)):
            return ", ".join(
                self.get_filter_display(filterset, name, item) for item in value
            )

        if isinstance(value, bool):
            return str(_("Yes") if value else _("No"))

        field = filterset.form.fields[name]
        if isinstance(value, Model) or not isinstance(field, forms.ChoiceField):
            return str(formats.localize(value))

        choices: Any = field.choices
        labels = {str(key): label for key, label in flatten_choices(choices)}
        return str(labels.get(str(value), value))


class MVPListViewMixin(
    BaseTemplateNameMixin,
    SearchOrderMixin,
    FilterContextMixin,
    CRUDDirectoryMixin,
    PageMixin,
):
    """Foundation mixin for paginated, searchable, orderable list pages.

    Composes ``BaseTemplateNameMixin``, ``SearchOrderMixin``, ``CRUDDirectoryMixin``, and
    ``PageMixin`` into a single base class. Subclass this directly (instead of ``MVPListView``)
    when you need to compose with another base class (e.g. ``FilterView``).

    The mixin limits CRUD URL injection to the create action only (``directory = ["create"]``).
    Detail, update, and delete URLs belong on object pages, not list pages.

    Config:
        base_template_name (str): Fallback template. Default: ``"list_view.html"``.
        list_item_template (str | None): Explicit path to the partial template for each item.
            When ``None`` (the default), the path is derived from the model's app label and
            model name: ``"<app_label>/<model_name>_list_item.html"``.
        grid (dict): Responsive grid breakpoint dict passed through to context unchanged
            as ``grid_config``. Default: ``{}``.
        empty_state_heading (str | None): Heading shown when the queryset is empty.
            Default: ``_("There's nothing here yet")``.
        empty_state_message (str | None): Body text shown when the queryset is empty and the
            user may create a record. A user who may not sees the heading alone, since the
            message exists to point at the create button. Set to ``None`` to suppress the
            paragraph for everyone. Default: translated library string.
        page_title (str | Promise): Overrides the model-derived page title. When falsy, the
            title falls back to ``model._meta.verbose_name_plural.title()``.
        search_fields (list[str] | None): Inherited from ``SearchMixin``. Default: ``None``.
        order_by (list[tuple] | None): Inherited from ``OrderMixin``. Default: ``None``.
        create_form_class (type[Form] | None): Django form class for inline object creation
            in a modal. When ``None`` (the default), inline create is disabled. When set, the
            mixin injects an unbound form instance into context as ``create_form`` (if the user
            has create permission). Default: ``None``.
        create_modal_title (str | None): Override the modal title for inline create. When
            ``None`` (the default), auto-derives as ``"Add <verbose_name>"`` (e.g. "Add Product").
            Default: ``None``.

    Override hooks:
        get_list_item_template(): Return the item partial path; override for full control.
        get_empty_state_heading(): Return the empty-state heading string (or ``None``).
        get_empty_state_message(): Return the empty-state message string (or ``None``).
        get_grid_config(): Return the grid breakpoint dict passed to context.
        get_page_title(): Return the page title; falls back to verbose_name_plural.title().
        get_breadcrumbs(): Return the breadcrumb list. Default includes Home + page title.
        get_search_fields(): Inherited from ``SearchMixin``.
        get_order_by_choices(): Inherited from ``OrderMixin``.
        get_create_form(): Instantiate and return the create form, or ``None`` if not configured.
            Default implementation returns ``self.create_form_class()`` (unbound). Override to pass
            additional kwargs (e.g. request, user, initial data).
        get_refinements(): Return what is narrowing the list: the search and each applied filter.
        get_url_without(): Return the current URL with the named query parameters removed.

    Context (always injected):
        result_count (int): How many records the list holds across every page, after the
            search and filters are applied.
        refinements (list[dict]): What is narrowing the list, the search first and then each
            applied filter. Each entry has ``kind`` (``"search"`` or ``"filter"``), ``name``,
            ``label``, ``value`` and ``remove_url``, the URL that removes that one entry and
            keeps the rest. Empty when nothing is applied.
        clear_refinements_url (str): Present only when ``refinements`` is not empty. The
            current URL with the search and every filter removed. The ordering is kept.
        list_item_template (str): Resolved partial template path.
        empty_state (dict): ``{"heading": str | None, "message": str | None}``.
        grid_config (dict): Grid breakpoint configuration (may be empty).
        directory (dict): CRUD URLs; only ``create_url`` is injected (when permitted).
        search_query (str): Active ``?q=`` value, or ``""``.
        is_searchable (bool): Whether ``search_fields`` is configured.
        page (dict): PageMixin metadata — ``title``, ``subtitle``, ``icon``, ``class``,
            ``breadcrumbs``.
        create_form (Form): Unbound form instance for inline create modal (only when
            ``create_form_class`` is set and ``show_create_action`` is ``True``).
        create_modal_title (str): Resolved modal title for inline create (only when
            ``create_form`` is also injected).
        applied_filters / applied_filter_count / clear_filters_url: Injected by
            ``FilterContextMixin`` when composed with a filtered view — see there.

    Example::

        from mvp.views.list import MVPListViewMixin
        from django_filters.views import FilterView


        class ProductFilteredListView(MVPListViewMixin, FilterView):
            model = Product
            filterset_class = ProductFilter
            search_fields = ["name", "description"]
            list_item_template = "shop/product_card.html"
    """

    base_template_name = "list_view.html"
    directory = ["create"]
    list_item_template = None
    grid: dict = {}
    empty_state_heading: str | Promise | None = _("There's nothing here yet")
    empty_state_message: str | Promise | None = _(
        "You haven't added any records yet. Click the button below to get started."
    )
    create_form_class = None
    create_modal_title = None

    def get_context_data(self, **kwargs):
        """Add grid, empty-state, item-template and inline-create context."""
        context = super().get_context_data(**kwargs)
        context["grid_config"] = self.get_grid_config()
        context["empty_state"] = {
            "heading": self.get_empty_state_heading(),
            "message": self.get_empty_state_message(),
        }
        context["list_item_template"] = self.get_list_item_template()

        paginator = context.get("paginator")
        context["result_count"] = (
            paginator.count if paginator else len(context["object_list"])
        )

        refinements = self.get_refinements(context)
        context["refinements"] = refinements
        if refinements:
            params = [param for item in refinements for param in item["params"]]
            context["clear_refinements_url"] = self.get_url_without(*params)

        if self.show_action("create") and self.create_form_class:
            context["create_form"] = self.get_create_form()
            title = (
                self.create_modal_title
                or f"Add {self.model._meta.verbose_name.title()}"
            )
            context["create_modal_title"] = title

        return context

    def get_refinements(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        """Return what is narrowing the list, as one entry per search or filter.

        The list page draws each entry as a control that removes it. An entry
        carries ``kind``, ``name``, ``label``, ``value``, ``params`` (the query
        parameters it occupies) and ``remove_url``.

        Args:
            context: The context built so far, read for the search term and
                the applied filters.

        Returns:
            The search first when there is one, then each applied filter.
        """
        refinements: list[dict[str, Any]] = []

        search_query = context.get("search_query", "").strip()
        if search_query and self.get_search_fields():
            refinements.append(
                {
                    "kind": "search",
                    "name": "q",
                    "label": _("Search"),
                    "value": search_query,
                    "params": ["q"],
                }
            )

        filterset = context.get("filter")
        for name, value in context.get("applied_filters", {}).items():
            refinements.append(
                {
                    "kind": "filter",
                    "name": name,
                    "label": self.get_filter_label(filterset, name),
                    "value": self.get_filter_display(filterset, name, value),
                    "params": self.get_filter_params(filterset, name),
                }
            )

        for item in refinements:
            item["remove_url"] = self.get_url_without(*item["params"])
        return refinements

    def get_url_without(self, *params: str) -> str:
        """Return the current URL with the named query parameters removed.

        The page number is removed with them: what is left may not have as
        many pages.

        Args:
            *params: The query parameters to remove.

        Returns:
            The current path, with the remaining query string when there is one.
        """
        request = self.request  # type: ignore[attr-defined]
        querydict = request.GET.copy()
        for param in (*params, getattr(self, "page_kwarg", "page")):
            querydict.pop(param, None)
        query_string = querydict.urlencode()
        return f"{request.path}?{query_string}" if query_string else request.path

    def get_create_form(self):
        """Instantiate and return the create form, or None if not configured.

        Default implementation returns ``self.create_form_class()`` (unbound).
        Override to pass additional kwargs (e.g. request, user, initial data).

        Returns:
            An unbound form instance, or ``None`` when ``create_form_class`` is unset.
        """
        if self.create_form_class is None:
            return None
        return self.create_form_class()

    def get_list_item_template(self):
        """Return the template path for rendering individual list items.

        If ``list_item_template`` is explicitly set, it is used. Otherwise the
        path follows the pattern ``"<app_label>/<model_name>_list_item.html"``.

        Returns:
            Template path for the list item partial.

        Raises:
            AttributeError: If model is not defined on the view.
        """
        if self.list_item_template:
            return self.list_item_template

        if not hasattr(self, "model") or self.model is None:
            msg = (
                f"{self.__class__.__name__} is missing a model. "
                "Define {0}.model or override "
                "{0}.get_list_item_template()."
            ).format(self.__class__.__name__)
            raise AttributeError(msg)

        opts = self.model._meta
        return f"{opts.app_label}/{opts.model_name}_list_item.html"

    def get_empty_state_heading(self) -> str | Promise | None:
        """Return the heading shown when the list is empty.

        Returns:
            ``empty_state_heading``, or ``None`` to show no heading.
        """
        return self.empty_state_heading

    def get_empty_state_message(self) -> str | Promise | None:
        """Return the empty-state body text, or ``None`` to show none.

        The message points the reader at the create button, so it is dropped
        for a user whose create action is hidden: the heading already says
        the page is empty, and there is no button for the message to name.

        Returns:
            ``empty_state_message``, or ``None`` when the create action is hidden.
        """
        if not self.show_action("create"):
            return None
        return self.empty_state_message

    def get_grid_config(self):
        """Return the responsive grid breakpoints passed to the template.

        Returns:
            The ``grid`` breakpoint dict, unchanged.
        """
        return self.grid

    def get_page_title(self):
        """Return the page title, falling back to the model's plural name.

        Returns:
            ``page_title`` when set, else the title-cased ``verbose_name_plural``.
        """
        if self.page_title:
            return self.page_title
        return self.model._meta.verbose_name_plural.title()

    def get_breadcrumbs(self):
        """Return the breadcrumb trail for the list page.

        Returns:
            A Home link followed by the page title.
        """
        return [
            {"text": _("Home"), "href": "/"},
            {"text": self.get_page_title()},
        ]


class MVPListView(MVPListViewMixin, ListView):
    """Concrete list view; subclass with only ``model`` for a fully functional page.

    Extends ``MVPListViewMixin`` with a default ``paginate_by = 24`` (divisible by
    1, 2, 3, and 4 — safe for single, two, three, and four-column grids). Override
    ``paginate_by`` on your subclass to change the page size.

    Config:
        paginate_by (int): Default page size. Default: ``24``.
        (all other config inherited from ``MVPListViewMixin``)

    Override hooks:
        (all hooks inherited from ``MVPListViewMixin``)

    Example::

        from mvp.views.list import MVPListView


        class ProductListView(MVPListView):
            model = Product
            # That's it — paginated, searchable, orderable list page.


        # With search and ordering:
        class ProductListView(MVPListView):
            model = Product
            search_fields = ["name", "description"]
            order_by = [
                ("name_asc", "Name (A-Z)", "name"),
                ("name_desc", "Name (Z-A)", "-name"),
            ]
    """

    paginate_by = 24
