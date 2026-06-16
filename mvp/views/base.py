from functools import cached_property

from django.core.exceptions import ImproperlyConfigured
from django.utils.functional import Promise
from django.utils.translation import gettext_lazy as _
from django.views import generic

from ..config import MVP_LANDING_PAGE_HERO


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
        - ``MVPTableView`` / ``MVPTableListView`` (``mvp.views.table``) — use ``"table_view.html"``

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
        template_names = super().get_template_names()
        template_names.append(self.base_template_name)
        return template_names


class PageMixin:
    """Mixin that injects a ``page`` context dict into every template rendered by the view.

    Groups all page-level rendering metadata (title, subtitle, caption, icon, CSS class, breadcrumbs)
    under a single ``page`` key in the template context. This keeps the main context
    namespace clean and makes it easy to identify where each variable originates.

    In templates, access page data as::

        {{ page.title }}
        {{ page.subtitle }}
        {{ page.caption }}
        {{ page.icon }}
        {{ page.class }}
        {% for crumb in page.breadcrumbs %}...{% endfor %}

    Each attribute has a corresponding ``get_*()`` method. Use the class attribute for
    static values known at class-definition time; override the method for values that
    depend on the request, the resolved object, or other runtime state.

    Attributes:
        page_title (str | Promise): Page heading. Defaults to ``""``.
        page_subtitle (str | Promise): Secondary heading shown below the title. Defaults to ``""``.
        page_class (str): Extra CSS class(es) appended to the page container after the
            mandatory ``"mvp-page"`` prefix. Defaults to ``""``.
        breadcrumbs (list): List of breadcrumb dicts. Each dict has a ``"text"`` key and
            an optional ``"href"`` key. Defaults to ``[]``.

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
    breadcrumbs: list = []

    def get_context_data(self, **kwargs):
        """Add the ``page`` context dict to the template context.

        Calls ``super().get_context_data(**kwargs)`` to collect the existing context, then
        adds a ``"page"`` key whose value is the dict returned by ``get_page_context()``.
        All other context keys from the parent are preserved unchanged.

        Args:
            **kwargs: Arbitrary keyword arguments forwarded to ``super().get_context_data()``.

        Returns:
            dict: The full template context with a ``"page"`` key added containing:
                ``{"title": str, "subtitle": str, "icon": str | None,
                "class": str, "caption": str, "breadcrumbs": list}``.
        """
        context = super().get_context_data(**kwargs)
        context["page"] = self.get_page_context()
        return context

    def get_page_context(self):
        """Return the ``page`` context dict populated by all page-level getter methods.

        All page-related variables are grouped under a single dict key to avoid polluting
        the main template context namespace and to make provenance clear at a glance.

        Returns:
            dict: A dict with the following string keys:
                - ``"title"`` — from ``get_page_title()``
                - ``"subtitle"`` — from ``get_page_subtitle()``
                - ``"class"`` — from ``get_page_class()`` (always starts with ``"mvp-page"``)
                - ``"breadcrumbs"`` — from ``get_breadcrumbs()``
        """
        return {
            "title": self.get_page_title(),
            "subtitle": self.get_page_subtitle(),
            "class": self.get_page_class(),
            "breadcrumbs": self.get_breadcrumbs(),
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
            list: The value of ``self.breadcrumbs``.

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

    def get_page_class(self):
        """Return the CSS class string to apply to the page container element.

        Always prefixes the result with ``"mvp-page"`` regardless of ``page_class``.
        This method is the override hook for dynamic class values. To set a static
        extra class, assign ``page_class`` as a class attribute instead.

        Returns:
            str: Space-separated CSS class string, always starting with ``"mvp-page"``.
            Extra classes from ``page_class`` are appended. Empty or ``None`` values
            in ``page_class`` are silently ignored.

        Example::

            # page_class = "products-list"  →  get_page_class() == "mvp-page products-list"
            # page_class = ""               →  get_page_class() == "mvp-page"
            # page_class = None             →  get_page_class() == "mvp-page"
        """

        return " ".join(filter(None, ["mvp-page", self.page_class]))


class ModelInfoMixin:
    """Mixin to provide model metadata in the template context."""

    @cached_property
    def model_meta(self):
        """Return the meta options of the model class for this view. Subclasses can override this if they need to
        customize how the model class is determined.

        Returns:
            type: The Django model class associated with this view
        """
        return self.get_model_class()._meta

    def get_model_class(self):
        """Resolve the model class for this view across common configuration styles."""

        # 1) Explicit model attribute
        if getattr(self, "model", None) is not None:
            return self.model

        # 2) Queryset/model from SingleObjectMixin/ModelFormMixin path
        try:
            queryset = self.get_queryset()
        except Exception:
            queryset = None
        if queryset is not None and getattr(queryset, "model", None) is not None:
            return queryset.model

        # 3) Model declared on a custom form class (ModelForm)
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

        # 4) Fallback when an object instance is already available
        if getattr(self, "object", None) is not None:
            return self.object.__class__

        raise ImproperlyConfigured(
            f"{self.__class__.__name__} inherits from `ModelInfoMixin` but could not determine a model class. "
            "Set `model`, `queryset`, use a ModelForm `form_class` or override the `get_model_class()` method."
        )

    def get_model_info(self):
        """Return a dict of details about the model for use in templates.

        Returns:
            dict: Details about the model, including:
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
        context = super().get_context_data(**kwargs)
        context["model_info"] = self.get_model_info()
        return context


class MVPTemplateView(PageMixin, generic.TemplateView):
    """TemplateView with support for page configuration features like title and breadcrumbs."""

    pass


class MVPHomeView(MVPTemplateView):
    """Home page view. Shows stats and recent activity for authenticated users. Landing page for unauthenticated users."""

    page_title = _("Home")
    dashboard_template_name = "mvp/dashboard.html"
    landing_template_name = "mvp/landing.html"

    def get_template_names(self):
        """Choose template based on authentication status."""
        if self.landing_template_name is None:
            raise ImproperlyConfigured(f"{self.__class__.__name__} requires `landing_template_name` to be set.")
        if self.request.user.is_authenticated:
            if self.dashboard_template_name is None:
                raise ImproperlyConfigured(
                    f"{self.__class__.__name__} requires `dashboard_template_name` to be set for authenticated users."
                )
            return [self.dashboard_template_name]
        return [self.landing_template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context = self.get_dashboard_context(context)
        else:
            context = self.get_landing_context(context)

        return context

    def get_landing_context(self, context):
        """Context for unauthenticated users."""
        context["hero_content"] = MVP_LANDING_PAGE_HERO
        return context

    def get_dashboard_context(self, context):
        """Context for authenticated users."""
        return context
