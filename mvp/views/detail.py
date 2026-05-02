from functools import cached_property
from typing import Any

from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from django.views import generic

from ..config import MVP_DEFAULT_VIEW_NAMES
from .base import BaseTemplateNameMixin, PageMixin

_OBJECT_ACTIONS = frozenset({"detail", "update", "delete"})


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
        lookup_kwargs = self.get_lookup_kwargs()
        if action in self._OBJECT_ACTIONS and not lookup_kwargs:
            return None

        url_name = self._get_view_name(action)

        # Only generate a URL if has_<action>_permission exists and returns True
        perm = getattr(self, f"has_{action}_permission", None)
        if perm is None:
            return None
        allowed = perm(self.request.user) if callable(perm) else bool(perm)
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


class MVPDetailView(BaseTemplateNameMixin, PageObjectMixin, generic.DetailView):
    base_template_name = "detail_view.html"
    page_class = "mvp-detail-page"

    def get_page_title(self):
        return str(self.object)
