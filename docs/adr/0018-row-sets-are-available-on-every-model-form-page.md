# 0018 — Row sets are available on every model form page, not behind their own view classes

**Status:** accepted

**Date:** 2026-08-26

**Supersedes:** [ADR 0007 — A row set is declared as its own class, named after Django's admin
inlines](0007-a-row-set-is-declared-as-its-own-class.md), in the part that put `InlinesMixin` on
two separate view classes, `MVPInlineCreateView` and `MVPInlineUpdateView`. The declaration
surface 0007 established — `InlineFormSet`, its admin-derived attribute names, `factory_kwargs`/
`formset_kwargs`, `get_form_kwargs(index)`, `sort_forms()` — still holds and is unaffected by this
decision.

## Context

`InlinesMixin` composed with `MVPCreateView`/`MVPUpdateView` to produce two further classes,
`MVPInlineCreateView` and `MVPInlineUpdateView`, and a page that wanted row sets subclassed one of
those instead of the plain create or update view. Issue #313 asked the obvious question: given
that an empty `inlines` would make the mixin a no-op, why does adding rows to a page mean starting
from a different base class rather than setting an attribute on the view already in use?

It did not, historically, start from a question of ergonomics. `InlinesMixin` was not written as a
no-op when empty — `construct_inlines()` called `get_parent_model()` unconditionally, which falls
through to `self.get_queryset().model` when neither `model` nor `queryset` is configured, and
Django's own `get_queryset()` raises `ImproperlyConfigured` in exactly that case. A `form_class`-
only create view — a shape Django's own `ModelFormMixin` has always allowed — would have broken
the moment the mixin sat on it unconditionally. Putting it behind its own view classes sidestepped
that by construction: the mixin was never present unless a page had already committed to rows.

That reason is gone once the mixin is made a genuine no-op — the actual guarantee the issue names.
With it, there is no remaining case for two separate entrance points into what is otherwise the
same page.

## Decision

**`InlinesMixin` is mixed into `MVPCreateView` and `MVPUpdateView` by default**, first in each
class's bases, reproducing the MRO the removed classes gave it. Adding rows to a page is setting
`inlines` on the view already in use:

```python
class OrderLineInline(InlineFormSet):
    model = OrderLine
    fields = ["quantity"]


class ProductUpdateView(MVPUpdateView):
    model = Product
    fields = ["name", "category"]
    inlines = [OrderLineInline]  # the only line rows add to a view that already existed
```

**`MVPInlineCreateView` and `MVPInlineUpdateView` are removed outright**, with no deprecated
alias. The package is pre-1.0, and Article XVI of the constitution says import paths may change
between minor versions with a CHANGELOG entry; there is no consumer of these names outside this
repository.

**The no-op is a guarantee, not an assumption, enforced in `InlinesMixin` itself:**
`construct_inlines()` returns `[]` without resolving a parent model when no declarations are
listed; `form_valid()` and `form_invalid()` each defer to `super()` — the ordinary Django path —
when there are no formsets to validate or save. A view that declares no `inlines` behaves exactly
as it would if `InlinesMixin` were never mixed in, including the `form_class`-only shape that
motivated the two-class split in the first place.

**The dependency between the two modules inverts.** `mvp/views/edit.py` now imports
`InlinesMixin` from `mvp/views/inline.py`; `inline.py` no longer imports from `edit.py` at all.
`InlineFormSet` and `InlinesMixin` stay in `inline.py` rather than moving into `edit.py` — folding
a further ~1100 lines into an already-large module buys nothing, and it matches how `MVPFormBase`
already composes mixins from other view modules rather than absorbing them.

The two rows-only misconfiguration guards from ADR 0007's line of work — an empty `fields` on a
create page, and an empty `fields` with no `inlines` on an update page — still raise
`ImproperlyConfigured` at page-build time, now against every model form page rather than a
dedicated inline view class.

## Consequences

A project on the removed classes rewrites two lines: the base class, and `inlines` gains a home
on a view it may already have. No behaviour changes for a page that already declared `inlines` —
this is a naming and composition change, not a behavioural one, apart from the no-op guarantee
itself.

A `form_class`-only `MVPCreateView`, or an `MVPUpdateView` with no `inlines`, is now provably
unaffected by row-set machinery it never asked for — provable because it is tested, not merely
argued. That is the guarantee this decision trades the two-class split for.
