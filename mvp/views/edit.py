import logging
from collections import defaultdict
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ImproperlyConfigured
from django.db.models.deletion import ProtectedError
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.text import camel_case_to_spaces
from django.utils.translation import gettext_lazy as _
from django.views import generic

from .base import BaseTemplateNameMixin
from .detail import PageObjectMixin

logger = logging.getLogger(__name__)


class NextURLMixin:
    """Mixin to determine the next URL to redirect to after form submission."""

    def get_next_candidate(self):
        """Return the raw next URL candidate from the request, without validation."""
        if self.request.method == "POST":
            return self.request.POST.get("next")
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
            str | None: Validated URL path, or ``None`` if absent or unsafe.
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

        # Emit a warning when a candidate was present but rejected.
        if candidate and settings.DEBUG:
            logger.warning(
                "next parameter %r rejected (unsafe or cross-origin); falling back to default destination.",
                candidate,
            )
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["next_url"] = self.get_next_url()
        return context


class MVPFormBase(SuccessMessageMixin, BaseTemplateNameMixin, NextURLMixin, PageObjectMixin):
    """Base class for form views in AdminLTE layout with auto-detected renderer."""

    base_template_name = "form_view.html"
    page_class = "mvp-form-page"

    def get_next_url(self):
        """Extend NextURLMixin by resolving CRUD shorthands into real URLs.

        If the candidate is a recognised CRUD shorthand it is resolved via
        ``resolve_crud_url()`` and the resulting URL is returned directly,
        bypassing the open-redirect validation (the resolved URL is always
        same-origin).  When resolution fails (e.g. no pk is available yet on
        a create view) ``None`` is returned.
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
        """Determine the URL to redirect to after successful form submission.

        Priority chain:

        1. ``get_next_url()`` — validated same-origin ``next`` URL, or a
           resolved CRUD action shorthand (e.g. ``"list"``, ``"detail"``)
        2. Django ``FormMixin.get_success_url()`` — uses ``success_url`` attribute

        Returns:
            str: URL to redirect to
        """
        if next_url := self.get_next_url():
            return next_url
        if getattr(self, "success_url", None):
            return str(self.success_url)
        raise ImproperlyConfigured(
            f"'{self.__class__.__name__}' must define 'success_url' or override 'get_success_url()'."
        )


class MVPModelFormBase(MVPFormBase):
    """Base class for model form views in AdminLTE layout with auto-detected renderer."""

    page_title = ""

    def get_page_title(self) -> str:
        """Return a model-aware page title, or the explicit override if set.

        When ``page_title`` is not falsy, uses it to create an interpolated string using
        the model's verbose_name capitalised with title. For example, for ``page_title = _("Create %(verbose_name)s")``,
        and a ``Product`` model with ``verbose_name = "product"``, a title will be produced as ``"Create Product"``; a model with
        ``verbose_name = "order line"`` produces ``"Create Order Line"``.

        Returns:
            str: The page title to display.
        """
        if not self.page_title:
            return self.page_title
        return self.page_title % {"verbose_name": self.model_meta.verbose_name.title()}

    def get_success_message(self, cleaned_data):
        """Return the interpolated success message for this form submission.

        ``%(verbose_name)s`` is always substituted with the model's verbose name.
        Any other ``%(key)s`` placeholders present in ``success_message`` are
        filled from ``cleaned_data``; keys absent from ``cleaned_data`` (e.g.
        ``%(name)s`` on a delete view, which has no form fields) silently
        substitute ``""`` via ``collections.defaultdict(str)`` — no
        ``KeyError`` is raised.

        Args:
            cleaned_data (dict): Validated form field values (may be empty on
                delete views).

        Returns:
            str: The formatted success message.
        """
        data = defaultdict(str, cleaned_data)
        data["verbose_name"] = self.model_meta.verbose_name
        return self.success_message % data

    def get_url_kwargs(self, action: str) -> dict | None:
        """Extend base URL kwargs with a CreateView fallback.

        After saving a new object ``self.kwargs`` is still empty, but
        ``self.object`` now has a pk, so we use that to allow ``next=detail``
        redirects after creation.
        """
        result = super().get_url_kwargs(action)
        if result is not None:
            return result
        if obj := getattr(self, "object", None):
            return {self.pk_url_kwarg: obj.pk}
        return None

    def get_success_url(self):
        """Determine the URL to redirect to after successful form submission.

        Priority chain (4 steps):

        1. **next URL**: A validated ``?next=`` or ``POST next=`` value from
           :meth:`get_next_url` (safe-URL check applied; CRUD shorthands are
           resolved via :meth:`resolve_crud_url`).

        2. **success_url as CRUD shorthand**: If ``success_url`` is set, it is
           first tried as an argument to :meth:`resolve_crud_url`.  If it
           resolves to a known CRUD URL (e.g. ``"list"``, ``"detail"``), that
           URL is returned.  If resolution fails (unknown key, missing
           permission, unregistered name), the value is used verbatim as a
           literal URL path (step 2b).

        3. **object.get_absolute_url()**: When neither a next URL nor
           ``success_url`` is available, the saved ``self.object`` is checked
           for a ``get_absolute_url()`` method.  If present, its return value
           is used.

        4. **ImproperlyConfigured**: Raised when the previous three steps all
           fail — typically because ``self.object`` is absent (delete views
           after deletion) or the model does not define ``get_absolute_url()``.
           Add ``success_url = "list"`` (or any valid CRUD shorthand / literal
           path) to fix this error.

        Returns:
            str: URL to redirect to.

        Raises:
            ImproperlyConfigured: When no redirect URL can be determined.
        """
        # Step 1: validated next URL / CRUD shorthand
        if next_url := self.get_next_url():
            return next_url

        # Step 2: success_url — tried as CRUD shorthand first, then literal path
        raw = getattr(self, "success_url", None)
        if raw:
            try:
                resolved = self.resolve_crud_url(str(raw))
            except Exception:
                resolved = None
            if resolved:
                return resolved
            return str(raw)

        # Step 3: object.get_absolute_url() final fallback
        obj = getattr(self, "object", None)
        if obj is not None and callable(getattr(obj, "get_absolute_url", None)):
            return obj.get_absolute_url()

        raise ImproperlyConfigured(
            f"'{self.__class__.__name__}' could not determine a redirect URL. "
            f"Set 'success_url' (e.g. 'list'), or ensure the model defines "
            f"'get_absolute_url()'."
        )


class MVPFormView(MVPFormBase, generic.FormView):
    """FormView with AdminLTE layout and auto-detected form rendering.

    Combines MVPFormBase with Django's FormView to provide a complete
    form view with automatic renderer detection and AdminLTE card layout.

    Inherits all attributes and methods from MVPFormBase and FormView.

    Example:
        class ContactView(MVPFormView):
            form_class = ContactForm
            success_url = "/contact/success/"
            page_title = "Contact Us"
    """

    page_class = "mvp-form-page"

    def get_success_message(self, cleaned_data):
        """Return the interpolated success message for this non-model form submission.

        Unlike :meth:`MVPModelFormBase.get_success_message`, this method does
        **not** inject ``verbose_name`` into the substitution dict — there is no
        model associated with a plain ``FormView``.  Any ``%(key)s`` placeholder
        absent from ``cleaned_data`` silently substitutes ``""`` via
        ``collections.defaultdict(str)``; no ``KeyError`` is raised.

        Args:
            cleaned_data (dict): Validated form field values from the submitted form.

        Returns:
            str: The formatted success message, or ``""`` when ``success_message``
            is falsy.
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
        word with ``.title()``.  For example, a class named
        ``ContactFormView`` returns ``"Contact Form View"``.

        Returns:
            str: The page title to display in the template.
        """
        if self.page_title:
            return str(self.page_title)
        return camel_case_to_spaces(self.__class__.__name__).title()


class MVPCreateView(MVPModelFormBase, generic.CreateView):
    """CreateView with AdminLTE layout and auto-detected form rendering."""

    page_title = _("Create %(verbose_name)s")
    page_icon = "add"
    page_class = "mvp-form-page mvp-create-page"
    success_message = _("%(verbose_name)s successfully created.")


class MVPUpdateView(MVPModelFormBase, generic.UpdateView):
    """UpdateView with AdminLTE layout and auto-detected form rendering."""

    page_icon = "edit"
    page_title = _("Update Entry")
    page_class = "mvp-form-page mvp-update-page"
    success_message = _("%(verbose_name)s successfully updated.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["delete_url"] = self.get_delete_url()
        return context

    def get_breadcrumbs(self):
        """Return the list of breadcrumb items for the form view.

        By default, includes a link back to the list view and a final item for the current form.

        Returns:
            list[dict]: List of breadcrumb items with 'text' and optional 'href'
        """
        return [
            {"text": self.get_list_title(), "href": self.resolve_crud_url("list")},
            {"text": str(self.object), "href": self.object.get_absolute_url()},
            {"text": self.get_page_title()},
        ]

    def get_delete_url(self):
        """Return the URL to use for the delete view link in the form header.

        Routes through ``resolve_crud_url("delete")`` so that
        ``has_delete_permission`` gates the URL. Appends ``?back=<update url>&next=<list url>``
        so the delete view redirects to the list after successful deletion.

        Returns:
            str: URL for the delete view link, or empty string when suppressed.
        """
        url = self.resolve_crud_url("delete")
        if not url:
            return ""
        back_url = reverse(self._get_view_name("update"), kwargs=self.get_url_kwargs("update"))
        next_url = self.resolve_crud_url("list")
        params = urlencode({"back": back_url, "next": next_url})
        return f"{url}?{params}"


class MVPDeleteView(MVPModelFormBase, generic.DeleteView):
    """DeleteView with AdminLTE layout, enhanced for four deletion scenarios.

    Scenarios (all configurable via class attributes):

    1. **Basic** (default) — warning message, Go Back, Delete button.
    2. **Related objects summary** — opt-in; shows cascade-deleted related records
       before the user commits. Set ``show_related_objects = True``.
    3. **Protected object** — auto-detected; shows which records block deletion,
       hides the Delete button.
    4. **Type-to-confirm** — opt-in; user must type ``confirmation_value`` into an
       input before the Delete button becomes active. Set ``require_confirmation = True``.

    Attributes:
        show_related_objects (bool): Show a summary of cascade-deleted related
            records. Defaults to ``False``.
        require_confirmation (bool): Require the user to type the object name (or
            a custom string) before deletion proceeds. Defaults to ``False``.
        confirmation_label (str): Label for the confirmation input.
    """

    base_template_name = "delete_view.html"
    page_icon = "delete"
    page_class = "mvp-delete-page"
    page_title = _("Delete Entry")
    success_message = _("%(verbose_name)s successfully deleted.")

    show_related_objects: bool = False
    require_confirmation: bool = False
    confirmation_label: str = _("Type the name to confirm")

    def get_confirmation_value(self) -> str:
        """Return the string the user must type. Override to customise.

        Defaults to ``str(self.object)``.
        """
        return str(self.object)

    def _collect_deletion_data(self):
        """Use Django's Collector to inspect what would happen on delete.

        Returns:
            tuple[dict, list]:
                - related: ``{model: [instances]}`` for cascade relations
                  (excluding the object itself). Empty dict when protected.
                - protected: list of objects blocking deletion via PROTECT.
                  Empty list when deletion is safe.
        """
        from django.db.models.deletion import Collector, ProtectedError

        using = self.object._state.db
        collector = Collector(using=using)
        try:
            collector.collect([self.object])
        except ProtectedError as exc:
            return {}, list(exc.protected_objects)

        related = {}
        for model, instances in collector.data.items():
            if model is type(self.object):
                continue
            if instances:
                related[model] = list(instances)
        return related, []

    def get_back_url(self) -> str:
        """Return the URL for the Go Back button.

        Reads ``?back`` from the GET query string, validates it against the
        current host, and falls back to the list URL.

        Returns:
            str: Validated back URL, or list URL as fallback.
        """
        candidate = self.request.GET.get("back")
        if candidate and url_has_allowed_host_and_scheme(
            url=candidate,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return candidate
        return self.resolve_crud_url("list")

    def get_next_url(self):
        """Return the URL for the post-delete redirect.

        Priority:
        1. Validated ``next`` query parameter from the incoming request
        2. List URL

        Note: We deliberately do NOT fall back to ``get_absolute_url()`` here.
        That URL belongs to the object being deleted — after deletion it would
        be a 404. The list is always a safe fallback.

        Returns:
            str: URL to navigate back to
        """
        if next_url := super().get_next_url():
            return next_url
        return self.resolve_crud_url("list")

    def get_success_url(self):
        """Redirect to the validated ``next`` URL from POST, or the list view."""
        return super().get_next_url() or self.resolve_crud_url("list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        related_map, protected_objects = self._collect_deletion_data()

        context["is_protected"] = bool(protected_objects)
        context["protected_objects"] = protected_objects
        context["require_confirmation"] = self.require_confirmation
        context["confirmation_value"] = self.get_confirmation_value() if self.require_confirmation else ""
        context["confirmation_label"] = self.confirmation_label

        if self.show_related_objects and not protected_objects:
            context["related_objects"] = [
                (model._meta.verbose_name_plural.title(), objs) for model, objs in related_map.items()
            ]
        else:
            context["related_objects"] = []

        context.setdefault("confirmation_error", kwargs.get("confirmation_error", ""))
        context["back_url"] = self.get_back_url()

        return context

    def post(self, request, *args, **kwargs):
        """Handle DELETE confirmation — validates type-to-confirm and catches ProtectedError.

        Overrides ``post()`` rather than ``delete()`` because Django 5.x's
        ``BaseDeleteView.post()`` calls ``form_valid()`` directly, bypassing
        any ``delete()`` override in subclasses.
        """

        self.object = self.get_object()

        if self.require_confirmation:
            submitted = request.POST.get("confirmation", "").strip()
            if submitted != self.get_confirmation_value():
                return self.render_to_response(
                    self.get_context_data(
                        confirmation_error=_("The value you entered does not match. Please try again.")
                    )
                )

        success_url = self.get_success_url()
        try:
            self.object.delete()
        except ProtectedError:
            return self.render_to_response(self.get_context_data())

        messages.success(request, self.get_success_message({}))
        return HttpResponseRedirect(success_url)
