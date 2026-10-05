"""Form, create, update and delete views with redirect and message handling."""

import logging
from collections import defaultdict
from typing import Any
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ImproperlyConfigured
from django.db.models.deletion import Collector, ProtectedError, RestrictedError
from django.http import HttpResponseRedirect
from django.urls import NoReverseMatch, reverse
from django.utils.functional import Promise
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.text import camel_case_to_spaces
from django.utils.translation import gettext_lazy as _
from django.views import generic

from ..forms import DeleteConfirmForm
from .base import BaseTemplateNameMixin
from .detail import PageObjectMixin
from .inline import InlinesMixin

logger = logging.getLogger(__name__)


class NextURLMixin:
    """Mixin to determine the next URL to redirect to after form submission."""

    def get_next_candidate(self):
        """Return the raw next URL candidate from the request, without validation.

        On POST, an explicit ``next`` value (the hidden field carrying a caller-
        supplied ``?next=`` through the form) always wins. ``default_next`` — the
        name/value pair contributed by whichever submit button was clicked, e.g.
        "Save & continue" → ``default_next=list`` — is consulted only when no
        explicit ``next`` was supplied. A button must never override a caller's
        destination; it only proposes one when the caller didn't ask for a
        specific place to land.

        Returns:
            The unvalidated ``next`` candidate, or ``None`` when the request has none.
        """
        if self.request.method == "POST":
            return self.request.POST.get("next") or self.request.POST.get(
                "default_next"
            )
        return self.request.GET.get("next")

    def get_next_url(self):
        """Return a validated ``next`` URL from the current request, or ``None``.

        On POST requests reads from POST data; on GET requests reads from the
        query string. The candidate URL is validated against the current host
        via ``url_has_allowed_host_and_scheme`` to prevent open redirects.

        Validation rules:

        - Bare words (e.g. ``"list"``) that don't start with ``"/"`` or
          contain ``"://"`` are rejected (open-redirect protection).
        - Cross-origin or unsafe-scheme URLs are rejected.
        - When ``settings.DEBUG`` is ``True``, a ``logger.warning`` is emitted
          for every rejected candidate to aid development.

        Returns:
            Validated URL path, or ``None`` if absent or unsafe.
        """
        candidate = self.get_next_candidate()

        # Require the candidate to look like a URL (starts with "/" or contains "://")
        # to prevent bare words from being treated as valid relative paths.
        if candidate and not (candidate.startswith("/") or "://" in candidate):
            if settings.DEBUG:
                logger.warning(
                    "next parameter %r rejected (unsafe or cross-origin); falling back to default destination.",
                    candidate,
                )
            return None

        if candidate and url_has_allowed_host_and_scheme(
            url=candidate,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return candidate

        if candidate and settings.DEBUG:
            logger.warning(
                "next parameter %r rejected (unsafe or cross-origin); falling back to default destination.",
                candidate,
            )
        return None

    def get_context_data(self, **kwargs):
        """Add the validated ``next`` URL to the context as ``next_url``."""
        context = super().get_context_data(**kwargs)
        context["next_url"] = self.get_next_url()
        return context


class MVPFormBase(
    SuccessMessageMixin, BaseTemplateNameMixin, NextURLMixin, PageObjectMixin
):
    """Base class for form views: page layout, ``next`` handling and redirects."""

    base_template_name = "form_view.html"
    page_class = "mvp-form-page"

    def get_next_url(self):
        """Extend NextURLMixin by resolving CRUD shorthands into real URLs.

        If the candidate is a recognised CRUD shorthand it is resolved via
        ``resolve_crud_url()`` and the resulting URL is returned directly,
        bypassing the open-redirect validation (the resolved URL is always
        same-origin).  When resolution fails (e.g. no pk is available yet on
        a create view) ``None`` is returned.

        Returns:
            The resolved or validated URL, or ``None`` when there is none.
        """
        candidate = self.get_next_candidate()
        if candidate and hasattr(self, "crud_views") and candidate in self.crud_views:
            try:
                url = self.resolve_crud_url(candidate)
            except Exception:
                return None  # No model configured on this view — fall through silently.
            if url is None and settings.DEBUG:
                logger.warning(
                    "next shorthand %r could not be resolved; falling back to default destination.",
                    candidate,
                )
            return url
        return super().get_next_url()

    def get_success_url(self):
        """Prefer a validated ``next`` URL or CRUD shorthand over ``success_url``.

        Returns:
            The URL to redirect to.

        Raises:
            ImproperlyConfigured: If there is no ``next`` URL and no ``success_url``.
        """
        if next_url := self.get_next_url():
            return next_url
        if getattr(self, "success_url", None):
            return str(self.success_url)
        raise ImproperlyConfigured(
            f"'{self.__class__.__name__}' must define 'success_url' or override 'get_success_url()'."
        )


class MVPModelFormBase(MVPFormBase):
    """Base class for model form views, with model-aware titles and messages."""

    page_title: str | Promise = ""

    def get_page_title(self) -> str:
        """Return a model-aware page title, or the explicit override if set.

        When ``page_title`` is not falsy, it is interpolated with the model's
        title-cased ``verbose_name``. For ``page_title = _("Create %(verbose_name)s")``
        a ``Product`` model gives ``"Create Product"``, and a model with
        ``verbose_name = "order line"`` gives ``"Create Order Line"``.

        Returns:
            The page title to display, or ``""`` when ``page_title`` is unset.
        """
        if not self.page_title:
            return ""
        return self.page_title % {"verbose_name": self.model_meta.verbose_name.title()}

    def get_success_message(self, cleaned_data: dict[str, Any]):
        """Return the interpolated success message for this form submission.

        ``%(verbose_name)s`` is always substituted with the model's verbose name.
        Any other ``%(key)s`` placeholders present in ``success_message`` are
        filled from ``cleaned_data``; keys absent from ``cleaned_data`` (e.g.
        ``%(name)s`` on a delete view, which has no form fields) silently
        substitute ``""`` via ``collections.defaultdict(str)`` — no
        ``KeyError`` is raised.

        Args:
            cleaned_data: Validated form field values (may be empty on delete views).

        Returns:
            The formatted success message.
        """
        data = defaultdict(str, cleaned_data)
        data["verbose_name"] = self.model_meta.verbose_name
        return self.success_message % data

    def get_url_kwargs(self, action: str) -> dict | None:
        """Extend base URL kwargs with a CreateView fallback.

        After saving a new object ``self.kwargs`` is still empty, but
        ``self.object`` now has a pk, so we use that to allow ``next=detail``
        redirects after creation.

        Args:
            action: The CRUD action being linked, e.g. ``"detail"``.

        Returns:
            The kwargs for ``reverse()``, or ``None`` to suppress the action.
        """
        result = super().get_url_kwargs(action)
        if result is not None:
            return result
        if obj := getattr(self, "object", None):
            return {self.pk_url_kwarg: obj.pk}  # type: ignore[attr-defined]
        return None

    def get_success_url(self):
        """Fall back from ``next`` and ``success_url`` to ``get_absolute_url()``.

        Returns:
            The URL to redirect to.

        Raises:
            ImproperlyConfigured: If no ``next`` URL, ``success_url`` or
                ``get_absolute_url()`` is available.
        """
        if next_url := self.get_next_url():
            return next_url

        raw = getattr(self, "success_url", None)
        if raw:
            try:
                resolved = self.resolve_crud_url(str(raw))
            except Exception:
                # Not a resolvable CRUD shorthand, so it is used as a literal path.
                resolved = None
            if resolved:
                return resolved
            return str(raw)

        obj = getattr(self, "object", None)
        if obj is not None and callable(getattr(obj, "get_absolute_url", None)):
            return obj.get_absolute_url()

        raise ImproperlyConfigured(
            f"'{self.__class__.__name__}' could not determine a redirect URL. "
            f"Set 'success_url' (e.g. 'list'), or ensure the model defines "
            f"'get_absolute_url()'."
        )


class MVPFormView(MVPFormBase, generic.FormView):
    """FormView for a form with no model behind it, rendered in the page layout.

    Combines ``MVPFormBase`` with Django's ``FormView``, so it inherits their
    attributes and methods.

    Attributes:
        page_class: CSS class(es) applied to the page wrapper.

    Example:
        class ContactView(MVPFormView):
            form_class = ContactForm
            success_url = "/contact/success/"
            page_title = "Contact Us"
    """

    page_class = "mvp-form-page"

    def get_success_message(self, cleaned_data: dict[str, Any]):
        """Return the interpolated success message for a non-model form submission.

        Unlike :meth:`MVPModelFormBase.get_success_message`, this method does
        **not** inject ``verbose_name`` into the substitution dict — there is no
        model associated with a plain ``FormView``.  Any ``%(key)s`` placeholder
        absent from ``cleaned_data`` silently substitutes ``""`` via
        ``collections.defaultdict(str)``; no ``KeyError`` is raised.

        Args:
            cleaned_data: Validated form field values from the submitted form.

        Returns:
            The formatted success message, or ``""`` when ``success_message`` is
            falsy.
        """
        if not self.success_message:
            return ""
        data = defaultdict(str, cleaned_data)
        return self.success_message % data

    def get_page_title(self):
        """Return the page title for this form view.

        When :attr:`page_title` is set (truthy), returns it directly.
        When :attr:`page_title` is falsy (unset or empty), derives a readable
        default from the concrete class name using
        :func:`django.utils.text.camel_case_to_spaces` and capitalises each
        word with ``.title()``.

        Returns:
            The page title to display in the template.
        """
        if self.page_title:
            return str(self.page_title)
        return camel_case_to_spaces(self.__class__.__name__).title()


class MVPCreateView(InlinesMixin, MVPModelFormBase, generic.CreateView):
    """CreateView rendered in the page layout, with an optional set of inlines.

    Set ``inlines`` to add one or more related row sets to the page — see
    ``InlinesMixin``. Leaving ``inlines`` unset is a no-op: the view behaves
    exactly like a plain ``CreateView``.
    """

    page_title = _("Create %(verbose_name)s")
    page_class = "mvp-form-page mvp-create-page"
    success_message = _("%(verbose_name)s successfully created.")

    def get_success_message(self, cleaned_data):
        """Title-case ``verbose_name`` so the message opens with a capital letter."""
        data = defaultdict(str, cleaned_data)
        data["verbose_name"] = self.model_meta.verbose_name.title()
        return self.success_message % data


class MVPUpdateView(InlinesMixin, MVPModelFormBase, generic.UpdateView):
    """Concrete model update view with zero-config page layout integration.

    A minimal subclass needs only ``model`` and ``fields``; everything else is
    auto-derived from the model's ``verbose_name``.  The page title, breadcrumb,
    and delete-button visibility all adapt automatically to whatever CRUD directory
    the developer has configured.

    Set ``inlines`` to add one or more related row sets to the page — see
    ``InlinesMixin``. Leaving ``inlines`` unset is a no-op: the view behaves
    exactly like a plain ``UpdateView``.

    Config:
        page_title (str | lazy str): Interpolation template for the page heading.
            Defaults to ``_("Update %(verbose_name)s")``; ``%(verbose_name)s`` is
            replaced at runtime with the title-cased model verbose name.
        page_class (str): CSS class(es) applied to the page wrapper.
            Defaults to ``"mvp-form-page mvp-update-page"``.
        success_message (str | lazy str): Flash message template shown after a
            successful save.  ``%(verbose_name)s`` is replaced with the
            title-cased model verbose name (e.g. "Product").
            Defaults to ``_("%(verbose_name)s successfully updated.")``.
        success_url (str | None): Redirect target after save.  Accepts literal
            URL paths or CRUD action shorthands (``"list"``, ``"detail"``).
            Defaults to ``None`` (falls back to ``get_absolute_url()`` then
            ``ImproperlyConfigured``).
        fields (list[str]): Required. Model fields to include in the form.
        model (Model): Required. The Django model class to update.

    Override hooks:
        get_breadcrumbs(): Returns the three-level breadcrumb list.  Override to
            replace the default list → detail → form structure.
        get_delete_url(): Returns the delete-button href with ``?back`` and
            ``?next`` params, or ``""`` when the delete view is not registered.
        get_page_title(): Inherited from ``MVPModelFormBase``; interpolates
            ``page_title`` with the model's title-cased ``verbose_name``.
        get_success_message(cleaned_data): Inherited from ``MVPModelFormBase``;
            interpolates ``success_message`` with ``verbose_name`` and
            ``cleaned_data``.
        get_success_url(): Inherited from ``MVPModelFormBase``; priority chain:
            next URL → ``success_url`` → ``object.get_absolute_url()``.

    Example::

        class ProductUpdateView(MVPUpdateView):
            model = Product
            fields = ["name", "slug", "price"]
            show_list_action = True
            show_detail_action = True
            show_delete_action = True
    """

    page_title = _("Update %(verbose_name)s")
    page_class = "mvp-form-page mvp-update-page"
    success_message = _("%(verbose_name)s successfully updated.")

    def get_context_data(self, **kwargs):
        """Add the delete button's URL to the context as ``delete_url``."""
        context = super().get_context_data(**kwargs)
        context["delete_url"] = self.get_delete_url()
        return context

    def get_breadcrumbs(self):
        """Return the list of breadcrumb items for the form view.

        By default, includes a link back to the list view, a link to the detail
        view (gated by ``show_detail_action``), and a final item for the current
        form.  When a permission is falsy the affected breadcrumb renders as plain
        text (the ``href|yesno`` filter in the Cotton breadcrumbs component handles
        the ``None``/empty-href case automatically).

        Returns:
            Breadcrumb items, each with ``"text"`` and an optional ``"href"``.
        """
        return [
            {"text": self.get_list_title(), "href": self.resolve_crud_url("list")},
            {"text": str(self.object), "href": self.resolve_crud_url("detail")},
            {"text": self.get_page_title()},
        ]

    def get_delete_url(self):
        """Return the URL to use for the delete view link in the form header.

        Routes through ``resolve_crud_url("delete")`` so that
        ``show_delete_action`` gates the URL. Appends
        ``?back=<update url>&next=<list url>`` so the delete view redirects to the list after successful deletion.

        Returns:
            URL for the delete view link, or empty string when suppressed.
        """
        url = self.resolve_crud_url("delete")
        if not url:
            return ""
        # Not resolve_crud_url("update"): that gates on show_update_action (default
        # False) and would silently drop the back URL.
        try:
            back_url = reverse(
                self._get_view_name("update"), kwargs=self.get_url_kwargs("update")
            )
        except NoReverseMatch:
            back_url = ""
        next_url = self.resolve_crud_url("list")
        params = urlencode({"back": back_url, "next": next_url})
        return f"{url}?{params}"


class MVPDeleteView(MVPModelFormBase, generic.DeleteView):
    """DeleteView rendered in the page layout, covering four deletion scenarios.

    Scenarios (all configurable via class attributes):

    1. **Basic** (default) — warning message, Go Back, Delete button.
    2. **Related objects summary** — opt-in; shows cascade-deleted related records
       before the user commits. Set ``show_related_objects = True``.
    3. **Protected object** — auto-detected; shows which records block deletion,
       hides the Delete button.
    4. **Type-to-confirm** — opt-in; user must type ``confirmation_value`` into an
       input before the Delete button becomes active.
       Set ``require_confirmation = True``.

    Config:
        show_related_objects (bool): Show a summary of cascade-deleted related
            records. Defaults to ``False``.
        require_confirmation (bool): Require the user to type the object name (or
            a custom string) before deletion proceeds. Defaults to ``False``.
        confirmation_label (str): Label for the confirmation input.
            Defaults to ``"Type the name to confirm"``.
        related_objects_max_per_group (int): Maximum number of related objects
            shown per group before an overflow note is displayed.
            Defaults to ``25``.
        related_objects_attrs (dict): Attributes passed straight to daisy-cotton's
            alert that presents the related-objects summary, e.g.
            ``{"variant": "warning"}`` when the cascade is more consequential
            than a routine cleanup. The alert accepts the variants ``info``,
            ``success``, ``warning`` and ``error``. A view that sets it replaces
            the default rather than adding to it. Defaults to
            ``{"variant": "info"}``.

    Override hooks:
        get_confirmation_value(): Returns the string the user must type.
            Defaults to ``str(self.object)``.
        get_back_url(): Returns the URL for the Go Back button.
            Reads ``?back`` from the query string, falling back to the list URL,
            then to ``object.get_absolute_url()`` when there is no list URL. No
            button renders when neither is available.
        get_breadcrumbs(): Returns a three-item breadcrumb list: List → Detail → Delete.
        get_success_url(): Redirect priority: ``?next=`` → ``success_url`` → list URL.
            Does NOT use ``object.get_absolute_url()`` (the object no longer exists
            after deletion).

    Example::

        class ArticleDeleteView(MVPDeleteView):
            model = Article
            require_confirmation = True  # user must type article title
            show_related_objects = True  # preview cascade deletes


        class DatasetDeleteView(MVPDeleteView):
            model = Dataset
            show_related_objects = True
            related_objects_attrs = {"variant": "warning"}  # a consequential cascade
    """

    base_template_name = "delete_view.html"
    page_class = "mvp-delete-page"
    page_title = _("Delete %(verbose_name)s")
    success_message = _("%(verbose_name)s successfully deleted.")

    show_related_objects: bool = False
    require_confirmation: bool = False
    confirmation_label: str | Promise = _("Type the name to confirm")
    related_objects_max_per_group: int = 25
    related_objects_attrs: dict[str, Any] = {"variant": "info"}

    def get_breadcrumbs(self):
        """Return the three-level breadcrumb list: List → Detail → Delete.

        Returns:
            Breadcrumb items, each with ``"text"`` and an optional ``"href"``.
        """
        return [
            {"text": self.get_list_title(), "href": self.resolve_crud_url("list")},
            {"text": str(self.object), "href": self.resolve_crud_url("detail")},
            {"text": self.get_page_title()},
        ]

    def get_confirmation_value(self) -> str:
        """Return the string the user must type. Override to customise.

        Returns:
            The confirmation string; ``str(self.object)`` by default.
        """
        return str(self.object)

    def _collect_deletion_data(self):
        """Use Django's Collector to inspect what would happen on delete.

        Returns:
            A ``(related, protected)`` pair. ``related`` maps each model to the
            instances a cascade would delete (excluding the object itself), and
            is empty when protected. ``protected`` lists the objects blocking
            deletion via PROTECT or RESTRICT, and is empty when deletion is safe.
        """
        using = self.object._state.db
        collector = Collector(using=using)
        try:
            collector.collect([self.object])
        except ProtectedError as exc:
            return {}, list(exc.protected_objects)
        except RestrictedError as exc:
            return {}, list(exc.restricted_objects)

        related = defaultdict(list)
        for model, instances in collector.data.items():
            if model is type(self.object):
                continue
            if instances:
                related[model].extend(instances)

        # Django moves cascades with no children or signal listeners to
        # `fast_deletes`; they are deleted all the same, so reading only
        # `collector.data` would omit the commonest cascade there is.
        for queryset in collector.fast_deletes:
            if queryset.model is type(self.object):
                continue
            instances = list(queryset)
            if instances:
                related[queryset.model].extend(instances)

        return dict(related), []

    def get_form_class(self):
        """Use ``DeleteConfirmForm`` when ``require_confirmation`` is set."""
        if self.require_confirmation:
            return DeleteConfirmForm
        return super().get_form_class()

    def get_form_kwargs(self):
        """Pass the confirmation value and label to the form when it is required."""
        kwargs = super().get_form_kwargs()
        if self.require_confirmation:
            kwargs["confirmation_value"] = self.get_confirmation_value()
            kwargs["confirmation_label"] = self.confirmation_label
        return kwargs

    def form_valid(self, form):
        """Delete the object and add the success message before redirecting."""
        success_url = self.get_success_url()
        self.object.delete()
        messages.success(self.request, self.get_success_message({}))
        return HttpResponseRedirect(success_url)

    def get_back_url(self) -> str:
        """Return the URL for the Go Back button.

        Reads ``?back`` from the GET query string, validates it against the
        current host, and falls back to the list URL. When the page's action
        directory carries no list entry, falls back further to the object's
        own ``get_absolute_url()`` — the record still exists at the moment a
        deletion confirmation page is drawn, so there is always a sensible
        destination. Returns ``""`` (no button rendered) only when neither is
        available.

        Returns:
            Validated back URL, list URL, the object's absolute URL, or ``""``.
        """
        candidate = self.request.GET.get("back")
        if candidate and url_has_allowed_host_and_scheme(
            url=candidate,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return candidate

        list_url = self.resolve_crud_url("list")
        if list_url:
            return list_url

        obj = getattr(self, "object", None)
        get_absolute_url = getattr(obj, "get_absolute_url", None)
        if callable(get_absolute_url):
            try:
                return get_absolute_url() or ""
            except NoReverseMatch:
                # A model may declare get_absolute_url for a route the project
                # never mounted. Anything else raised by a consumer's own method
                # is a bug in it and must not be swallowed here.
                return ""

        return ""

    def get_success_url(self):
        """Fall back from ``next`` and ``success_url`` to the list URL.

        Returns:
            The URL to redirect to.

        Raises:
            ImproperlyConfigured: If no ``next`` URL, ``success_url`` or list URL
                is available.
        """
        if next_url := self.get_next_url():
            return next_url

        raw = getattr(self, "success_url", None)
        if raw:
            try:
                resolved = self.resolve_crud_url(str(raw))
            except Exception:
                # Not a resolvable CRUD shorthand, so it is used as a literal path.
                resolved = None
            if resolved:
                return resolved
            return str(raw)

        # Not object.get_absolute_url(): the object no longer exists after deletion.
        url = self.resolve_crud_url("list")
        if url:
            return url

        raise ImproperlyConfigured(
            f"'{self.__class__.__name__}' could not determine a redirect URL. "
            f"Set 'success_url' (e.g. 'list'), or register a list view with show_list_action=True."
        )

    def get_context_data(self, **kwargs):
        """Add the deletion preview, protection state and confirmation fields."""
        context = super().get_context_data(**kwargs)

        related_map, protected_objects = self._collect_deletion_data()

        context["is_protected"] = bool(protected_objects)
        context["protected_objects"] = protected_objects
        context["require_confirmation"] = self.require_confirmation
        context["confirmation_value"] = (
            self.get_confirmation_value() if self.require_confirmation else ""
        )
        context["confirmation_label"] = self.confirmation_label

        # A protected record cannot be deleted, so the page offers no Delete
        # button — and the confirmation field that would sit above it has
        # nothing to submit to. Drop the form so the page renders neither.
        if protected_objects:
            context["form"] = None

        if self.show_related_objects and not protected_objects:
            cap = self.related_objects_max_per_group
            context["related_objects"] = [
                (
                    model._meta.verbose_name_plural.title(),
                    list(instances)[:cap],
                    max(0, len(instances) - cap),
                )
                for model, instances in related_map.items()
            ]
        else:
            context["related_objects"] = []
        context["related_objects_attrs"] = self.related_objects_attrs

        context["back_url"] = self.get_back_url()

        return context

    def post(self, request, *args, **kwargs):
        """Refuse a protected delete before validating the confirmation form."""
        self.object = self.get_object()
        _, protected = self._collect_deletion_data()
        if protected:
            return self.render_to_response(self.get_context_data())
        form = self.get_form()
        return self.form_valid(form) if form.is_valid() else self.form_invalid(form)
