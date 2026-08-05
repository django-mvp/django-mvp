"""A parent record and its related rows on one page.

Source: mvp/views/inline.py
Contract: specs/024-formset-pages/contracts/inline-view.md
"""

from django.core.exceptions import ImproperlyConfigured
from django.forms import inlineformset_factory


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
            self._formset = self.get_formset_class()(**self.get_formset_kwargs())
        return self._formset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["formset"] = self.get_formset()
        return context
