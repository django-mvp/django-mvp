# Phase 0 Research: Formset Pages

**Feature**: `024-formset-pages` | **Date**: 2026-08-05

Every unknown the Technical Context raised, resolved against the installed source of the
libraries involved rather than against documentation. File references are to the versions
resolved in this repository's lock file: Django 5.2, django-crispy-forms 2.7,
crispy-tailwind 1.0.3.

---

## R1 — How a formset renders through the packaged form path

**Decision**: The packaged formset component renders the set's structure itself and delegates
only the individual fields to crispy, field by field, through `|as_crispy_field`. It does not
use crispy's `|crispy` filter on the formset.

**Rationale**: `|crispy` does accept a formset — `as_crispy_form` checks
`isinstance(form, BaseFormSet)` and switches to `<pack>/uni_formset.html`. For the `tailwind`
pack that template is four lines:

```django
{% with formset.management_form as form %}{% include 'tailwind/uni_form.html' %}{% endwith %}
{% for form in formset %}<div class="multiField">{% include 'tailwind/uni_form.html' %}</div>{% endfor %}
```

It has two properties that make it unusable here:

1. **It never renders `formset.non_form_errors`.** FR-017 requires set-level errors above the
   set, and the only crispy template that renders them is `errors_formset.html`, reachable
   only through the separate `|as_crispy_errors` filter. Rendering through `|crispy` alone
   would silently drop every set-level error — the exact failure FR-018 forbids.
2. **Its sibling error templates are not DaisyUI.** `errors_formset.html` and `errors.html`
   emit `bg-red-500`, `text-red-700`, `border-red-400` — raw utility colours from crispy's own
   Tailwind styling, not the DaisyUI semantic classes the package uses everywhere else.
   Article XI forbids raw utility classes in templates demonstrating a component, and the
   result would not match the packaged look FR-004 requires.

Delegating per field keeps SC-008 exactly true. `as_crispy_field` renders through
`tailwind/field.html`, which is the same template `uni_form.html` includes for every field of a
single form. A row's fields therefore go through a byte-identical path to a single form's
fields, including this repository's own `tailwind/layout/help_text.html` override and the
per-field error block in `tailwind/layout/help_text_and_errors.html`. That block is what
satisfies FR-016 with no work: a row's field error already renders adjacent to its field.

**Alternatives considered**:

- *Override `tailwind/uni_formset.html` in `mvp/templates/`, as this repo already does for
  `tailwind/layout/help_text.html`.* Rejected: the override would have to reintroduce the
  errors, the add and remove controls, the empty-form template and the Alpine root, at which
  point it is a component wearing a vendored template's path — invisible to
  `tests/test_components/test_render_all.py`, not overridable by a consumer at a
  `cotton/` path, and in breach of Article XI's rule that reusable markup is a Cotton
  component.
- *Render rows with the packaged `<c-form.field>` component.* Rejected: `<c-form.field>` is
  the manual DaisyUI-native path and produces different markup from the crispy path a single
  form takes. Using it would make a formset row visibly different from a single form's field
  and break SC-008.

---

## R2 — What removing a row means

**Decision**: Every row, saved or unsaved, is removed the same way — Django's `DELETE` flag is
set and the row is hidden. Nothing is re-indexed and `TOTAL_FORMS` is never decremented.

**Rationale**: Django already distinguishes the two cases, so the page does not have to.
`BaseModelFormSet.save_new_objects` (`django/forms/models.py:950`) reads:

```python
for form in self.extra_forms:
    if not form.has_changed():
        continue
    # If someone has marked an add form for deletion, don't save the object.
    if self.can_delete and self._should_delete_form(form):
        continue
```

An unsaved row marked for deletion is therefore never created, satisfying FR-022, and a saved
row marked for deletion is deleted by `save_existing_objects` on submission, satisfying FR-023.
`can_delete_extra` defaults to `True` (`django/forms/formsets.py:545`), so extra forms carry a
`DELETE` field and the uniform treatment is available without configuration.

Not decrementing `TOTAL_FORMS` is the load-bearing half. Django reads submitted forms by index
from `0` to `TOTAL_FORMS - 1`, so removing a row from the middle of the page and decrementing
the count silently shifts every later row onto the wrong index. Hiding rather than deleting the
markup keeps the indices contiguous and keeps the submitted values intact, which is also what
makes the re-render edge case work: an invalid submission comes back with the removal still
applied, because the `DELETE` value was submitted like any other field.

**Alternatives considered**: removing unsaved rows from the DOM and re-indexing the survivors.
Rejected — it is the standard source of off-by-one bugs in hand-written formset pages, it
requires rewriting every `name`, `id` and `for` attribute in the remaining rows, and it buys
nothing that the `DELETE` flag does not already give.

---

## R3 — Adding a row without a reload

**Decision**: The component renders `formset.empty_form` once into an inert
`<template x-ref>` element. Adding a row clones that markup, replaces every `__prefix__`
occurrence with the current `TOTAL_FORMS` value, appends it, and increments `TOTAL_FORMS`.

**Rationale**: This is what `empty_form` exists for. It is a real, unbound form whose prefix is
the literal `__prefix__`, so its field names, ids and label `for` attributes are all
substitutable in one pass. Holding it in a `<template>` keeps it out of the submitted document
and out of Alpine's reach until it is cloned. The Alpine 3 runtime and its plugins are already
loaded by the packaged base template (`mvp/templates/mvp/base.html:34-39`), so FR-025 is met
with no build tooling and no new client-side dependency.

The row cap in FR-026 reads from `formset.max_num`, which `formset_factory` always sets
(defaulting to `DEFAULT_MAX_NUM`), so the add control has a number to compare against in every
configuration.

Two details, both added after the design review:

- **The state is two counters, not one.** `total` is monotonic and seeds both `__prefix__` and
  `TOTAL_FORMS`; `visible` counts rows not marked for removal and is what the add control compares
  against the cap. With a single counter, removing a row on a capped set would permanently forfeit
  its slot, which is neither what the user expects nor what Django accepts — `full_clean` tests
  `total_form_count() - len(deleted_forms) > max_num`.
- **`total` is seeded from `formset.total_form_count`, never from the DOM.** The management form's
  `TOTAL_FORMS` input is a string the server re-emits verbatim after an invalid submission. Reading
  it back and substituting it into cloned markup would put a user-supplied string into the `name`
  and `id` attributes of a new row. Seeding from the template variable takes an integer Django has
  already clamped to `absolute_max`.

**Alternatives considered**: fetching a fresh blank row from the server. Rejected outright by
FR-024, which forbids any row change reaching the server before submission.

---

## R4 — Atomicity

**Decision**: The parent save and the formset save happen inside a single
`transaction.atomic()` block in the view's `form_valid`.

**Rationale**: FR-011 states atomicity as a requirement on the feature, not an assumption about
the database. Django gives no implicit transaction around a view unless `ATOMIC_REQUESTS` is
set, which is a project-level setting the package cannot rely on. Wrapping the two saves is the
whole of the mechanism: if saving a row raises, the parent's `INSERT` or `UPDATE` is rolled
back with it and nothing is persisted.

Ordering matters and follows Django's documented inline pattern: save the parent first, assign
it to `formset.instance`, then save the formset. `BaseInlineFormSet.save_new` reads
`self.instance` at save time to set the foreign key, so assigning the freshly-created parent
after the fact is sufficient and satisfies FR-014 for the create case.

**What must stay outside the block**: the success message and the redirect. The parent save runs
through `super().form_valid()`, which reaches `SuccessMessageMixin` and calls `messages.success`.
Django's message storage is not transactional, so a flash queued inside the block outlives the
rollback — a request that persisted nothing would still tell the user the record was saved. The
transaction wraps the two saves and nothing else.

---

## R9 — `max_num` is not a cap unless `validate_max` is set

**Decision**: `get_formset_factory_kwargs()` sets `validate_max=True` and a bounded
`absolute_max` whenever `inline_max_num` is configured.

**Rationale**: `inlineformset_factory` defaults `validate_max=False`, and `BaseFormSet.full_clean`
raises `too_many_forms` only when `self.validate_max` is set, or when the submitted `TOTAL_FORMS`
exceeds `absolute_max` — which defaults to `max_num + DEFAULT_MAX_NUM`, that is `max_num + 1000`
(`django/forms/formsets.py:552-557`). Passing `max_num` alone therefore rejects nothing: a view
configured for three rows accepts and saves a submission carrying a thousand.

That would have made FR-026 a browser-side suggestion and left the spec's own edge case false —
it says the add control stops "rather than adding a row the submission will reject", which
assumes a rejection the design had not arranged. For a published package the distinction is not
academic: the consumer sets `inline_max_num` and reasonably believes it binds.

`absolute_max` matters independently of `validate_max`, and this is the part that is easy to
miss. `full_clean` constructs and validates **every** submitted form before it reaches the
too-many-forms check, so with the default a single request can still force a thousand form
constructions and a thousand primary-key lookups while holding a write transaction open. Bounding
`absolute_max` to the configured cap plus the extras is what bounds the work.

**Alternatives considered**: leaving enforcement to the consumer through
`get_formset_factory_kwargs()`. Rejected — a property that only holds when the consumer
independently discovers an override hook is a design defect in a package, not a documentation gap.

---

## R5 — Declaring the crispy dependencies

**Decision**: `django-crispy-forms` and `crispy-tailwind` move from the dev group to
`[project].dependencies`, and both are added to deptry's `DEP002` ignore list. The consumer
setup documentation gains the two `INSTALLED_APPS` entries and the two `CRISPY_*` settings.

**Rationale**: `mvp/templates/cotton/form/render.html:1-2` unconditionally loads
`crispy_forms_tags` and `tailwind_filters`. The packaged form rendering has always required
both distributions at render time while the metadata declared them dev-only, which is the
defect US1 exists to close. Article VII asks for a stated justification for a runtime
dependency, and the justification is that the dependency already existed in the code.

`DEP002` (declared but not imported) fires because neither package is imported from Python in
`mvp/` — they are reached through `{% load %}` and `INSTALLED_APPS`. That is the same shape as
`django-flex-menus` and `django-easy-icons`, which are already listed there
(`pyproject.toml:100`), so the ignore entry follows established precedent rather than
suppressing a real finding.

The documentation half is not optional. Django resolves template tag libraries only from apps
in `INSTALLED_APPS`, so installing the distributions is necessary but not sufficient —
`{% load crispy_forms_tags %}` still raises `TemplateSyntaxError` without the app entries.
`docs/integrations.md` currently presents crispy as an optional add-on; that section moves to
the required setup in `README.md` and `docs/getting-started.md`.

**Alternatives considered**: a Django system check that reports the missing apps at startup
instead of a template error at render time. Declined — no requirement asks for it, and a check
is a public surface of its own needing an id, documentation and a CHANGELOG entry. Recorded in
`decisions.md` rather than built.

---

## R6 — Where the formset renders on the page

**Decision**: `mvp/templates/form_view.html` gains a `{% block formset %}` inside the `<c-form>`
body, above the actions block, whose default content renders `<c-form.formset>` when a
`formset` is present in the context. No new page template is added, and no new view is needed
for the standalone case.

**Rationale**: This is the smallest change that satisfies FR-006 and US2 scenario 4 together.
Any packaged form view that puts a `formset` in its context — including the existing
`MVPFormView` with a standalone formset — renders it, in the right place, with no further
configuration. The configured view of US3 then needs no template of its own: it inherits
`form_view.html` unchanged and only has to supply the context entry.

The block sits inside the `<c-form>` slot, which is where the existing `{% block actions %}`
already lives, so the pattern is the one the template already uses.

One consequence: `<c-form>` decides the form's `enctype` from `form_obj.is_multipart` alone, so
a file field on a row would submit without the multipart encoding. `<c-form>` therefore gains a
`formset` attribute consulted in the same condition. `BaseFormSet.is_multipart` interrogates the
first form, or `empty_form` when there are none, so it answers correctly for an empty set.

**Alternatives considered**: a dedicated `inline_form_view.html` extending `form_view.html`.
Rejected under Article II once the default block content covered both cases — the extra
template would have carried one line and left the standalone case unsolved.

---

## R7 — Where the view lives, and what it is called

**Decision**: A new module `mvp/views/inline.py` holds `InlineFormsetMixin`,
`MVPInlineCreateView` and `MVPInlineUpdateView`. The two views are exported from
`mvp/views/__init__.py`; the mixin is not, matching the existing rule stated in that file.
Tests live in `tests/test_views/test_inline.py`.

**Rationale**: Article X requires tests to mirror the source tree and to split by class within
one module rather than across files. Either placement satisfies it, so the choice is about
cohesion: `mvp/views/edit.py` already carries the form, create, update and delete views across
roughly six hundred lines, and the parent-and-rows page is a distinct concern with its own
configuration surface. A separate module keeps each test file targeted.

"Inline" is Django's own word for a formset bound to a parent through a foreign key
(`inlineformset_factory`), so the name is the domain vocabulary rather than an invention.

**Configuration surface**: `inline_model`, `inline_form_class`, `inline_fields`,
`inline_extra`, `inline_can_delete`, `inline_max_num` as class attributes for the common cases,
plus `get_formset_factory_kwargs()` returning the full kwargs dictionary so `min_num`,
`validate_min`, `validate_max` and a custom base formset are each one override away. Article
III is satisfied — this is configuration on one class, not a layer between the caller and the
work.

---

## R8 — The demo models behind the worked example

**Decision**: The worked example and the demo page use the existing `Product` and `OrderLine`
models. No new demo model is added.

**Rationale**: `demo/models.py:229` already defines `OrderLine` with a `PROTECT` foreign key to
`Product` (`related_name="order_lines"`) and a `quantity` field. It is the only true
line-item-shaped pair in the demo application and needs no new model and no new factory. Its
docstring records that it was added for delete-view tests; that stays true and gains a second use.

**Correction after the design review**: an earlier draft of this section claimed the pair needed
no `verbose_name`/`help_text` work either. That was wrong. Neither `OrderLine.product` nor
`OrderLine.quantity` carries either, and Article IX makes both mandatory and says explicitly that
it applies to `demo/`. It matters here beyond conformance: this is the pair the worked example
renders, and a page whose job is to demonstrate that a row's field gets the same label and help
text a single form's field gets cannot demonstrate it with a field that has neither. The fields
are given both, with `gettext_lazy`, and the resulting migration is squashed with the branch's
others at convergence.

The naming is a shade off the spec's illustration of an order and its line items, but the shape
is identical and Article II prefers what is already there.

---

## Technology summary

| Concern | Resolution |
|---|---|
| Row field rendering | `\|as_crispy_field`, per field, skipping `DELETE` |
| Set-level errors | Rendered by the packaged component into `<c-alert variant="error">` |
| Row-level field errors | Already handled by `tailwind/layout/help_text_and_errors.html` |
| Row removal | `DELETE` flag set, row hidden, indices untouched |
| Row addition | `empty_form` in a `<template>`, `__prefix__` substitution, `TOTAL_FORMS` incremented |
| Row cap | `validate_max=True` plus a bounded `absolute_max` on the server; the add control compares the visible-row count |
| Client runtime | Alpine 3, already loaded by `mvp/templates/mvp/base.html` |
| Atomicity | `transaction.atomic()` around parent save and formset save |
| Dependencies | crispy pair promoted to runtime, deptry `DEP002` ignores extended |
| Stylesheet | Rebuilt with `invoke build-stylesheet`; new classes are literal, so no safelist entry |
