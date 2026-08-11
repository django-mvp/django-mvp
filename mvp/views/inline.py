"""A parent record and one or more sets of related rows on one page.

The prior art for this is django-extra-views (MIT, Andrew Ingram), which has
solved the parent-and-rows page through a class-based view for far longer than
this package has existed. The save flow is written here rather than inherited
from it, for the reasons set out in specs/024-formset-pages/research.md (R10).

The declaration surface is named after django.contrib.admin's inlines and
inlineformset_factory's parameters (specs/025-multiple-related-sets/research.md
R7) rather than reproducing django-extra-views' surface.

Spec: specs/025-multiple-related-sets/spec.md
"""

from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.forms import inlineformset_factory
from django.forms.formsets import all_valid
from django.http import HttpResponseRedirect

from .edit import MVPCreateView, MVPUpdateView


class InlineFormSet:
    """Declares one set of related rows: the related model and how its
    formset is built, instance and displayed.

    One declaration class per related model, listed on a view's ``inlines``.
    ``model`` keeps meaning the related model for its whole life — never
    rebound to the parent — the parent is held separately on ``parent_model``
    (research R2).

    Attributes fall into two groups, per Django's own two-phase construction
    (``get_factory_kwargs()`` / ``get_formset_kwargs()``): ``fields``,
    ``exclude``, ``form``, ``formset``, ``extra``, ``min_num``, ``max_num``,
    ``can_delete`` and ``fk_name`` shape the generated formset *class*;
    ``prefix`` and ``initial`` shape the formset *instance*. ``factory_kwargs``
    and ``formset_kwargs`` reach anything the shorthands do not expose, and
    ``factory_kwargs`` wins over its shorthand on any key both set.
    """

    model = None
    """The related model this set edits. Never rebound to the parent."""

    fields = None
    exclude = None
    """Fields to omit from the generated form.

    On a related model that reaches the parent by more than one relation,
    ``BaseInlineFormSet.add_fields`` replaces only *this set's own* foreign
    key with the parent-bound field — any other foreign key the field
    selection admits (via ``exclude`` rather than an explicit ``fields``)
    stays a plain chooser over every parent record, not just this one. Name
    ``fields`` explicitly on that shape rather than relying on ``exclude``.
    """
    form = None
    formset = None
    extra = None
    min_num = None
    max_num = None
    can_delete = None
    fk_name = None

    prefix = None
    initial = None

    factory_kwargs = None
    formset_kwargs = None
    form_kwargs = None

    title = None
    """Heading above the set. Defaults to the related model's
    ``verbose_name_plural`` — the heading django.contrib.admin would give."""

    description = None
    """Help text under the heading. No default; omitted when unset."""

    def __init__(self, parent_model, request, instance, view):
        if self.model is None:
            raise ImproperlyConfigured(
                f"'{self.__class__.__name__}' must set 'model'."
            )
        self.parent_model = parent_model
        self.request = request
        self.instance = instance
        self.view = view

    def get_factory_kwargs(self):
        """Return the kwargs ``inlineformset_factory`` builds the class from.

        Folds the shorthand attributes in; an explicit ``factory_kwargs`` key
        wins over its shorthand. ``validate_max``/``validate_min`` are set
        exactly when ``max_num``/``min_num`` are, because
        ``inlineformset_factory`` defaults both to ``False`` and a bound
        alone rejects nothing. ``absolute_max`` is never derived from
        ``max_num`` — Django reads the raw submitted ``TOTAL_FORMS`` before
        subtracting deleted rows, so deriving it would silently truncate a
        submission that is legitimately within the cap.

        Super-and-extend, like Django's own ``get_form_kwargs``: to reach a
        formset-class parameter this method does not expose as an attribute,
        override this method, call ``super().get_factory_kwargs()`` and
        mutate the result.
        """
        kwargs = {}
        for name in ("fields", "exclude", "form", "formset", "extra", "can_delete", "fk_name"):
            value = getattr(self, name)
            if value is not None:
                kwargs[name] = value
        if self.min_num is not None:
            kwargs["min_num"] = self.min_num
            kwargs["validate_min"] = True
        if self.max_num is not None:
            kwargs["max_num"] = self.max_num
            kwargs["validate_max"] = True
        if self.factory_kwargs:
            kwargs.update(self.factory_kwargs)
        return kwargs

    def get_formset_class(self):
        """Build the formset class from ``get_factory_kwargs()``."""
        return inlineformset_factory(
            self.parent_model, self.model, **self.get_factory_kwargs()
        )

    def get_formset_kwargs(self):
        """Return instance-level kwargs: ``instance``, and ``data``/``files``
        on a POST.

        Both ``formset_kwargs`` and its nested ``form_kwargs`` are copied at
        both levels, so mutating the returned dict never mutates the
        declaration's own class-level attributes across requests (research
        R6). ``prefix`` is put in only when the declaration sets one, so
        Django's per-relation default applies when it does not (research R3)
        — load-bearing beyond configuration: the prefix-collision error
        (FR-005) tells the developer to set a prefix, so an unwired override
        would make the error's own suggested fix do nothing.
        """
        kwargs = dict(self.formset_kwargs) if self.formset_kwargs else {}
        kwargs["form_kwargs"] = dict(self.form_kwargs) if self.form_kwargs else {}
        kwargs["instance"] = self.instance
        if self.initial is not None:
            kwargs["initial"] = self.initial
        if self.prefix:
            kwargs["prefix"] = self.prefix
        if self.request.method in ("POST", "PUT"):
            kwargs["data"] = self.request.POST
            kwargs["files"] = self.request.FILES
        return kwargs

    def get_title(self):
        """Return the heading for the set, defaulting to the related model's
        ``verbose_name_plural``."""
        if self.title:
            return self.title
        return self.model._meta.verbose_name_plural

    def get_description(self):
        """Return the help text under the heading, or ``None`` for none."""
        return self.description

    def get_form_kwargs(self, index):
        """Return additional keyword arguments for the form at ``index``.

        Django's own signature (index and all — research R13): ``index`` is
        ``None`` for the blank template form the browser clones. Defaults to
        the shared ``form_kwargs`` attribute, mirroring
        ``BaseFormSet.get_form_kwargs``. Override to give forms different
        arguments according to their position.
        """
        return dict(self.form_kwargs) if self.form_kwargs else {}

    def sort_forms(self, forms):
        """Return the sequence forms are displayed in. Defaults to the order
        given.

        Display only — must never reach the order rows are validated or
        saved in, since reordering that would change which submitted row
        maps to which record.
        """
        return forms

    def construct_formset(self):
        """Build the formset, wiring this declaration's ``get_form_kwargs``
        and ``sort_forms`` through so Django's own per-form hook and the
        page's rendering reach them, and attaching ``title``/``description``
        so a template rendering the formset needs no second variable."""
        formset_class = self.get_formset_class()
        formset = formset_class(**self.get_formset_kwargs())
        formset.get_form_kwargs = self.get_form_kwargs
        formset.sort_forms = self.sort_forms
        formset.title = self.get_title()
        formset.description = self.get_description()
        return formset


class InlinesMixin:
    """Builds and validates one or more ``InlineFormSet`` declarations
    alongside a single-object form.

    Not exported from ``mvp.views`` - compose it with ``MVPCreateView`` or
    ``MVPUpdateView`` (see ``MVPInlineCreateView`` and ``MVPInlineUpdateView``)
    rather than using it directly, matching the rule already stated in
    ``mvp/views/__init__.py``: the package exports views, not mixins.
    """

    inlines = []

    def get_inlines(self):
        """Return the declaration classes to build, in the order given."""
        return list(self.inlines)

    def get_parent_model(self):
        """Return the parent model, matching how Django's own model-form
        pages resolve it (``ModelFormMixin.get_form_class``): ``self.model``
        first, then the loaded object's class, then the queryset's model."""
        if self.model is not None:
            return self.model
        obj = getattr(self, "object", None)
        if obj is not None:
            return obj.__class__
        return self.get_queryset().model

    def construct_inlines(self):
        """Return one formset per declaration, built once per request and
        reused.

        The memoisation is not an optimisation: on an invalid submission,
        ``form_invalid`` re-renders through ``get_context_data``, and a
        second construction there would discard the bound formsets carrying
        the user's submitted values and their errors.
        """
        if not hasattr(self, "_inline_formsets"):
            parent_model = self.get_parent_model()
            self._inline_formsets = [
                declaration_cls(
                    parent_model, self.request, self.object, self
                ).construct_formset()
                for declaration_cls in self.get_inlines()
            ]
        return self._inline_formsets

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        formsets = self.construct_inlines()
        for formset in formsets:
            formset.forms = formset.sort_forms(list(formset.forms))
        context["inlines"] = formsets
        return context

    def form_valid(self, form):
        """Validate every set with Django's ``all_valid``, then save the
        parent and every set inside one ``transaction.atomic()``.

        ``all_valid`` is used rather than a hand-rolled loop specifically
        because its list comprehension defeats ``all()``'s short-circuit, so
        every set is validated even after an earlier one has failed
        (research R5). The success URL, the message and the redirect are all
        produced after the block exits, and never by calling
        ``super().form_valid()``: that would save the parent a second time
        outside the transaction.
        """
        formsets = self.construct_inlines()
        if not all_valid(formsets):
            return self.form_invalid(form)

        with transaction.atomic():
            self.object = form.save()
            for formset in formsets:
                formset.instance = self.object
                formset.save()

        success_url = self.get_success_url()
        messages.success(self.request, self.get_success_message(form.cleaned_data))
        return HttpResponseRedirect(success_url)


class MVPInlineCreateView(InlinesMixin, MVPCreateView):
    """A create page carrying one record and its declared row sets.

    On create, each set's formset is built against an unsaved parent
    instance, which is what ``BaseInlineFormSet`` does when given no
    instance.
    """


class MVPInlineUpdateView(InlinesMixin, MVPUpdateView):
    """An update page carrying one record and its declared row sets."""
