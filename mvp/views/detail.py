import warnings
from typing import Any

from django.urls import reverse
from django.views import generic

from ..config import MVP_CONFIG
from ..warnings import MVPDeprecationWarning
from .base import BaseTemplateNameMixin, ModelInfoMixin, PageMixin

_UNSET = object()


class CRUDDirectoryMixin(ModelInfoMixin):
    """Mixin to provide URLs for related CRUD views in the template context.

    This mixin assumes a standard set of CRUD view names based on the model name and action (list, detail, create, update, delete).

    The ``show_<action>_action`` attributes decide whether a **link** to that action
    is offered on this page. They are display flags, not access control.

    An action link is drawn on one view and points at another. ``show_delete_action``
    on a detail view says "this page offers a delete link", and the delete view it
    points at is a different class that never sees the attribute. Restricting who may
    delete belongs on the delete view, through Django's ``LoginRequiredMixin``,
    ``PermissionRequiredMixin`` or ``UserPassesTestMixin``, or through a package such
    as django-guardian for object-level rules. Hiding a button is not authorization::

        class ProductDetailView(MVPDetailView):
            model = Product

            def show_delete_action(self, user):  # hides the button
                return user.is_staff


        class ProductDeleteView(
            PermissionRequiredMixin, MVPDeleteView
        ):  # closes the door
            model = Product
            permission_required = "shop.delete_product"

    Each attribute accepts a boolean or a callable taking the request user.

    .. deprecated:: 0.16
        The former ``has_<action>_permission`` names are still honoured and still
        decide visibility, with an ``MVPDeprecationWarning``. They are read rather
        than ignored on purpose: ignoring one would reveal a link the project had
        hidden. Removed in 0.18.
    """

    crud_views = MVP_CONFIG["view_names"]
    directory: list[str] = []
    show_list_action = False
    show_detail_action = False
    show_create_action = False
    show_update_action = False
    show_delete_action = False

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

    def show_action(self, action: str) -> bool:
        """Return whether a link to ``action`` should be offered on this page.

        Reads ``show_<action>_action``, calling it with the request user when it is a
        callable. An action with no attribute at all is not shown, so a custom action
        added to ``directory`` stays hidden until the view opts into it.

        This is a display decision. It has no bearing on whether the target view
        accepts the request — see the class docstring.
        """
        legacy_name = f"has_{action}_permission"
        legacy = getattr(self, legacy_name, _UNSET)
        if legacy is not _UNSET:
            warnings.warn(
                f"{legacy_name} is deprecated and will be removed in 0.18; "
                f"rename it to show_{action}_action. Either way it decides only "
                f"whether the link is drawn — it does not restrict access to the "
                f"{action} view, which needs its own access mixin.",
                MVPDeprecationWarning,
                stacklevel=2,
            )
            flag = legacy
        else:
            flag = getattr(self, f"show_{action}_action", None)

        if flag is None:
            return False
        return bool(flag(self.request.user)) if callable(flag) else bool(flag)  # type: ignore[attr-defined]

    def resolve_crud_url(self, action: str) -> str | None:
        """Resolve the URL for a single CRUD action.

        Returns ``None`` when the action is suppressed by a ``None`` return from
        ``get_url_kwargs`` or by ``show_action`` returning ``False``.

        A shown action whose route does not exist raises ``NoReverseMatch`` rather
        than dropping the link, so the misconfiguration surfaces. Suppress an action
        deliberately by returning ``None`` from ``get_url_kwargs``.
        """
        url_kwargs = self.get_url_kwargs(action)
        if url_kwargs is None:
            return None

        if not self.show_action(action):
            return None

        url_name = self._get_view_name(action)

        return reverse(url_name, kwargs=url_kwargs)

    def get_directory(self) -> dict[str, str]:
        """Return a dict mapping ``{action}_url`` keys to resolved URLs.

        Only actions listed in ``self.directory`` are included. Entries whose
        resolved URL is ``None`` (e.g. suppressed by a ``get_url_kwargs``
        return of ``None`` or a hidden action) are omitted from the result.
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
        model = self.get_model_class_or_none()
        model_page_class = f"{model._meta.model_name}-page" if model else None
        return " ".join(filter(None, [super().get_page_class(), model_page_class]))

    def get_list_title(self):
        """Return the title to use for the list view link in the form header.

        Returns:
            str: Title for the list view link
        """
        return self.list_view_title or self.model_meta.verbose_name_plural.title()

    def get_breadcrumbs(self):
        """Return the list of breadcrumb items for the form view.

        By default, includes a link back to the list view and a final item for
        the current form. The list-view crumb is omitted entirely on a
        model-less view (a plain ``MVPFormView``, by design) — there is no
        list view for it to link to.

        Returns:
            list[dict]: List of breadcrumb items with 'text' and optional 'href'
        """

        breadcrumbs = []
        if self.get_model_class_or_none() is not None:
            breadcrumbs.append(
                {
                    "text": self.get_list_title(),
                    "href": self.resolve_crud_url("list") or "",
                }
            )
        breadcrumbs.append({"text": self.get_page_title()})
        return breadcrumbs


class MVPDetailView(BaseTemplateNameMixin, PageObjectMixin, generic.DetailView):
    base_template_name = "detail_view.html"
    page_class = "mvp-detail-page"

    #: Actions offered in the page header. Each still resolves to a URL only
    #: when its ``show_<action>_action`` allows it, so the default is inert
    #: until a view opts in. The list action is deliberately absent:
    #: the breadcrumb trail already links it.
    directory = ["update", "delete"]

    def get_page_title(self):
        return str(self.object)
