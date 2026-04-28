from functools import cached_property
from typing import Any

from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from django.utils.functional import Promise
from django.utils.http import url_has_allowed_host_and_scheme

from ..config import MVP_DEFAULT_VIEW_NAMES

_OBJECT_ACTIONS = frozenset({"detail", "update", "delete"})


class BaseTemplateNameMixin:
    base_template_name = ""

    def get_template_names(self):
        """Determine the template to use for rendering the form.

        Returns:
            list[str]: List of template names to search, with the most specific first
        """
        template_names = super().get_template_names()
        template_names.append(self.base_template_name)
        return template_names


class PageMixin:
    """Combined mixin for adding both page modifiers and breadcrumbs to the template context."""

    page_title: str | Promise = ""
    page_subtitle: str | Promise = ""
    page_icon: str | None = None
    page_class = ""
    # breadcrumbs = []

    def get_context_data(self, **kwargs):
        """Inject form renderer and page title into template context.

        Returns:
            dict: Context with form_renderer and page_title added
        """
        context = super().get_context_data(**kwargs)
        context["page"] = self.get_page_context()
        return context

    def get_page_context(self):
        """Return a dict of context variables related to page rendering.

        Note: We group these together in a single 'page' dict to avoid cluttering the main context namespace and make it
        easier to discern which context variable come from where.

        """
        return {
            "title": self.get_page_title(),
            "subtitle": self.get_page_subtitle(),
            "icon": self.get_page_icon(),
            "class": self.get_page_class(),
            "breadcrumbs": self.get_breadcrumbs(),
        }

    def get_page_title(self):
        """Return the page title for the form.

        Returns:
            str: Page title from page_title attribute
        """
        return self.page_title

    def get_page_subtitle(self):
        """Return the page subtitle for the form.

        Returns:
            str: Page subtitle from page_subtitle attribute
        """
        return self.page_subtitle

    def get_page_icon(self) -> str | None:
        """Return the icon name for the page.

        Returns:
            str or None: Icon name from icon attribute
        """
        return self.page_icon

    def get_breadcrumbs(self):
        """Return the list of breadcrumb items.

        Returns:
            list[dict]: List of breadcrumb items with 'text' and optional 'href'
        """
        return []

    def get_page_class(self):
        """Return the CSS class to apply to the page container.

        Returns:
            str: CSS class name(s) for the page container
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


class CRUDDirectoryMixin(ModelInfoMixin):
    """Mixin to provide URLs for related CRUD views in the template context.

    This mixin assumes a standard set of CRUD view names based on the model name and action (list, detail, create, update, delete).
    The view names can be customized via the `crud_views` attribute, which should be a dict mapping action keys to URL name patterns. The URL name patterns can include `{model_name}` and `{app_name}` placeholders that will be filled in based on the model metadata.
    """

    crud_views = MVP_DEFAULT_VIEW_NAMES
    directory = []
    _OBJECT_ACTIONS = _OBJECT_ACTIONS

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["directory"] = self.get_directory()
        return context

    def _get_view_name(self, action):
        """Helper method to get the URL name for a given CRUD action.

        Args:
            action (str): One of 'list', 'detail', 'create', 'update'
        """
        if action not in self.crud_views:
            raise ValueError(f"Invalid action '{action}'. Must be one of: {', '.join(self.crud_views.keys())}")
        return self.crud_views[action].format(model_name=self.model_meta.model_name, app_name=self.model_meta.app_label)

    def get_lookup_kwargs(self) -> dict:
        """Return URL kwargs for reversing object-level URLs.

        Returns a copy of all URL kwargs captured by the dispatcher (``self.kwargs``),
        which is empty on views without an object in the URL (list, create).

        For nested URLs (e.g. ``/projects/<project_pk>/tasks/<pk>/``), override this
        method to remove parent resource kwargs that sibling URLs don't expect::

            def get_lookup_kwargs(self):
                return {"pk": self.kwargs["pk"]}
        """
        return dict(self.kwargs)

    def _resolve_directory_url(self, action: str) -> str | None:
        """Resolve the URL for a single CRUD action.

        Returns ``None`` for object-level actions (detail, update, delete) when
        no lookup kwargs are available (e.g. on list or create views).
        """
        print("ARE WE EVEN GETTING HERE?", action)
        lookup_kwargs = self.get_lookup_kwargs()
        if action in self._OBJECT_ACTIONS and not lookup_kwargs:
            return None

        url_name = self._get_view_name(action)

        # Optional permission gating: has_<action>_permission = True/False or callable(user) -> bool
        perm = getattr(self, f"has_{action}_permission", None)
        print(perm)
        if perm is not None:
            allowed = perm(self.request.user) if callable(perm) else perm
            if not allowed:
                return None

        return reverse(url_name, kwargs=lookup_kwargs)

    def get_directory(self) -> dict[str, str]:
        """Return a dict mapping ``{action}_url`` keys to resolved URLs.

        Only actions listed in ``self.directory`` are included. Entries whose
        resolved URL is ``None`` (e.g. suppressed by a ``get_{action}_url``
        hook or missing object context) are omitted from the result.
        """
        result = {}
        for action in self.directory:
            url = self._resolve_directory_url(action)
            if url is not None:
                result[f"{action}_url"] = url
        return result


class PageObjectMixin(CRUDDirectoryMixin, ModelInfoMixin, PageMixin):
    object: Any
    list_view_title = ""

    def get_page_class(self):
        return " ".join(filter(None, [super().get_page_class(), self.model_meta.model_name + "-page"]))

    def get_list_title(self):
        """Return the title to use for the list view link in the form header.

        Returns:
            str: Title for the list view link
        """
        return self.list_view_title or self.model_meta.verbose_name_plural.title()

    def get_list_url(self):
        """Return the URL for the list view, or an empty string if suppressed by permission gating."""
        return self._resolve_directory_url("list") or ""

    def get_breadcrumbs(self):
        """Return the list of breadcrumb items for the form view.

        By default, includes a link back to the list view and a final item for the current form.

        Returns:
            list[dict]: List of breadcrumb items with 'text' and optional 'href'
        """

        breadcrumbs = [
            {"text": self.get_list_title(), "href": self.get_list_url()},
            {"text": self.get_page_title()},
        ]
        return breadcrumbs


class NextURLMixin:
    """Mixin to determine the next URL to redirect to after form submission."""

    def get_next_url(self):
        """Return a validated ``next`` URL from the current request, or ``None``.

        On POST requests reads from POST data; on GET requests reads from the
        query string. The candidate URL is validated against the current host
        via ``url_has_allowed_host_and_scheme`` to prevent open redirects.

        Returns:
            str | None: Validated URL, or ``None`` if absent or unsafe.
        """
        if self.request.method == "POST":
            candidate = self.request.POST.get("next")
        else:
            candidate = self.request.GET.get("next")

        if candidate and url_has_allowed_host_and_scheme(
            url=candidate,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return candidate
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["next_url"] = self.get_next_url()
        return context


# =========== Form Mixins ===========


class MVPFormViewMixin(SuccessMessageMixin, BaseTemplateNameMixin, NextURLMixin, PageObjectMixin):
    """Mixin to render forms in AdminLTE layout with auto-detected renderer."""

    base_template_name = "form_view.html"
    page_class = "mvp-form-page"


class MVPModelFormViewMixin(MVPFormViewMixin):
    """Mixin to render model forms in AdminLTE layout with auto-detected renderer.

    Features:

        - Smart redirection after form submission based on 'next' parameter or default to list view
        - Automatic page title generation based on model and action (Create/Edit/Delete)
        - Breadcrumb generation with links back to list and detail views

    """

    def get_success_message(self, cleaned_data):
        return self.success_message % {
            **cleaned_data,
            "verbose_name": self.model_meta.verbose_name,
        }

    def get_lookup_kwargs(self):
        """Extend base lookup kwargs with a CreateView fallback.

        After saving a new object ``self.kwargs`` is still empty, but
        ``self.object`` now has a pk, so we use that to allow ``next=detail``
        redirects after creation.
        """
        if lookup := super().get_lookup_kwargs():
            return lookup
        if obj := getattr(self, "object", None):
            return {self.pk_url_kwarg: obj.pk}
        return {}

    def get_success_url(self):
        """Determine the URL to redirect to after successful form submission.

        Returns:
            str: URL to redirect to
        """
        # Validated external 'next' URL from query string or POST data
        if next_url := self.get_next_url():
            return next_url

        # 'next' as a CRUD action key in POST data (e.g. next=detail)
        # Delegates entirely to _resolve_directory_url, which handles
        # permission gating and object-action guarding automatically.
        next_key = self.request.POST.get("next")
        if next_key and next_key in self.crud_views:
            if url := self._resolve_directory_url(next_key):
                return url

        return self.get_list_url()
