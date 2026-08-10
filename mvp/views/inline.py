"""A parent record and its related rows on one page.

The prior art for this is django-extra-views (MIT, Andrew Ingram), which has
solved the parent-and-rows page through a class-based view for far longer than
this package has existed. The save flow is written here rather than inherited
from it, for the reasons set out in specs/024-formset-pages/research.md (R10).

Contract: specs/024-formset-pages/contracts/inline-view.md
"""

from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect

from .edit import MVPCreateView, MVPUpdateView


class InlineFormsetMixin:
    """Builds and validates an inline formset alongside a single-object form.

    Not exported from ``mvp.views`` - compose it with ``MVPCreateView`` or
    ``MVPUpdateView`` (see ``MVPInlineCreateView`` and ``MVPInlineUpdateView``)
    rather than using it directly, matching the rule already stated in
    ``mvp/views/__init__.py``: the package exports views, not mixins.
    """

    inline_model = None
    inline_form_class = None
    inline_fields = None
    inline_extra = 1
    inline_can_delete = True
    inline_max_num = None

    inline_title = None
    """Heading above the set. Defaults to the related model in plural."""

    inline_description = None
    """Help text under the heading. No default; omitted when unset."""

    def get_formset_factory_kwargs(self):
        """Return the kwargs ``inlineformset_factory`` builds the class from.

        Derived from the six ``inline_*`` attributes. Super-and-extend, like
        Django's own ``get_form_kwargs``: to add ``min_num``, ``validate_min``,
        a custom base formset class, or ``fk_name``, override this method,
        call ``super().get_formset_factory_kwargs()`` and mutate the result.

        ``validate_max`` is set to ``True`` whenever ``inline_max_num`` is
        set, because ``inlineformset_factory`` defaults ``validate_max=False``
        and ``max_num`` alone rejects nothing. ``absolute_max`` is left at
        Django's default and must never be derived from the cap - see the
        contract for why deriving it silently discards submitted rows.
        """
        if self.inline_model is None:
            raise ImproperlyConfigured(
                f"'{self.__class__.__name__}' must set 'inline_model'."
            )
        kwargs = {
            "fields": self.inline_fields,
            "extra": self.inline_extra,
            "can_delete": self.inline_can_delete,
        }
        if self.inline_form_class is not None:
            kwargs["form"] = self.inline_form_class
        if self.inline_max_num is not None:
            kwargs["max_num"] = self.inline_max_num
            kwargs["validate_max"] = True
        return kwargs

    def get_formset_class(self):
        """Build the formset class from ``get_formset_factory_kwargs()``."""
        return inlineformset_factory(
            self.model, self.inline_model, **self.get_formset_factory_kwargs()
        )

    def get_formset_kwargs(self):
        """Return instance-level kwargs: ``instance``, and ``data``/``files``
        on a POST."""
        kwargs = {"instance": self.object}
        if self.request.method in ("POST", "PUT"):
            kwargs["data"] = self.request.POST
            kwargs["files"] = self.request.FILES
        return kwargs

    def get_formset(self):
        """Return the formset, built once per request and reused.

        The memoisation is not an optimisation: ``form_invalid`` re-renders
        through ``get_context_data``, and a second construction there would
        discard the bound formset carrying the user's submitted values and
        its errors, and the page would come back blank.
        """
        if not hasattr(self, "_formset"):
            formset = self.get_formset_class()(**self.get_formset_kwargs())
            # Carried on the formset rather than passed through the context,
            # so that a template rendering <c-form.formset> needs no second
            # variable and an override can set them per request.
            formset.title = self.get_inline_title()
            formset.description = self.get_inline_description()
            self._formset = formset
        return self._formset

    def get_inline_title(self):
        """Return the heading for the set, or None to take the default."""
        return self.inline_title

    def get_inline_description(self):
        """Return the help text under the heading, or None for none."""
        return self.inline_description

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["formset"] = self.get_formset()
        return context

    def form_valid(self, form):
        """Validate the formset, then save both atomically.

        Delegates to ``form_invalid`` when the formset fails validation.
        Otherwise, in one ``transaction.atomic()`` block, saves the parent,
        assigns it to ``formset.instance`` and saves the formset - in that
        order, because ``BaseInlineFormSet.save_new`` reads
        ``formset.instance`` at save time. The success URL, the message and
        the redirect are all produced after the block exits, and never by
        calling ``super().form_valid()``: that reaches ``SuccessMessageMixin``,
        which delegates to ``ModelFormMixin.form_valid``, which would save the
        parent a second time outside the transaction. The URL is resolved
        after the saves so that, on the create path, ``get_success_url()``
        sees the saved object rather than ``self.object is None``.

        Reaching this method means ``form.is_valid()`` has already run and,
        with it, ``BaseModelForm._post_clean()``, which writes the submitted
        values onto ``form.instance`` - the same object as ``self.object`` on
        an update view, because ``ModelFormMixin.get_form_kwargs`` passes it
        in as ``instance``. When the formset then fails, re-reading
        ``self.object`` before delegating to ``form_invalid`` undoes that
        mutation, so object-derived page parts (breadcrumbs, page title)
        render the stored record rather than the refused submission (#193).
        On create, ``self.object`` has no pk yet and is left alone.
        """
        formset = self.get_formset()
        if not formset.is_valid():
            if self.object is not None and self.object.pk is not None:
                self.object = self.get_object()
            return self.form_invalid(form)

        with transaction.atomic():
            self.object = form.save()
            formset.instance = self.object
            formset.save()

        success_url = self.get_success_url()
        messages.success(self.request, self.get_success_message(form.cleaned_data))
        return HttpResponseRedirect(success_url)


class MVPInlineCreateView(InlineFormsetMixin, MVPCreateView):
    """A create page carrying one record and one set of rows belonging to it.

    On create, the formset is built against an unsaved parent instance,
    which is what ``BaseInlineFormSet`` does when given no instance.
    """


class MVPInlineUpdateView(InlineFormsetMixin, MVPUpdateView):
    """An update page carrying one record and one set of rows belonging to it."""
