# FS-025 — research

Findings that shaped the plan. Each is evidence, read from source rather than recalled.

## R1 — django-extra-views' configuration surface, read from upstream

Read at commit `d37136d` (master, 2025-04-26), `__version__ = "0.16.0"`, MIT.

`InlineFormSetFactory` declares no attributes of its own. They come from two bases:

```python
# extra_views/formsets.py:22-28  (BaseFormSetFactory)
initial = []
form_class = None
formset_class = None
prefix = None
formset_kwargs = {}
factory_kwargs = {}
form_kwargs = {}

# extra_views/formsets.py:181-184  (BaseInlineFormSetFactory)
model = None
inline_model = None
exclude = None
fields = None
```

The whole declarative surface is `model`, `inline_model`, `fields`, `exclude`, `form_class`,
`formset_class`, `prefix`, `initial`, `factory_kwargs`, `formset_kwargs`, `form_kwargs`.

**There is no `extra`, `max_num`, `min_num`, `can_delete`, `can_order` or `fk_name`.** Those were
removed as class attributes in 0.11.0 and must be written into `factory_kwargs`.

The split itself is Django's two-phase construction, and it is exact:

- `factory_kwargs` → `inlineformset_factory(parent, child, **kwargs)` — shapes the class.
- `formset_kwargs` → `FormSetClass(**kwargs)` — shapes the instance.

## R2 — The naming inversion in `__init__`, and why it is not copied

```python
# extra_views/advanced.py:19-25
def __init__(self, parent_model, request, instance, view_kwargs=None, view=None):
    self.inline_model = self.model
    self.model = parent_model
```

A developer writes `model = OrderLine` meaning the *related* model, and at construction the
attribute is overwritten with the *parent* model. Every method downstream then reads `self.model`
as the parent. The upstream docs have to warn about this explicitly.

**Decision: keep the declaration's `model` meaning the related model for its whole life, and hold
the parent in a separately-named attribute.** The declared spelling — `model = OrderLine` — is
identical, so a developer arriving from django-extra-views writes the same class. What differs is
that the attribute does not silently change meaning after construction, which is a trap for anyone
overriding a method rather than merely declaring one. FR-002 asks for the split and the names, not
for a rebinding that upstream itself documents as a surprise.

## R3 — The default prefix comes from Django, not from django-extra-views

`get_prefix()` upstream returns `self.prefix` verbatim, defaulting to `None`
(`extra_views/formsets.py:43-47`). There is no `get_default_prefix()` anywhere in the package. When
the prefix is `None` it falls through to Django:

```python
# django/forms/formsets.py:93
self.prefix = prefix or self.get_default_prefix()

# django/forms/models.py:1149-1150  (BaseInlineFormSet)
@classmethod
def get_default_prefix(cls):
    return cls.fk.remote_field.get_accessor_name(model=cls.model).replace("+", "")
```

Verified against the project's own environment rather than the docs.

Two consequences the spec depends on. The prefix is derived from **the relation**, so two sets on
the same related model through different foreign keys already differ with nothing declared
(FR-004, US2 scenario 6). And because `prefix or ...` is a truthiness test, an empty string falls
through to the default rather than producing an unprefixed set.

## R4 — Upstream has no transaction and no collision detection. Both are ours.

`grep -rn "atomic\|transaction" extra_views/` returns nothing. `forms_valid` saves the parent then
loops the formsets, so a failure in the third inline leaves the parent and the first two committed
(`extra_views/advanced.py:53-57`).

Prefix collisions are equally unhandled: `construct_inlines` appends without inspecting the
resulting prefixes (`advanced.py:72-83`), and `NamedFormsetsMixin` names *context variables*, not
form prefixes, so it does not help. Two declarations over the same relation both parse the same
POST keys and share one management form, silently.

FR-009 and FR-005 are therefore deliberate divergences, not omissions being filled in. They are
the two places this package does more than the surface it borrows, and both were named in the
tracking issue before any research ran.

## R5 — `all_valid` is the mechanism FR-008 needs, and short-circuiting is the trap

```python
# django/forms/formsets.py:581-584
def all_valid(formsets):
    """Validate every formset and return True if all are valid."""
    # List comprehension ensures is_valid() is called for all formsets.
    return all([formset.is_valid() for formset in formsets])
```

The comment is the point: the list comprehension exists to defeat `all()`'s short-circuit, so
every formset accumulates its errors for re-rendering. Upstream also places `all_valid(inlines)` as
the **left** operand of `and` (`advanced.py:116`), so the inlines are validated even when the
parent form has already failed. Reversing those operands would suppress every inline error on the
page reporting the failure.

Use Django's helper rather than reimplementing it, and preserve the operand order.

## R6 — A defect upstream that must not be copied

```python
# extra_views/formsets.py:77-79
kwargs = self.formset_kwargs.copy()
kwargs.setdefault("form_kwargs", {}).update(self.get_form_kwargs())
```

`.copy()` is shallow. When a subclass declares `formset_kwargs = {"form_kwargs": {...}}` at class
level, `setdefault` returns that same nested dict and `.update()` mutates class-level state in
place, accumulating across every request the process serves. Only the outer dict is protected.

Copy both levels.

## R7 — The shorthand attributes are a deliberate divergence

Upstream removed `extra`, `max_num`, `can_delete` and `fk_name` as attributes in 0.11.0. This
package keeps them as named shorthands *alongside* `factory_kwargs`, which then wins on conflict.

Two independent sources agree on this. The tracking issue's own worked example and the sketch on
`024-multi-inline-wip` both declare shorthand attributes, and the specification names them in
FR-001 and in the Key Entities. It is also what the six removed `inline_*` attributes provided, so
dropping them would make the common case wordier than the surface being replaced:

```python
# shorthand kept                          # what upstream requires instead
class OrderLineInline(InlineFormSetFactory):   class OrderLineInline(InlineFormSetFactory):
    model = OrderLine                              model = OrderLine
    fields = ["quantity"]                          fields = ["quantity"]
    extra = 3                                      factory_kwargs = {"extra": 3}
```

The cost of the divergence is that a reader who knows upstream 0.16 finds attributes upstream does
not have. That is a smaller surprise than the reverse, because the shorthands are additive: a
declaration written to upstream's surface still works here unchanged.

Flagged at the plan gate rather than settled quietly, because "follows django-extra-views' surface"
is the tracking issue's phrase and this is the one place the plan does not follow it exactly.

## R8 — `fields = []` produces a valid form, and saving it is the risk

`ModelFormMixin.get_form_class` raises only when `fields is None`. With `fields = []`,
`modelform_factory(model, fields=[])` returns a `ModelForm` with no fields, which is always valid.

So the rows-only page (FR-014) needs no new form machinery — but `form.save()` on that empty form
still issues a full `UPDATE` of every column, which touches `auto_now` fields and fires
`pre_save`/`post_save` with `update_fields=None`. FR-015 asks for the record's stored values to be
unchanged, and a no-op UPDATE is not the same thing as no write.

**The parent is not saved at all when the page carries no parent fields.** The formsets bind to the
loaded instance, which already has a pk.

This is also why FR-016 exists: on create there is no loaded instance, so a page with no parent
fields would have to save an empty parent to obtain a pk for the rows to hang off, which is exactly
the record nobody asked to create.

## R9 — The current view's decisions that carry forward unchanged

Three were settled under FS-024 by design review and are not reopened. Each is load-bearing here
because the multi-set flow has the same shapes:

- **`validate_max=True` whenever a cap is set, and `absolute_max` left at Django's default.**
  `inlineformset_factory` defaults `validate_max=False`, so a cap alone rejects nothing. Bounding
  `absolute_max` to the cap looks like defence in depth and is not: Django reads the raw submitted
  `TOTAL_FORMS` before subtracting deleted rows, and drops every row past the bound *before*
  validation, so a submission legitimately within the cap is silently truncated (FS-024 D25).
- **`super().form_valid()` is never called.** It reaches `SuccessMessageMixin` → `
  ModelFormMixin.form_valid`, which saves the parent a second time outside the transaction
  (FS-024 D26).
- **The success URL is resolved after the transaction commits, not before.** Resolving it above the
  block breaks the create path, where `self.object` has no pk yet (FS-024 D28).

## R10 — Why the view logic is written here rather than inherited

Recorded under FS-024 as R10 and not reopened. Restated in one line because this feature adopts
the upstream *surface* while still not depending on the package: the save flow this package needs
is transactional, and the two behaviours it must add — the transaction and the collision check —
are precisely the two upstream does not have (R4).

## R11 — What the sketch on `024-multi-inline-wip` is worth

It is one commit, tests and demo still on the old attribute names, and Sam described it as a
sketch of the shape rather than a candidate for merge. Under D7 it is not a behavioural oracle
either.

Read for shape, it agrees with this plan on the declaration surface, the prefix collision check,
the `all([...])` validation and the transaction. Two things in it are wrong and the plan does not
carry them:

- Formsets are validated only on the path where the parent form is valid. When the parent form
  fails, Django's `ProcessFormView.post` calls `form_invalid` directly, so nothing calls
  `is_valid()` on the sets and their errors reach the page only by lazy evaluation during
  rendering. US3 scenario 2 requires the parent's errors and every set's errors together, so the
  sets are validated explicitly on both paths.
- It has no rows-only page, which is US4.

The plan is written against the specification. Where the sketch happens to agree, that is
corroboration, not authority.
