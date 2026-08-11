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
the parent in a separately-named attribute.** This is also what `django.contrib.admin` does — an
`InlineModelAdmin`'s `model` is the related model from declaration to render, and the parent is
never written over it. The rebinding is upstream's alone, and its own documentation has to warn
about it.

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

## R4 — django-extra-views has no transaction and no collision detection. Both are ours.

`grep -rn "atomic\|transaction" extra_views/` returns nothing. `forms_valid` saves the parent then
loops the formsets, so a failure in the third inline leaves the parent and the first two committed
(`extra_views/advanced.py:53-57`).

Prefix collisions are equally unhandled: `construct_inlines` appends without inspecting the
resulting prefixes (`advanced.py:72-83`), and `NamedFormsetsMixin` names *context variables*, not
form prefixes, so it does not help. Two declarations over the same relation both parse the same
POST keys and share one management form, silently.

FR-009 and FR-005 are therefore things this package does that its prior art does not, and both
were named in the tracking issue before any research ran.

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

## R7 — The shorthand attributes are Django's names, not a divergence

**This entry replaces an earlier version that had the argument backwards**, and the correction
matters because the earlier version asked for a justification that was never needed.

The earlier text described `extra`, `max_num`, `can_delete` and `fk_name` as shorthands kept "in
deliberate divergence from django-extra-views", which removed them as class attributes in 0.11.0.
That framing takes django-extra-views as the baseline. It is not. Those are **Django's own names**,
in two places at once:

- they are parameters of `inlineformset_factory`;
- they are attributes of `django.contrib.admin`'s `InlineModelAdmin`. Read from the class in the
  project's environment, its class attributes are exactly:

```
['can_delete', 'classes', 'extra', 'fk_name', 'max_num', 'media',
 'min_num', 'model', 'show_change_link', 'template', 'verbose_name', 'verbose_name_plural']
```

So keeping them is alignment with the framework, and django-extra-views is the outlier for having
dropped them. Nothing here needs justifying against that package.

The same reading settles the class name. `InlineFormSetFactory` was borrowed wholesale, and
"Factory" was never accurate for it: the class *declares* a set, and something else manufactures
the formset from the declaration. `InlineFormSet` says what it is, and reads as the sibling of
admin's `TabularInline` and `StackedInline` that it functionally is.

Two more names follow admin rather than the borrowed surface: `form` and `formset`, not
`form_class` and `formset_class`. Those are both admin's attribute names and
`inlineformset_factory`'s parameter names, so they agree twice over.

`title` and `description` keep their own names rather than becoming admin's `verbose_name_plural`,
because ours is a rendered heading with help text beneath it and admin has no equivalent for the
second half. Borrowing the name for only half the concept would cost more than it saves.

**`title` defaults to the related model's `verbose_name_plural`** (Sam, plan gate). So the admin
name is where the default comes *from*, even though it is not what the attribute is called — which
is the right way round: a developer who sets nothing gets the same heading admin would give them,
and a developer who sets something is plainly overriding a heading rather than renaming a model.

## R8 — `fields = []` produces a valid form, and saving it is the risk

`ModelFormMixin.get_form_class` raises only when `fields is None`. With `fields = []`,
`modelform_factory(model, fields=[])` returns a `ModelForm` with no fields, which is always valid.

So the rows-only page (FR-014) needs no new form machinery — but `form.save()` on that empty form
still issues a full `UPDATE` of every column, which touches `auto_now` fields and fires
`pre_save`/`post_save` with `update_fields=None`. FR-015 forbids writing the record's field values
at all, and it forbids losing a concurrent change, which a full UPDATE does. See R12 for the
measurement.

**The parent form is never saved when the page carries no parent fields.** The formsets bind to the
loaded instance, which already has a pk. Where the parent's timestamp is to be updated, that is a
separate surgical write, not this form's save (FR-016, R12).

This is also why FR-017 exists: on create there is no loaded instance, so a page with no parent
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

## R12 — Touching the parent on a rows-only page, measured rather than assumed

FR-016 asks the rows-only page to record its change on the parent's own timestamp. The obvious
implementation — save the empty parent form — is the wrong one, and the difference is a data-loss
bug rather than a matter of taste. Three probes against the project's own database:

| What was done | Result |
|---|---|
| `parent.save(update_fields=["modified"])` on a model with `auto_now=True` | timestamp bumped |
| the same, after another writer changed a different field | the other writer's change survived |
| `parent.save()` — what `form.save()` on a field-less form does | **the other writer's change was lost** |

The third row is the whole argument. An empty `ModelForm` is always valid and its `save()` issues a
full `UPDATE` of every column from values read when the page was opened, so any change made in
between is silently overwritten. That risk is highest on exactly the pages this feature targets:
a long-lived editing page for a record other people also edit.

So the mechanism is a surgical touch of the model's `auto_now` fields, not a save of the parent
form. It produces the timestamp the developer wants and cannot lose a concurrent write.

**Default on**, for a reason that also bounds the blast radius: a model with no `auto_now` field
has nothing to touch, so the feature does nothing at all there. It acts only where the developer
has already declared, by putting such a field on the model, that they care when the record last
changed. Switching it off is a one-line opt-out on the view.

One consequence worth stating rather than discovering: a touch fires the model's save signals and
any lifecycle hooks attached to them. That is the point — it is how a parent-level "something
changed" is observed — but it is not a silent write.

## R13 — Django already has the per-form hook; the shared dictionary is what hides it

FR-021 asks for keyword arguments that differ per form. Django has carried the hook since 1.9:

```python
# django/forms/formsets.py
def get_form_kwargs(self, index):
    """
    Return additional keyword arguments for each individual formset form.

    index will be None if the form being constructed is a new empty form.
    """
    return self.form_kwargs.copy()
```

`_construct_form` calls it per form, so the index identifies which form is being built, and `None`
identifies the blank template form the browser clones to add a row.

django-extra-views declares `get_form_kwargs(self)` with no index and merges the result into
`formset_kwargs["form_kwargs"]`, which is a single dictionary shared by every form
(`extra_views/formsets.py:61-79`). That signature shadows Django's, so a project needing per-form
arguments has to reach around the surface it is using and subclass the formset directly — two
different APIs for one job, on the same page.

Our declaration takes **Django's signature**, index and all. It is one parameter, and it is the
difference between the requirement being reachable and not.

The related requirement, FR-022, is display order. Django's `can_order` is a different feature: it
adds an `ORDER` field to every form so the *user* can reorder rows, and exposes `ordered_forms`
after validation. What FR-022 asks for is the *developer* deciding the sequence forms appear in —
a set that renders in a fixed conceptual order rather than "rows already saved, then blanks". The
two were bundled together and dropped together in an earlier draft, which was a mistake: they are
unrelated options that happened to be adjacent in the same list. `can_order` stays unbuilt until
something asks for it; the display order is FR-022 and is built here.

Because it is display only, it must not touch validation or saving. Reordering the sequence a
formset validates or writes in would change which row is which, and the requirement says so
explicitly.
