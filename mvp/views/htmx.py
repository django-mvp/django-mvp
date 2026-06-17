"""
HTMX mixins for Django MVP views.

Provides two classes:

* ``HtmxMixin`` — lightweight base for all htmx-enhanced views; injects
  ``htmx_enabled = True`` into the view context via ``get_context_data()``.
* ``HtmxFormMixin`` — subclass of ``HtmxMixin`` that adds htmx-aware form
  handling: partial rendering on htmx POST, client-side redirects via
  ``HX-Redirect``, and optional ``HX-Trigger`` event emission.

Usage example::

    from mvp.views.htmx import HtmxFormMixin
    from mvp.views import MVPCreateView
    from .models import Product


    class ProductCreateView(HtmxFormMixin, MVPCreateView):
        model = Product
        fields = ["name", "price"]
        htmx_success_component = "ui.product-created"
        success_url = "list"
"""

from django.contrib.messages import get_messages
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django_cotton import render_component
from django_htmx.http import HttpResponseClientRedirect, trigger_client_event


class HtmxMixin:
    """Lightweight base class for all htmx-enhanced Django class-based views.

    Provides functionality shared by all htmx view types. Any future htmx
    mixin (e.g., ``HtmxListViewMixin``) inherits context injection, the
    trigger subsystem, and component-resolution logic without form-specific
    code.

    Import::

        from mvp.views.htmx import HtmxMixin
    """

    htmx_trigger = None
    htmx_trigger_after = "receive"

    def get_context_data(self, **kwargs):
        """Inject ``htmx_enabled = True`` so templates can conditionally render
        htmx-specific attributes (``hx-post``, ``hx-target``, ``hx-swap``).
        """
        context = super().get_context_data(**kwargs)
        context["htmx_enabled"] = True
        return context

    def _apply_htmx_triggers(self, response):
        """Apply HX-Trigger family headers to *response* based on ``htmx_trigger``.

        No-op when ``htmx_trigger`` is falsy.
        """
        if not self.htmx_trigger:
            return response
        if isinstance(self.htmx_trigger, dict):
            for name, params in self.htmx_trigger.items():
                trigger_client_event(
                    response, name, params or {}, after=self.htmx_trigger_after
                )
        else:
            trigger_client_event(
                response, self.htmx_trigger, after=self.htmx_trigger_after
            )
        return response

    def _resolve_component(self, attr, allowlist_attr, header_name):
        """Resolve a Cotton component name using the client-header / allowlist pattern.

        Resolution order:

        1. If ``getattr(self, allowlist_attr)`` is non-empty, look up
           ``self.request.headers.get(header_name)`` in the allowlist dict.
           Return the paired component if the alias matches.
        2. Fall through to ``getattr(self, attr, None)`` as the server default.

        Returns:
            str | None: The resolved component name, or ``None`` if neither
                the allowlist nor the server-default attribute is set.
        """
        allowlist = getattr(self, allowlist_attr, ())
        if allowlist:
            alias = self.request.headers.get(header_name, "").strip()
            if alias:
                component = dict(allowlist).get(alias)
                if component:
                    return component
        return getattr(self, attr, None)


class HtmxFormMixin(HtmxMixin):
    """Mixin that adds HTMX-aware form handling to Django class-based views.

    Inherits from ``HtmxMixin`` (which provides ``htmx_enabled`` context
    injection). Add this mixin before the base view class in the inheritance
    list so that its ``form_valid()`` and ``form_invalid()`` overrides
    intercept first::

        class MyView(HtmxFormMixin, MVPCreateView): ...

    Class Attributes:
        htmx_success_component (str | None):
            Cotton component name (dot-notation) for the success partial.
            Example: ``"ui.product-created"`` → ``cotton/ui/product_created.html``.
        htmx_success_components (tuple[tuple[str, str], ...]):
            Allowlist of ``(alias, component)`` pairs that the requesting HTMX
            element may choose between via the ``X-Success-Component`` request
            header. When the header is present and the alias is found here, that
            component overrides ``htmx_success_component``. Unknown aliases are
            silently ignored and fall through to the default.

            Example::

                htmx_success_components = (
                    ("list", "product.list-item"),
                    ("detail", "product.detail-card"),
                )

            Client side::

                <form hx-post="..." hx-headers='{"X-Success-Component": "list"}'>

        htmx_form_component (str):
            Cotton component name (dot-notation) for the form-error partial.
            Defaults to ``"form"`` (the package's standard card layout).
            Override when a non-standard form layout is required.
        htmx_redirect_on_success (bool):
            When ``True``, returns ``HttpResponseClientRedirect`` on a valid
            htmx POST instead of rendering a success partial.

    Trigger attributes (``htmx_trigger``, ``htmx_trigger_after``) and
    ``_apply_htmx_triggers()`` are inherited from ``HtmxMixin``.
    """

    htmx_success_component = None
    htmx_success_components: tuple = ()  # allowlist of (alias, component) pairs
    htmx_form_component = "form"
    htmx_redirect_on_success = False

    # ------------------------------------------------------------------
    # Component getters
    # ------------------------------------------------------------------

    def get_htmx_success_component(self):
        """Return the Cotton component name for the success partial.

        Delegates to ``_resolve_component()`` (inherited from ``HtmxMixin``).
        Resolution order: client ``X-Success-Component`` header (allowlist
        lookup) → server default ``htmx_success_component``.

        Raises:
            ImproperlyConfigured: if no component can be resolved and
                ``htmx_redirect_on_success`` is also falsy.
        """
        component = self._resolve_component(
            "htmx_success_component", "htmx_success_components", "X-Success-Component"
        )
        if component:
            return component
        raise ImproperlyConfigured(
            "HtmxFormMixin requires 'htmx_success_component' or 'htmx_redirect_on_success = True'."
        )

    def get_htmx_form_component(self):
        """Return the Cotton component name for the form-error partial.

        Raises:
            ImproperlyConfigured: if ``htmx_form_component`` is falsy (only
                when it has been explicitly cleared from its default ``"form"``
                value).
        """
        if self.htmx_form_component:
            return self.htmx_form_component
        raise ImproperlyConfigured(
            "HtmxFormMixin requires 'htmx_form_component' to be set."
        )

    # ------------------------------------------------------------------
    # Form handling
    # ------------------------------------------------------------------

    def form_valid(self, form):
        """Handle a valid form submission.

        Non-htmx path: delegates entirely to ``super().form_valid(form)``.

        Htmx path:
            1. Calls ``super().form_valid(form)`` to save the object and queue
               any success message (the redirect response is discarded).
            2. Drains the Django message queue.
            3. If ``htmx_redirect_on_success`` is truthy, returns
               ``HttpResponseClientRedirect(success_url)``.
            4. Otherwise renders the success partial via ``render_component()``.
            5. Applies any ``HX-Trigger`` family headers before returning.
        """
        if not self.request.htmx:
            return super().form_valid(form)

        # Save the object and queue messages; discard the redirect response.
        super().form_valid(form)

        # Drain queued messages so they don't reappear on the next full-page load.
        list(get_messages(self.request))

        if self.htmx_redirect_on_success:
            response = HttpResponseClientRedirect(self.get_success_url())
        else:
            template = self.get_htmx_success_component()
            context = self.get_context_data(form=form)
            response = HttpResponse(render_component(self.request, template, context))

        return self._apply_htmx_triggers(response)

    def form_invalid(self, form):
        """Handle an invalid form submission.

        Non-htmx path: delegates entirely to ``super().form_invalid(form)``.

        Htmx path: renders the form-error partial at HTTP 200 via
        ``render_component()``.
        """
        if not self.request.htmx:
            return super().form_invalid(form)

        template = self.get_htmx_form_component()
        context = self.get_context_data(form=form)
        return HttpResponse(
            render_component(self.request, template, context), status=200
        )
