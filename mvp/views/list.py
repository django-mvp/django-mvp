"""List views, which take their search, sort and filters from one filterset."""

import sys
from numbers import Number
from typing import Any

from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model, QuerySet
from django.utils import formats
from django.utils.cache import patch_vary_headers
from django.utils.choices import flatten_choices
from django.utils.functional import Promise
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView
from django_filters import (
    BooleanFilter,
    CharFilter,
    ChoiceFilter,
    ModelChoiceFilter,
    ModelMultipleChoiceFilter,
    MultipleChoiceFilter,
)
from django_filters.filterset import filterset_factory
from django_filters.views import FilterMixin

from ..filters import SearchFilter, SortFilter
from .base import BaseTemplateNameMixin, PageMixin
from .detail import CRUDDirectoryMixin


class FilterContextMixin:
    """Publish the state of the list's filterset to the page.

    The one place filter state is computed. A no-op unless the context holds
    a filterset as ``filter``, which ``MVPListViewMixin`` puts there.

    A ``SortFilter`` orders the list and never narrows it, so it is never an
    applied filter and neither clear action removes it. A ``SearchFilter`` is
    an applied filter like any other, labelled by its own label.

    Context (only when a filterset is present):
        applied_filters (dict): Field name to value, for filters actually set.
        applied_filter_count (int): ``len(applied_filters)``.
        clear_filters_url (str): Present only when at least one filter is
            applied. The current URL with the filterset's own fields removed,
            except the sort.
        sort_label (str): The label of the chosen sort option, or ``""``.
        toolbar_fields (list[dict]): The fields ``toolbar_filters`` names, in
            that order and each once, as ``get_toolbar_field()`` describes
            them. The sort is never among them.
        toolbar_sort (dict | None): The sort, when ``toolbar_filters`` names
            it, described the same way. The page draws it at the end of the row.
        panel_fields (list[BoundField]): Every field the toolbar does not draw,
            for the filter panel. Each widget carries ``form="filterForm"``, so
            the field joins the toolbar's form from outside it.
        panel_applied_count (int): How many of the panel's fields are applied
            filters — the panel button's badge.
        clear_panel_url (str): Present only when a panel field is applied. The
            current URL with the panel's fields and the page number removed;
            the toolbar's fields and the sort, wherever it is drawn, are kept.

    Override hooks:
        get_active_filters(): Return the filters that are actually set.
        get_filter_params(): Return the query parameters one filter reads.
        get_filter_label(): Return the words that name one filter.
        get_filter_display(): Return one filter's value as the reader set it.
        get_clear_filters_url(): Return the URL with every filter removed.
        get_sort_label(): Return the label of the chosen sort option.
        get_toolbar_field(): Describe one field the way the toolbar draws it.
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
        context["sort_label"] = self.get_sort_label(filterset)

        toolbar_names = self.get_toolbar_names(filterset)
        fields = [self.get_toolbar_field(filterset, name) for name in toolbar_names]
        context["toolbar_fields"] = [f for f in fields if f["kind"] != "sort"]
        context["toolbar_sort"] = next((f for f in fields if f["kind"] == "sort"), None)
        panel_names = [n for n in filterset.form.fields if n not in toolbar_names]
        for name in panel_names:
            filterset.form.fields[name].widget.attrs["form"] = "filterForm"
        context["panel_fields"] = [filterset.form[n] for n in panel_names]
        panel_active = [n for n in active if n in panel_names]
        context["panel_applied_count"] = len(panel_active)
        if panel_active:
            params = [
                p
                for n in panel_names
                if not isinstance(filterset.filters.get(n), SortFilter)
                for p in self.get_filter_params(filterset, n)
            ]
            context["clear_panel_url"] = self.get_url_without(*params)  # type: ignore[attr-defined]
        return context

    def get_toolbar_names(self, filterset: Any) -> list[str]:
        """Return the names of the fields the toolbar draws, each once.

        A name a table view dropped from its filterset is skipped.

        Args:
            filterset: The django-filter ``FilterSet`` from the context.

        Returns:
            The names in ``toolbar_filters``, in that order, duplicates dropped.

        Raises:
            ImproperlyConfigured: A name is not a field of the filterset.
        """
        dropped = getattr(self, "dropped_filters", ())
        names = [
            name
            for name in dict.fromkeys(getattr(self, "toolbar_filters", ()))
            if name not in dropped
        ]
        for name in names:
            if name not in filterset.form.fields:
                raise ImproperlyConfigured(
                    f"{self.__class__.__name__}.toolbar_filters names {name!r}, "
                    f"which {filterset.__class__.__name__} has no field for."
                )
        return names

    def get_toolbar_field(self, filterset: Any, name: str) -> dict[str, Any]:
        """Describe one filterset field the way the toolbar draws it.

        Override to draw a filter class the toolbar does not cover: return a
        dict with a ``kind`` of your own and draw it in your template.

        A filter whose widget is not its field's default is drawn by that
        widget, as it is. It gains the daisyUI class of its control, and an
        ``aria-label`` of the filter's label, unless it has its own.

        Args:
            filterset: The django-filter ``FilterSet`` from the context.
            name: The field's name on the filterset.

        Returns:
            ``name``, ``label`` and ``kind``, one of ``widget`` (with
            ``bound``), ``search`` or ``text`` (with ``value``), ``sort`` or
            ``choice`` (with ``value`` and ``choices``), ``multichoice`` (with
            ``choices``) or ``toggle`` (with ``checked``). Each choice is
            ``(key, label, selected)``, without the empty choice.

        Raises:
            ImproperlyConfigured: The toolbar cannot draw the filter.
        """
        flt = filterset.filters[name]
        bound = filterset.form[name]
        item: dict[str, Any] = {"name": name, "label": str(bound.label)}
        widget = bound.field.widget
        value = bound.value()

        if type(widget) is not type(bound.field).widget and not isinstance(
            flt, SortFilter
        ):
            control = "select" if isinstance(widget, forms.Select) else "input"
            widget.attrs.setdefault("class", f"{control} w-full")
            widget.attrs.setdefault("aria-label", item["label"])
            item.update(kind="widget", bound=bound)
        elif isinstance(flt, SearchFilter):
            item.update(kind="search", value=value or "")
        elif isinstance(flt, CharFilter):
            item.update(kind="text", value=value or "")
        elif isinstance(flt, BooleanFilter):
            item.update(kind="toggle", checked=value is True)
        elif isinstance(flt, (MultipleChoiceFilter, ModelMultipleChoiceFilter)):
            chosen = [str(v) for v in value or []]
            item.update(kind="multichoice", choices=self._choices(bound, chosen))
        elif isinstance(flt, (ChoiceFilter, ModelChoiceFilter)):
            current = "" if value is None else str(value)
            item.update(
                kind="sort" if isinstance(flt, SortFilter) else "choice",
                value=current,
                choices=self._choices(bound, [current]),
            )
        else:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__}.toolbar_filters names {name!r}, a "
                f"{flt.__class__.__name__} the toolbar cannot draw. Leave it in "
                "the filter panel."
            )
        return item

    @staticmethod
    def _choices(bound: Any, chosen: list[str]) -> list[tuple[str, str, bool]]:
        """Return a choice field's choices as the toolbar lists them.

        Args:
            bound: The field's bound field.
            chosen: The keys the request chose.

        Returns:
            ``(key, label, selected)`` for each choice but the empty one.
        """
        out: list[tuple[str, str, bool]] = []
        pairs: Any = flatten_choices(bound.field.choices)
        for raw_key, label in pairs:
            key = "" if raw_key is None else str(getattr(raw_key, "value", raw_key))
            if key:
                out.append((key, str(label), key in chosen))
        return out

    def get_active_filters(self, filterset: Any):
        """Return the subset of the filterset's fields that are actually set.

        ``None`` and empty values (an empty string, list or queryset) are what
        an untouched filter field cleans to, so they are not applied filters
        and are dropped here. A number is always kept: ``0`` is a real choice.
        So is the ``False`` of a ``BooleanFilter`` the request named: only a
        chosen "No" gives one. Any other ``False`` is dropped.

        Args:
            filterset: The django-filter ``FilterSet`` from the context.

        Returns:
            Field name to cleaned value, for each filter that is set.
        """
        active: dict[str, Any] = {}
        if not hasattr(filterset.form, "cleaned_data"):
            return active

        for name, value in filterset.form.cleaned_data.items():
            if isinstance(filterset.filters.get(name), SortFilter):
                continue
            if value is None:
                continue
            if value is False and not self._is_chosen_no(filterset, name):
                continue
            if not isinstance(value, Number) and not value:
                continue
            active[name] = value

        return active

    def _is_chosen_no(self, filterset: Any, name: str) -> bool:
        """Return whether a ``False`` came from a "No" the request chose.

        A checkbox cleans to ``False`` when it is absent, so only a
        ``BooleanFilter`` whose parameter is in the request counts.

        Args:
            filterset: The django-filter ``FilterSet`` from the context.
            name: The filter's name on the filterset.

        Returns:
            ``True`` for a ``BooleanFilter`` the request carries a value for.
        """
        if not isinstance(filterset.filters.get(name), BooleanFilter):
            return False
        data = filterset.data or {}
        return any(param in data for param in self.get_filter_params(filterset, name))

    def get_clear_filters_url(self, filterset: Any):
        """Return the current URL with the filterset's fields removed, but not the sort.

        The sort orders the list rather than narrowing it, so clearing the
        filters keeps it. Pagination is reset, since the cleared result set may
        not have as many pages.

        Args:
            filterset: The django-filter ``FilterSet`` from the context.

        Returns:
            The current path, with the remaining query string when there is one.
        """
        params = [
            param
            for name in filterset.form.fields
            if not isinstance(filterset.filters.get(name), SortFilter)
            for param in self.get_filter_params(filterset, name)
        ]
        return self.get_url_without(*params)  # type: ignore[attr-defined]

    def get_sort_label(self, filterset: Any) -> str:
        """Return the label of the sort option the request chose.

        Args:
            filterset: The django-filter ``FilterSet`` from the context.

        Returns:
            The chosen option's label, or ``""`` when the filterset has no
            sort, or none was chosen, or the address named an unknown one.
        """
        cleaned = getattr(filterset.form, "cleaned_data", {})
        for name, flt in filterset.filters.items():
            if isinstance(flt, SortFilter) and cleaned.get(name):
                labels = {key: label for key, label, _columns in flt.options}
                return str(labels.get(cleaned[name], ""))
        return ""

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
        pairs: Any = flatten_choices(choices)
        labels = {str(key): label for key, label in pairs}
        return str(labels.get(str(value), value))


# Settings list views used to read, with the filter on a filterset that replaces each.
REMOVED_SETTINGS = {
    "search_fields": "SearchFilter",
    "max_search_words": "SearchFilter",
    "get_search_fields": "SearchFilter",
    "order_by": "SortFilter",
    "get_order_by_choices": "SortFilter",
}


class MVPListViewMixin(
    BaseTemplateNameMixin,
    FilterContextMixin,
    CRUDDirectoryMixin,
    PageMixin,
):
    """Foundation mixin for paginated list pages that take their search, sort and filters from a filterset.

    Composes ``BaseTemplateNameMixin``, ``FilterContextMixin``, ``CRUDDirectoryMixin``, and
    ``PageMixin`` into a single base class. Subclass this directly (instead of ``MVPListView``)
    when you need to compose with another base class, such as a table view's. The mixin builds
    its own filterset, so it refuses django-filter's ``FilterView``, and it refuses the removed
    ``search_fields``, ``max_search_words``, ``order_by``, ``get_search_fields`` and
    ``get_order_by_choices`` when the class is defined.

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
        filterset_class (type[FilterSet] | None): The filterset every search, sort and filter
            comes from. Declare the search with ``mvp.filters.SearchFilter`` and the sort with
            ``mvp.filters.SortFilter``. Default: ``None``.
        filterset_fields (list[str] | None): Model field names django-filter generates a
            filterset from when ``filterset_class`` is unset. Default: ``None``.
        toolbar_filters (list[str]): The filterset fields drawn in the toolbar, in this order;
            the sort among them is drawn at the end of the row. Every other field is drawn
            in the filter panel. Default: ``[]``.
        create_form_class (type[Form] | None): Django form class for inline object creation
            in a modal. When ``None`` (the default), inline create is disabled. When set, the
            mixin injects an unbound form instance into context as ``create_form`` (if the user
            has create permission). Default: ``None``.
        create_modal_title (str | None): Override the modal title for inline create. When
            ``None`` (the default), auto-derives as ``"Add <verbose_name>"`` (e.g. "Add Product").
            Default: ``None``.
        list_region_id (str): The id of the region a filter, a chip, a column heading or the
            pager swaps in place with htmx. Default: ``"mvp-list"``.
        filter_panel_attrs (dict): The attributes of the filter panel's ``<c-mvp.page.side>``
            (``position``, ``align``, ``width``, ``breakpoint``, ``collapse``). A subclass's
            dict replaces the default whole. Default: ``{"position": "end"}``. The
            panel aligns with the content at the end and with the title at the start, unless
            ``align`` is set.
        filter_panel_id (str): The id of the filter panel's root element, which the toolbar's
            button opens and every list update refreshes. Default: ``"filters"``.
        partial_base_template (str): What the page extends in place of ``base.html`` when
            htmx asks for the region alone. Default: ``"mvp/partial.html"``.

    Override hooks:
        get_list_item_template(): Return the item partial path; override for full control.
        get_empty_state_heading(): Return the empty-state heading string (or ``None``).
        get_empty_state_message(): Return the empty-state message string (or ``None``).
        get_grid_config(): Return the grid breakpoint dict passed to context.
        get_page_title(): Return the page title; falls back to verbose_name_plural.title().
        get_breadcrumbs(): Return the breadcrumb list. Default includes Home + page title.
        get_filterset_class(): Return the filterset class, declared or generated.
        get_filterset(): Return this request's filterset, built once.
        get_create_form(): Instantiate and return the create form, or ``None`` if not configured.
            Default implementation returns ``self.create_form_class()`` (unbound). Override to pass
            additional kwargs (e.g. request, user, initial data).
        get_result_count(): Return how many records the list holds across every page.
        get_refinements(): Return what is narrowing the list: each applied filter, the search
            among them.
        get_url_without(): Return the current URL with the named query parameters removed.
        is_region_request(): Return whether htmx asked for the list region alone.

    Context (always injected):
        result_count (int): How many records the list holds across every page, after the
            search and filters are applied.
        refinements (list[dict]): What is narrowing the list: each applied filter of the
            filterset, a search among them, in the filterset's order. The sort is never one.
            Each entry has ``kind`` (``"filter"``), ``name``, ``label``, ``value`` and
            ``remove_url``, the URL that removes that one entry and keeps the rest. Empty
            when nothing is applied.
        clear_refinements_url (str): Present only when ``refinements`` is not empty. The
            current URL with the search and every filter removed. The sort is kept.
        list_item_template (str): Resolved partial template path.
        empty_state (dict): ``{"heading": str | None, "message": str | None}``.
        grid_config (dict): Grid breakpoint configuration (may be empty).
        directory (dict): CRUD URLs; only ``create_url`` is injected (when permitted).
        page (dict): PageMixin metadata — ``title``, ``subtitle``, ``icon``, ``class``,
            ``breadcrumbs``.
        create_form (Form): Unbound form instance for inline create modal (only when
            ``create_form_class`` is set and ``show_create_action`` is ``True``).
        create_modal_title (str): Resolved modal title for inline create (only when
            ``create_form`` is also injected).
        filter / filterset (FilterSet): The request's filterset, under both names, only when
            the view has one.
        list_region_id (str): The id of the region swapped in place.
        filter_panel_attrs / filter_panel_id: The filter panel's attributes and root id.
        page_base_template (str): ``partial_base_template``, only when the request asked for
            the region alone.
        applied_filters / applied_filter_count / clear_filters_url / sort_label: Injected by
            ``FilterContextMixin`` when the view has a filterset — see there.

    Example::

        from django.views.generic import ListView
        from mvp.views.list import MVPListViewMixin


        class ProductListView(MVPListViewMixin, ListView):
            model = Product
            filterset_class = ProductFilter
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
    filterset_class = None
    filterset_fields = None
    toolbar_filters: list[str] = []
    list_region_id = "mvp-list"
    filter_panel_attrs: dict = {"position": "end"}
    filter_panel_id = "filters"
    partial_base_template = "mvp/partial.html"

    def __init_subclass__(cls, **kwargs):
        """Refuse a removed search or sort setting, or ``FilterView``, as the class is defined.

        Checking here rather than on a request means Django raises while
        importing the module that declares the view, naming what to move.

        Raises:
            ImproperlyConfigured: The class declares a removed setting, or also
                inherits django-filter's ``FilterMixin``.
        """
        super().__init_subclass__(**kwargs)
        for name, replacement in REMOVED_SETTINGS.items():
            if name.startswith("get_"):
                found = hasattr(cls, name)
            else:
                found = bool(getattr(cls, name, None))
            if found:
                raise ImproperlyConfigured(
                    cls._removed_setting_message(name, replacement)
                )
        if issubclass(cls, FilterMixin):
            raise ImproperlyConfigured(
                f"{cls.__name__} composes django-filter's FilterView, but a list "
                "view builds its own filterset. Drop FilterView and set "
                "filterset_class (or filterset_fields) on the view."
            )

    @classmethod
    def _removed_setting_message(cls, name: str, replacement: str) -> str:
        """Return the refusal for one removed setting, naming what replaces it.

        Args:
            name: The removed setting the class declares.
            replacement: The filter that replaces it on a filterset.

        Returns:
            The message. A table view's ``order_by`` points to the table class,
            since a table view drops a ``SortFilter``.
        """
        # django_tables2 is optional: a class can only be a table view once it is imported.
        tables = sys.modules.get("django_tables2.views")
        if name == "order_by" and tables and issubclass(cls, tables.SingleTableMixin):
            return (
                f"{cls.__name__} declares 'order_by', which table views no longer "
                "read. Ordering belongs on the table class, via its own 'order_by' "
                "or Meta.order_by."
            )
        return (
            f"{cls.__name__} declares {name!r}, which list views no longer read. "
            f"Declare a {replacement} from mvp.filters on the view's filterset and "
            "set filterset_class."
        )

    def get_filterset_class(self):
        """Return the filterset class the list takes its search, sort and filters from.

        Returns:
            ``filterset_class`` when set, else a filterset django-filter
            generates from ``filterset_fields``, else ``None``.
        """
        if self.filterset_class is not None:
            return self.filterset_class
        if self.filterset_fields:
            return filterset_factory(self.model, fields=self.filterset_fields)
        return None

    def get_filterset(self, filterset_class=None):
        """Return this request's filterset, built on the first call.

        The filterset narrows the view's own queryset, the one the list would
        show unfiltered, so a value the request carries for one filter that the
        filter cannot accept is dropped for that filter alone.

        Args:
            filterset_class: The class to build. Defaults to
                ``get_filterset_class()``; the signature matches
                django-filter's ``FilterMixin.get_filterset``.

        Returns:
            The bound filterset, or ``None`` when the view has none.
        """
        if not hasattr(self, "_filterset"):
            filterset_class = filterset_class or self.get_filterset_class()
            self._filterset = None
            if filterset_class is not None:
                self._filterset = filterset_class(
                    data=self.request.GET or None,
                    queryset=self.get_queryset(),  # type: ignore[attr-defined]
                    request=self.request,
                )
        return self._filterset

    def get(self, request, *args, **kwargs):
        """List the records the filterset leaves, or every record without one."""
        filterset = self.get_filterset()
        if filterset is None:
            return super().get(request, *args, **kwargs)  # type: ignore[misc]
        self.object_list = filterset.qs
        return self.render_to_response(self.get_context_data())  # type: ignore[attr-defined]

    def get_context_data(self, **kwargs):
        """Add the filterset, grid, empty-state, item-template and inline-create context."""
        filterset = self.get_filterset()
        if filterset is not None:
            kwargs.setdefault("filter", filterset)
            kwargs.setdefault("filterset", filterset)
        context = super().get_context_data(**kwargs)
        context["grid_config"] = self.get_grid_config()
        context["empty_state"] = {
            "heading": self.get_empty_state_heading(),
            "message": self.get_empty_state_message(),
        }
        context["list_item_template"] = self.get_list_item_template()

        context["result_count"] = self.get_result_count(context)

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

        context["list_region_id"] = self.list_region_id
        context["filter_panel_attrs"] = self.filter_panel_attrs
        context["filter_panel_id"] = self.filter_panel_id
        if self.is_region_request():
            context["page_base_template"] = self.partial_base_template

        return context

    def is_region_request(self) -> bool:
        """Return whether htmx asked for the list region alone.

        Read from the header htmx sends rather than ``request.htmx``, so the
        list page needs no middleware. A boosted link elsewhere, such as the
        sidebar's, targets the whole body and gets the whole page.

        Returns:
            ``True`` when the request's ``HX-Target`` is the list region.
        """
        return self.request.headers.get("HX-Target") == self.list_region_id  # type: ignore[attr-defined]

    def render_to_response(self, context, **response_kwargs):
        """Render the page, varying on ``HX-Target`` so a cache keeps both forms apart."""
        response = super().render_to_response(context, **response_kwargs)  # type: ignore[misc]
        patch_vary_headers(response, ["HX-Target"])
        return response

    def get_result_count(self, context: dict[str, Any]) -> int:
        """Return how many records the list holds across every page.

        Args:
            context: The context built so far, read for the paginator and
                the list itself.

        Returns:
            The paginator's count, or the length of an unpaginated list.
        """
        paginator = context.get("paginator")
        return paginator.count if paginator else len(context["object_list"])

    def get_refinements(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        """Return what is narrowing the list, as one entry per applied filter.

        The list page draws each entry as a control that removes it. An entry
        carries ``kind``, ``name``, ``label``, ``value``, ``params`` (the query
        parameters it occupies) and ``remove_url``.

        Args:
            context: The context built so far, read for the applied filters.

        Returns:
            One entry per applied filter, a search among them; never the sort.
        """
        refinements: list[dict[str, Any]] = []

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
            # That's it — a paginated list page.


        # With a search, a sort and filters, all from one filterset:
        class ProductFilter(django_filters.FilterSet):
            q = SearchFilter(fields=["name", "description"])
            o = SortFilter(
                options=[
                    ("name", "Name (A-Z)", ["name", "pk"]),
                    ("-name", "Name (Z-A)", ["-name", "-pk"]),
                ]
            )

            class Meta:
                model = Product
                fields = ["status"]


        class ProductListView(MVPListView):
            model = Product
            filterset_class = ProductFilter
    """

    paginate_by = 24
