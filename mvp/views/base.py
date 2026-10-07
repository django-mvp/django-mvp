"""Cross-cutting mixins for django-mvp views.

This module provides the shared mixin infrastructure that all view types use:
- Template resolution with fallback (BaseTemplateNameMixin)
- Page metadata injection (PageMixin)
- Model info resolution (ModelInfoMixin)

These mixins are imported by all other view modules and composed into concrete
views via multiple inheritance. Developers rarely import from this module directly —
they use the concrete views exported from ``mvp.views``.

Example::

    from mvp.views.base import PageMixin, BaseTemplateNameMixin


    class MyView(PageMixin, BaseTemplateNameMixin, DetailView):
        model = Product
        base_template_name = "my_detail.html"
"""

from enum import StrEnum
from functools import cached_property

from django.core.exceptions import ImproperlyConfigured
from django.utils.functional import Promise


class BaseTemplateNameMixin:
    """Mixin that extends Django's template resolution to support a mandatory fallback base template.

    Most django-mvp view classes need to resolve a view-specific template first (e.g.,
    ``myapp/mymodel_detail.html``) and fall back to a shared base layout template when no
    custom template exists. This mixin implements that two-level resolution by appending
    ``base_template_name`` to the candidate list produced by the parent's
    ``get_template_names()``.

    Subclasses **must** set ``base_template_name`` to a non-``None`` string; failing to do
    so raises ``ImproperlyConfigured`` at render time, mirroring Django's own behaviour in
    ``TemplateResponseMixin``.

    Attributes:
        base_template_name (str | None): The fallback template appended to the candidate
            list. Defaults to ``None``. **Must** be overridden by every concrete subclass.

    Primary subclasses:
        - ``MVPDetailView`` (``mvp.views.detail``) — uses ``"detail_view.html"``
        - ``MVPListViewMixin`` (``mvp.views.list``) — uses ``"list_view.html"``
        - ``MVPFormBase`` (``mvp.views.edit``) — uses ``"form_view.html"``
        - ``MVPDeleteView`` (``mvp.views.edit``) — uses ``"delete_view.html"``
        - ``MVPTableView`` / ``MVPTableViewMixin`` (``mvp.integrations.django_tables.views``) — use ``"table_view.html"``

    Example::

        from django.views.generic import DetailView
        from mvp.views.base import BaseTemplateNameMixin


        class MyDetailView(BaseTemplateNameMixin, DetailView):
            model = MyModel
            base_template_name = "my_detail_base.html"
            # template_name = "myapp/mymodel_detail.html"  # optional; more specific
    """

    base_template_name: str | None = None

    def get_template_names(self):
        """Return the ordered list of template names to search.

        Calls ``super().get_template_names()`` to collect the view-specific candidates
        (e.g., ``myapp/mymodel_detail.html``), then appends ``base_template_name`` as the
        last fallback. Django's template loader tries each name in order and uses the first
        one that exists.

        Returns:
            list[str]: Template names in descending specificity order, with
            ``base_template_name`` appended last.

        Raises:
            ImproperlyConfigured: If ``base_template_name`` is ``None`` (i.e., the
                subclass forgot to set it).

        Example::

            class ConditionalDetailView(BaseTemplateNameMixin, DetailView):
                model = MyModel
                base_template_name = "detail_view.html"

                def get_template_names(self):
                    names = (
                        super().get_template_names()
                    )  # ['myapp/mymodel_detail.html', 'detail_view.html']
                    if self.object.is_featured:
                        names.insert(0, "myapp/featured_detail.html")
                    return names
        """
        if self.base_template_name is None:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} requires a 'base_template_name' attribute to be set."
            )
        try:
            template_names = super().get_template_names()
        except ImproperlyConfigured:
            # Django's own TemplateResponseMixin (unlike the model-based
            # SingleObjectTemplateResponseMixin/MultipleObjectTemplateResponseMixin)
            # raises here rather than returning no candidates when `template_name`
            # is unset — the case a plain, model-less MVPFormView is always in.
            # This mixin already guarantees base_template_name as a fallback, so
            # "no view-specific candidates" is not an error for it.
            template_names = []
        template_names.append(self.base_template_name)
        return template_names


class PageWidth(StrEnum):
    """The widths a page's content can take.

    Set one on a view as ``page_width``, or pass its value to
    ``<c-mvp.container width="...">`` on a page written by hand. Every width is
    centred, and every width fills a screen narrower than itself.

    Example::

        from mvp.views import MVPUpdateView, PageWidth


        class OrderLinesView(MVPUpdateView):
            model = Order
            page_width = PageWidth.MEDIUM
    """

    NARROW = "narrow"
    """A 672px column, for a form with one field to a row. Form pages use it."""

    MEDIUM = "medium"
    """An 896px column, for fields side by side or a row of related records."""

    WIDE = "wide"
    """The standard container, which steps with the screen up to 1536px."""

    FULL = "full"
    """The whole width of the screen, with no limit."""


class PageMixin:
    """Mixin that injects a ``page`` context dict into every template rendered by the view.

    Groups all page-level rendering metadata (title, subtitle, CSS class, breadcrumbs and the
    page's explanatory text) under a single ``page`` key in the template context. This keeps
    the main context namespace clean and makes it easy to identify where each variable
    originates.

    In templates, access page data as::

        {{ page.title }}
        {{ page.subtitle }}
        {{ page.class }}
        {{ page.info }}
        {% for crumb in page.breadcrumbs %}...{% endfor %}
        {% for action in page.info_actions %}...{% endfor %}

    Each attribute has a corresponding ``get_*()`` method. Use the class attribute for
    static values known at class-definition time; override the method for values that
    depend on the request, the resolved object, or other runtime state.

    Attributes:
        page_title (str | Promise): Page heading. Defaults to ``""``.
        page_subtitle (str | Promise): Secondary heading shown below the title. Defaults to ``""``.
        page_class (str): Extra CSS class(es) appended to the page container after the
            mandatory ``"mvp-page"`` prefix. Defaults to ``""``.
        page_width (PageWidth): How wide the page's content is. Defaults to
            ``PageWidth.WIDE``.
        breadcrumbs (list): List of breadcrumb dicts. Each dict has a ``"text"`` key and
            an optional ``"href"`` key. Defaults to ``[]``.
        page_info (str | Promise): Text explaining what the page is for. When set, an info
            icon appears beside the page title and opens a dialog containing this text.
            Defaults to ``""``, which renders no icon.
        page_info_actions (list): Buttons shown at the foot of that dialog. Each dict is
            passed straight to daisy-cotton's ``c-button``, so it accepts any
            attribute that component declares (``text``, ``href``, ``icon``,
            ``variant``, ``ghost``, ``outline``, ``size`` and the rest). Defaults
            to ``[]``.

    Primary consumers:
        - ``MVPTemplateView`` (``mvp.views.base``)
        - ``MVPDetailView`` (``mvp.views.detail``)
        - ``MVPListViewMixin`` (``mvp.views.list``)
        - ``MVPFormBase`` (``mvp.views.edit``)

    Example::

        from mvp.views.base import PageMixin
        from django.views.generic import TemplateView


        class DashboardView(PageMixin, TemplateView):
            template_name = "dashboard.html"
            page_title = "Dashboard"
            page_subtitle = "Welcome back"
            breadcrumbs = [{"text": "Home", "href": "/"}, {"text": "Dashboard"}]
    """

    page_title: str | Promise = ""
    page_subtitle: str | Promise = ""
    page_class = ""
    page_width: PageWidth = PageWidth.WIDE
    breadcrumbs: list = []
    page_info: str | Promise = ""
    page_info_actions: list = []

    def get_context_data(self, **kwargs):
        """Add the ``page`` context dict from ``get_page_context()`` to the context."""
        context = super().get_context_data(**kwargs)
        context["page"] = self.get_page_context()
        return context

    def get_page_context(self):
        """Return the ``page`` context dict populated by all page-level getter methods.

        All page-related variables are grouped under a single dict key to avoid polluting
        the main template context namespace and to make provenance clear at a glance.

        Returns:
            A dict with the following string keys:

                - ``"title"`` — from ``get_page_title()``
                - ``"subtitle"`` — from ``get_page_subtitle()``
                - ``"class"`` — from ``get_page_class()`` (always starts with ``"mvp-page"``)
                - ``"breadcrumbs"`` — from ``get_breadcrumbs()``
                - ``"info"`` — from ``get_page_info()``
                - ``"info_actions"`` — from ``get_page_info_actions()``
                - ``"width"`` — from ``get_page_width()``
        """
        return {
            "title": self.get_page_title(),
            "subtitle": self.get_page_subtitle(),
            "class": self.get_page_class(),
            "breadcrumbs": self.get_breadcrumbs(),
            "info": self.get_page_info(),
            "info_actions": self.get_page_info_actions(),
            "width": self.get_page_width(),
        }

    def get_page_title(self):
        """Return the page title string.

        This method is the override hook for dynamic values. To set a static title,
        assign ``page_title`` as a class attribute instead.

        Returns:
            str | Promise: The value of ``self.page_title``.

        Example::

            # Static title — use the class attribute:
            class ReportView(PageMixin, TemplateView):
                page_title = "Monthly Report"


            # Dynamic title — override this method:
            class ProductDetailView(PageMixin, DetailView):
                def get_page_title(self):
                    return self.object.name
        """
        return self.page_title

    def get_page_subtitle(self):
        """Return the page subtitle string.

        This method is the override hook for dynamic values. To set a static subtitle,
        assign ``page_subtitle`` as a class attribute instead.

        Returns:
            str | Promise: The value of ``self.page_subtitle``.

        Example::

            class ProductDetailView(PageMixin, DetailView):
                def get_page_subtitle(self):
                    return self.object.category.name
        """
        return self.page_subtitle

    def get_breadcrumbs(self):
        """Return the list of breadcrumb items for the page.

        This method is the override hook for dynamic breadcrumbs. To set static breadcrumbs,
        assign ``breadcrumbs`` as a class attribute instead.

        Each breadcrumb item is a dict with a ``"text"`` key (required) and an optional
        ``"href"`` key. Items without ``"href"`` are rendered as the current (non-linked)
        page indicator.

        Returns:
            The value of ``self.breadcrumbs``.

        Example::

            # Static breadcrumbs — use the class attribute:
            class AboutView(PageMixin, TemplateView):
                breadcrumbs = [{"text": "Home", "href": "/"}, {"text": "About"}]


            # Dynamic breadcrumbs — override this method:
            class ProductDetailView(PageMixin, DetailView):
                def get_breadcrumbs(self):
                    return [
                        {"text": "Home", "href": "/"},
                        {"text": "Products", "href": "/products/"},
                        {"text": self.object.name},
                    ]
        """
        return self.breadcrumbs

    def get_page_info(self):
        """Return the text explaining what this page is for.

        An empty return value means the page offers no explanation, and no info icon is
        drawn beside the title. To set static text, assign ``page_info`` as a class
        attribute instead.

        The return value goes through Django's template layer like any other context
        value: a plain string is escaped, and a string marked safe is written out as
        markup. That is the hook for text built at request time — a rendered template, a
        Markdown source, a value read from the database.

        Returns:
            str | Promise: The value of ``self.page_info``.

        Example::

            # Static text — use the class attribute:
            class ProductListView(MVPListView):
                page_info = _("Every product currently on sale.")


            # Built at request time — override this method:
            class ProductListView(MVPListView):
                def get_page_info(self):
                    return render_to_string("products/help.html", request=self.request)
        """
        return self.page_info

    def get_page_info_actions(self):
        """Return the buttons shown at the foot of the page-info dialog.

        Each item is a dict passed straight to daisy-cotton's ``c-button``, so it
        takes any attribute that component takes — ``text``, ``href``, ``icon``,
        ``variant``, ``ghost``, ``outline`` and the rest. Any other key lands on the
        element as an HTML attribute. This is how a page points at fuller
        documentation instead of restating it in the dialog.

        This method is the override hook for dynamic values. To set static actions, assign
        ``page_info_actions`` as a class attribute instead.

        Returns:
            The value of ``self.page_info_actions``.

        Example::

            class ProductListView(MVPListView):
                page_info = _("Every product currently on sale.")
                page_info_actions = [
                    {
                        "text": _("Read the guide"),
                        "href": "https://example.com/guide/",
                        "icon": "external-link",
                        "target": "_blank",
                    }
                ]
        """
        return self.page_info_actions

    def get_page_class(self):
        """Return the CSS class string to apply to the page container element.

        Always prefixes the result with ``"mvp-page"`` regardless of ``page_class``.
        This method is the override hook for dynamic class values. To set a static
        extra class, assign ``page_class`` as a class attribute instead.

        Returns:
            Space-separated CSS class string, always starting with ``"mvp-page"``.
            Extra classes from ``page_class`` are appended. Empty or ``None``
            values in ``page_class`` are silently ignored.

        Example::

            # page_class = "products-list"  →  get_page_class() == "mvp-page products-list"
            # page_class = ""               →  get_page_class() == "mvp-page"
            # page_class = None             →  get_page_class() == "mvp-page"
        """
        return " ".join(filter(None, ["mvp-page", self.page_class]))

    def get_page_width(self):
        """Return the width of the page's content.

        This method is the override hook for a width that depends on the request
        or the object. To set a fixed width, assign ``page_width`` as a class
        attribute instead.

        Returns:
            PageWidth: The value of ``self.page_width``.

        Raises:
            ValueError: If ``page_width`` is not one of the ``PageWidth`` values.

        Example::

            class OrderUpdateView(MVPUpdateView):
                def get_page_width(self):
                    if self.object.lines.exists():
                        return PageWidth.MEDIUM
                    return super().get_page_width()
        """
        return PageWidth(self.page_width)


class ModelInfoMixin:
    """Mixin to provide model metadata in the template context."""

    @cached_property
    def model_meta(self):
        """Return the meta options of the model class for this view.

        Returns:
            The Django model's ``_meta`` options object.
        """
        return self.get_model_class()._meta

    def get_model_class(self):
        """Resolve the model class for this view across common configuration styles.

        Tries, in order: an explicit ``model`` attribute, the queryset or
        model from a ``SingleObjectMixin``/``ModelFormMixin`` path, the
        model declared on a custom ``ModelForm`` class, then an
        already-loaded ``self.object``.

        Returns:
            The resolved model class.

        Raises:
            ImproperlyConfigured: No model class could be determined by any
                of the above.
        """
        if getattr(self, "model", None) is not None:
            return self.model

        try:
            queryset = self.get_queryset()
        except Exception:
            queryset = None
        if queryset is not None and getattr(queryset, "model", None) is not None:
            return queryset.model

        form_class = getattr(self, "form_class", None)
        if form_class is None:
            try:
                form_class = self.get_form_class()
            except Exception:
                form_class = None
        if form_class is not None:
            model = getattr(getattr(form_class, "_meta", None), "model", None)
            if model is not None:
                return model

        if getattr(self, "object", None) is not None:
            return self.object.__class__

        raise ImproperlyConfigured(
            f"{self.__class__.__name__} inherits from `ModelInfoMixin` but could not determine a model class. "
            "Set `model`, `queryset`, use a ModelForm `form_class` or override the `get_model_class()` method."
        )

    def get_model_class_or_none(self):
        """Like ``get_model_class()``, but returns ``None`` instead of raising.

        For page chrome that has a sensible model-less fallback — a plain
        ``MVPFormView`` carries no model by design (see its own docstring),
        but still shares ``PageObjectMixin`` with the model-based views.
        """
        try:
            return self.get_model_class()
        except ImproperlyConfigured:
            return None

    def get_model_info(self):
        """Return a dict of details about the model for use in templates.

        Returns:
            Details about the model:

                - verbose_name: The human-readable name of the model
                - verbose_name_plural: The plural form of the human-readable name
                - app_label: The Django app label for the model
                - model_name: The lowercase name of the model
        """
        return {
            "verbose_name": self.model_meta.verbose_name,
            "verbose_name_plural": self.model_meta.verbose_name_plural,
            "app_label": self.model_meta.app_label,
            "model_name": self.model_meta.model_name,
        }

    def get_context_data(self, **kwargs):
        """Add ``model_info`` to the context, or ``None`` when no model resolves."""
        context = super().get_context_data(**kwargs)
        model = self.get_model_class_or_none()
        context["model_info"] = self.get_model_info() if model is not None else None
        return context
