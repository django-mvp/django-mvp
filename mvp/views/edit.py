from urllib.parse import urlencode
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, FormView, UpdateView
from django.contrib.messages.views import SuccessMessageMixin
from .generic import PageMixin, NextURLMixin

# =========== Generic Form Views ===========


class MVPFormViewMixin(SuccessMessageMixin, NextURLMixin, PageMixin):
    """Mixin to render forms in AdminLTE layout with auto-detected renderer."""

    base_template_name = "form_view.html"

    def get_context_data(self, **kwargs):
        """Inject form renderer and page title into template context.

        Returns:
            dict: Context with form_renderer and page_title added
        """
        context = super().get_context_data(**kwargs)
        return context

    def get_template_names(self):
        """Determine the template to use for rendering the form.

        Returns:
            list[str]: List of template names to search, with the most specific first
        """
        template_names = super().get_template_names()
        template_names.append(self.base_template_name)
        return template_names


class MVPFormView(MVPFormViewMixin, FormView):
    """FormView with AdminLTE layout and auto-detected form rendering.

    Combines MVPFormViewMixin with Django's FormView to provide a complete
    form view with automatic renderer detection and AdminLTE card layout.

    Inherits all attributes and methods from MVPFormViewMixin and FormView.

    Example:
        class ContactView(MVPFormView):
            form_class = ContactForm
            success_url = "/contact/success/"
            page_title = "Contact Us"
    """

    pass

# ========== Model Form Views ===========

class MVPModelFormViewMixin(MVPFormViewMixin):
    """Mixin to render model forms in AdminLTE layout with auto-detected renderer.
    
    Features:

        - Smart redirection after form submission based on 'next' parameter or default to list view
        - Automatic page title generation based on model and action (Create/Edit/Delete)
        - Breadcrumb generation with links back to list and detail views
    
    """
    crud_views = {
        "list": "{model_name}-list",
        "detail": "{model_name}-detail",
        "create": "{model_name}-create",
        "update": "{model_name}-update",
        "delete": "{model_name}-delete",
    }
    list_view_title = ""

    def get_success_message(self, cleaned_data):
        return self.success_message % {
            **cleaned_data,
            "verbose_name": self.model._meta.verbose_name,
        }

    def get_lookup_kwargs(self):
        """
        Return kwargs for reversing URLs for this object,
        respecting how it was looked up (pk, slug, or both).
        """
        kwargs = {}

        # Respect configured kwarg names
        if hasattr(self, "pk_url_kwarg") and self.kwargs.get(self.pk_url_kwarg) is not None:
            kwargs[self.pk_url_kwarg] = self.object.pk

        if hasattr(self, "slug_url_kwarg") and self.kwargs.get(self.slug_url_kwarg) is not None:
            slug_value = getattr(self.object, self.slug_field, None)
            if slug_value is not None:
                kwargs[self.slug_url_kwarg] = slug_value

        # Fallback for CreateView or missing kwargs
        # if not kwargs:
            # return {getattr(self, "pk_url_kwarg", "pk"): self.object.pk}

        return kwargs

    def get_success_url(self):
        """Determine the URL to redirect to after successful form submission.

        Returns:
            str: URL to redirect to
        """
        # Check for 'next' parameter in query string
        if next_url := self.request.GET.get('next'):
            return next_url

        # Check for 'next' field in form data
        next_key = self.request.POST.get('next')
        if next_key and next_key in self.crud_views:
            url_name = self._get_view_name(next_key)
            if next_key in ["detail", "update"]:
                return reverse(url_name, kwargs=self.get_lookup_kwargs())

            return reverse(url_name)

        return self.get_list_url()

    def get_list_title(self):
        """Return the title to use for the list view link in the form header.

        Returns:
            str: Title for the list view link
        """
        return self.list_view_title or self.model._meta.verbose_name_plural.title()

    def _get_view_name(self, action):
        """Helper method to get the URL name for a given CRUD action.

        Args:
            action (str): One of 'list', 'detail', 'create', 'update'
        """

        if action not in self.crud_views:
            raise ValueError(f"Invalid action '{action}'. Must be one of: {', '.join(self.crud_views.keys())}")
        return self.crud_views[action].format(
            model_name=self.model._meta.model_name,
            app_name=self.model._meta.app_label
        )

    def get_list_url(self):
        """Return the URL to use for the list view link in the form header.

        Returns:
            str: URL for the list view link
        """
        if list_view_name := self._get_view_name("list"):
            return reverse(list_view_name)
        return ""

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

    def get_page_title(self):
        title = super().get_page_title()
        if not title:
            return ""
        return title % {"verbose_name": self.model._meta.verbose_name}


class MVPCreateView(MVPModelFormViewMixin, CreateView):
    """CreateView with AdminLTE layout and auto-detected form rendering."""

    page_icon = "add"
    page_title = _("Create %(verbose_name)s")
    success_message = _("%(verbose_name)s successfully created.")


class MVPUpdateView(MVPModelFormViewMixin, UpdateView):
    """UpdateView with AdminLTE layout and auto-detected form rendering."""
    page_icon = "edit"
    page_title = _("Update %(verbose_name)s")
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

        breadcrumbs = [
            {"text": self.get_list_title(), "href": self.get_list_url()},
            {"text": str(self.object), "href":self.object.get_absolute_url()},
            {"text": self.get_page_title()},
        ]
        return breadcrumbs

    def get_delete_url(self):
        """Return the URL to use for the delete view link in the form header.

        Appends ``?next=<list url>`` so the delete view redirects to the list
        after a successful deletion rather than back to the (now-gone) object.

        Returns:
            str: URL for the delete view link
        """
        if delete_view_name := self._get_view_name("delete"):
            url = reverse(delete_view_name, kwargs=self.get_lookup_kwargs())
            back_url = reverse(self._get_view_name("update"), kwargs=self.get_lookup_kwargs())
            next_url = self.get_list_url()
            params = urlencode({"back": back_url, "next": next_url})
            return f"{url}?{params}"
        return ""


class MVPDeleteView(MVPModelFormViewMixin, DeleteView):
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
    page_title = _("Delete %(verbose_name)s")
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
        from django.utils.http import url_has_allowed_host_and_scheme
        candidate = self.request.GET.get("back")
        if candidate and url_has_allowed_host_and_scheme(
            url=candidate,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return candidate
        return self.get_list_url()

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
        return self.get_list_url()

    def get_success_url(self):
        """Redirect to the validated ``next`` URL from POST, or the list view."""
        return super().get_next_url() or self.get_list_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        related_map, protected_objects = self._collect_deletion_data()

        context["is_protected"] = bool(protected_objects)
        context["protected_objects"] = protected_objects
        context["require_confirmation"] = self.require_confirmation
        context["confirmation_value"] = (
            self.get_confirmation_value() if self.require_confirmation else ""
        )
        context["confirmation_label"] = self.confirmation_label

        if self.show_related_objects and not protected_objects:
            context["related_objects"] = [
                (model._meta.verbose_name_plural.title(), objs)
                for model, objs in related_map.items()
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
        from django.contrib import messages
        from django.db.models.deletion import ProtectedError
        from django.http import HttpResponseRedirect

        self.object = self.get_object()

        if self.require_confirmation:
            submitted = request.POST.get("confirmation", "").strip()
            if submitted != self.get_confirmation_value():
                return self.render_to_response(
                    self.get_context_data(
                        confirmation_error=_(
                            "The value you entered does not match. Please try again."
                        )
                    )
                )

        success_url = self.get_success_url()
        try:
            self.object.delete()
        except ProtectedError:
            return self.render_to_response(self.get_context_data())

        messages.success(request, self.get_success_message({}))
        return HttpResponseRedirect(success_url)
