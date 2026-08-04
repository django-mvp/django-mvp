from typing import Any

from django.urls import reverse
from django.views import generic

from ..config import MVP_CONFIG
from .base import BaseTemplateNameMixin, ModelInfoMixin, PageMixin


class CRUDDirectoryMixin(ModelInfoMixin):
    """Mixin to provide URLs for related CRUD views in the template context.

    This mixin assumes a standard set of CRUD view names based on the model name and action (list, detail, create, update, delete).

    The ``has_<action>_permission`` attributes decide whether a **link** is offered.
    They do not protect the view that link points at. Each target view enforces its
    own access control, or it has none — hiding a button is not authorization.
    """

    crud_views = MVP_CONFIG["view_names"]
    directory: list[str] = []
    has_list_permission = False
    has_detail_permission = False
    has_create_permission = False
    has_update_permission = False
    has_delete_permission = False

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
            raise ValueError(
                f"Invalid action '{action}'. Must be one of: {', '.join(self.crud_views.keys())}"
            )
        return self.crud_views[action].format(
            model_name=self.model_meta.model_name, app_name=self.model_meta.app_label
        )

    def get_url_kwargs(self, action: str) -> dict | None:
        """Return URL kwargs for reversing the URL for ``action``.

        Default behaviour:
        - ``"list"`` and ``"create"`` → ``{}`` (collection-level, no object needed).
        - All other actions → ``dict(self.kwargs)`` or ``None`` when kwargs are empty.

        Override to branch on ``action`` for nested URL patterns::

            def get_url_kwargs(self, action: str) -> dict | None:
                if action in {"list", "create"}:
                    return {"project_pk": self.kwargs["project_pk"]}
                pk = self.kwargs.get("pk")
                if pk is None:
                    return None
                return {"project_pk": self.kwargs["project_pk"], "pk": pk}

        Return ``None`` to suppress the action silently (no URL generated, no error raised).
        """
        if action in {"list", "create"}:
            return {}
        return dict(self.kwargs) or None  # type: ignore[attr-defined]

    def resolve_crud_url(self, action: str) -> str | None:
        """Resolve the URL for a single CRUD action.

        Returns ``None`` when the action is suppressed by a ``None`` return from
        ``get_url_kwargs``, a missing/falsy permission attribute, or a falsy callable.

        A granted permission whose route does not exist raises ``NoReverseMatch``
        rather than dropping the link, so the misconfiguration surfaces. Suppress an
        action deliberately by returning ``None`` from ``get_url_kwargs``.
        """
        url_kwargs = self.get_url_kwargs(action)
        if url_kwargs is None:
            return None

        url_name = self._get_view_name(action)

        # Only generate a URL if has_<action>_permission exists and evaluates to True
        perm = getattr(self, f"has_{action}_permission", None)
        if perm is None:
            return None
        allowed = perm(self.request.user) if callable(perm) else bool(perm)  # type: ignore[attr-defined]
        if not allowed:
            return None

        return reverse(url_name, kwargs=url_kwargs)

    def get_directory(self) -> dict[str, str]:
        """Return a dict mapping ``{action}_url`` keys to resolved URLs.

        Only actions listed in ``self.directory`` are included. Entries whose
        resolved URL is ``None`` (e.g. suppressed by a ``get_url_kwargs``
        return of ``None`` or missing permission) are omitted from the result.
        """
        result = {}
        for action in self.directory:
            url = self.resolve_crud_url(action)
            if url is not None:
                result[f"{action}_url"] = url
        return result


class PageObjectMixin(CRUDDirectoryMixin, PageMixin):
    object: Any
    list_view_title = ""

    def get_page_class(self):
        return " ".join(
            filter(
                None, [super().get_page_class(), self.model_meta.model_name + "-page"]
            )
        )

    def get_list_title(self):
        """Return the title to use for the list view link in the form header.

        Returns:
            str: Title for the list view link
        """
        return self.list_view_title or self.model_meta.verbose_name_plural.title()

    def get_breadcrumbs(self):
        """Return the list of breadcrumb items for the form view.

        By default, includes a link back to the list view and a final item for the current form.

        Returns:
            list[dict]: List of breadcrumb items with 'text' and optional 'href'
        """

        breadcrumbs = [
            {
                "text": self.get_list_title(),
                "href": self.resolve_crud_url("list") or "",
            },
            {"text": self.get_page_title()},
        ]
        return breadcrumbs


class MVPDetailView(BaseTemplateNameMixin, PageObjectMixin, generic.DetailView):
    base_template_name = "detail_view.html"
    page_class = "mvp-detail-page"

    #: Actions offered in the page header. Each still resolves to a URL only
    #: when its ``has_<action>_permission`` allows it, so the default is inert
    #: until a view grants permission. The list action is deliberately absent:
    #: the breadcrumb trail already links it.
    directory = ["update", "delete"]

    def get_page_title(self):
        return str(self.object)
