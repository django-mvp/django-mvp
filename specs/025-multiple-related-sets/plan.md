# Implementation Plan: More than one row set on an inline page

**Branch**: `025-multiple-related-sets` · **Spec**: `spec.md` · **Issue**: #194 · **PR**: #215

## Summary

Replace the six `inline_*` view attributes with a declaration class per related model, listed on
the view as `inlines`. The view builds every declaration into its own formset, checks their
prefixes are distinct, validates all of them on both the valid-parent and invalid-parent paths,
and saves the parent and every set in one transaction. The same view covers the rows-only update
page: when the parent's `fields` is empty the parent form renders nothing and is never saved, and
the sets bind to the record the URL identifies.

The declaration is named after Django's own inlines: the class is `InlineFormSet`, and its options
are `django.contrib.admin`'s attribute names, which are also `inlineformset_factory`'s parameter
names (research R7). django-extra-views solved this first and its `factory_kwargs`/`formset_kwargs`
split is a good idea worth taking, but it is prior art rather than a surface to reproduce. Two
behaviours it does not have are ours by requirement: the transaction (FR-009) and the
prefix-collision error (FR-005).

The declaration also decides things Django exposes but no packaged view currently reaches: the
keyword arguments of each *individual* form (FR-021), and the order the forms are displayed in
(FR-022).

Nothing in the rendering layer is rebuilt. `<c-form.formset>` and `<c-form.formset.row>` already
render one set; the templates change only to loop over a list instead of reading one variable.

## Technical Context

**Language**: Python 3.12+ · **Framework**: Django 5.2+ / 6.0 · **Templates**: django-cotton,
Tailwind v4 + DaisyUI 5 · **Testing**: pytest, pytest-django, factory-boy · **Package manager**:
Poetry.

**No new dependency.** Everything needed is in Django: `inlineformset_factory`,
`BaseInlineFormSet.get_default_prefix`, `all_valid`, `transaction.atomic`.

**Files this feature owns:**

| Path | Change |
|---|---|
| `mvp/views/inline.py` | rewritten — `InlineFormSet` + `InlinesMixin`, replacing `InlineFormsetMixin` |
| `mvp/views/__init__.py` | export `InlineFormSet`; view class names unchanged |
| `mvp/templates/form_view.html` | render a list of sets, not one |
| `mvp/templates/cotton/form/index.html` | multipart decided from parent form plus every set |
| `tests/test_views/test_inline.py` | rewritten against the new surface |
| `demo/` | a page carrying two sets; a rows-only page |
| `docs/formsets.md`, `docs/views.md`, `CONTEXT.md`, `CHANGELOG.md` | the migration story and the glossary term (`docs/views.md:123` documents the removed attributes and is easily missed) |

**Out of scope, stated so it is not drifted into:** the row-adding JavaScript, the formset
components' internals, standalone formset rendering, and any per-row permission model. All are
FS-024's and unchanged.

## Constitution Check

| Article | Verdict |
|---|---|
| I Test-First | Every task pairs a test written first with the code that satisfies it. |
| II Simplicity | One declaration class and one mixin replace one mixin. No new layer. |
| III Anti-Abstraction | `InlineFormSet` has a present concrete second use by construction — the feature exists because there are two of them on a page. |
| IV Integration-First | The contracts below are written before internals; tests drive the view through `as_view()` and a real request, not by calling methods. |
| V Security & data-safety | The cap decision is inherited from FS-024 D25 and pinned by a test in both directions. The collision check is a data-integrity guard, not a nicety: without it two sets read the same POST keys. |
| VI Documentation | US5 is a delivered story, not a follow-up. `CONTEXT.md` gains the declaration term. |
| VII Dependency discipline | No new dependency. `deptry` unaffected. |
| VIII Internationalization | Every new user-facing string is `gettext_lazy`; the configuration errors are developer-facing and stay untranslated, matching the existing `ImproperlyConfigured` messages. |
| X Test structure | Tests mirror the source tree, one factory per model, classes grouping behaviour. |
| XI Components are the public API | `c-form` gains one attribute for the list of sets and keeps its existing `formset` attribute. The multipart decision stays attribute-driven — never read from ambient context (S3R ARCH-002). |
| XIII Rendered markup is a contract | Heading-per-set and multipart encoding are asserted on rendered markup. |
| XIV Browser tests are the exception | **None added.** Everything here is expressible with the test client and rendered-template assertions. |
| XV Shipped stylesheet | No new class is introduced, so no rebuild is expected. Verified at converge rather than assumed. |
| XVI Compatibility | The breaking change is the point; CHANGELOG entry is FR-026 and a delivered story. |

No Complexity Tracking entry, and no justification owed for the attribute names: they are Django's
own (research R7). The one behaviour needing a stated reason is the parent touch on a rows-only
page, and R12 states it with measurements.

## Design

### `InlineFormSet` — the declaration

A plain class, instantiated per request by the view. Declaring one is the whole configuration.

```python
class OrderLineInline(InlineFormSet):
    model = OrderLine            # the RELATED model, as in django.contrib.admin
    fields = ["quantity", "unit_price"]
    extra = 2
    title = _("Line items")
```

Attributes, all of them admin's names or `inlineformset_factory`'s: `model`, `fields`, `exclude`,
`form`, `formset`, `extra`, `min_num`, `max_num`, `can_delete`, `fk_name`, `prefix`, `initial`,
`factory_kwargs`, `formset_kwargs`, `form_kwargs`. Two are ours because admin has no equivalent:
`title` and `description`, the rendered heading and the help text beneath it. **`title` defaults to
the related model's `verbose_name_plural`**, so an unset heading is the one admin would have given
(Sam, plan gate). The attribute keeps its own name because admin's covers only the first half of
what the pair does.

`can_order` is **not** included. It is a distinct feature — an `ORDER` field on every form so the
*user* can reorder rows — and nothing asks for it yet. It stays reachable through `factory_kwargs`.
What is included is FR-022's display order, which is a different thing and is a method, below.

Methods, each mirroring its attribute so a subclass can decide per request: `get_title`,
`get_description`, `get_factory_kwargs`, `get_formset_kwargs`, `get_formset_class`,
`construct_formset`, plus the two new hooks:

- **`get_form_kwargs(index)`** — Django's own signature, not the shared-dictionary variant
  (R13). `index` says which form is being built and is `None` for the blank template form the
  browser clones. This is what lets a set give each form different arguments; the shared
  `form_kwargs` attribute stays as the default for the common case where they do not differ.
- **`sort_forms(forms)`** — returns the sequence the forms are displayed in, defaulting to the
  order given. **Display only.** It must not reach the order rows are validated or saved in, since
  reordering that would change which row is which.

Three decisions inside it:

- **`model` keeps meaning the related model for its whole life** (R2), as it does on an
  `InlineModelAdmin`. The parent is held separately, never written over it.
- **The shorthands are folded into `factory_kwargs`, and `factory_kwargs` wins** on any key both
  set. One direction, stated in the docstring, so there is never a question which applies.
- **Both kwarg dicts are copied at both levels** (R6), because class-level nested dicts are shared
  by every request in the process.
- **`prefix` is assembled into `get_formset_kwargs()`** when the declaration sets one, and omitted
  otherwise so Django's per-relation default applies (R3). This is load-bearing beyond FR-004: the
  collision error raised by FR-005 tells the developer to set a prefix, so an unwired override
  would make the error's own suggested fix do nothing. (S3R SPEC-001.)

`validate_max` is switched on alongside `max_num`; `absolute_max` is never derived (R9).

**`exclude` and the multi-relation shape.** Django's `BaseInlineFormSet.add_fields` replaces only
the set's own foreign key with an `InlineForeignKeyField` bound to the parent. Any *other* foreign
key the field selection admits stays a plain `ModelChoiceField` over the full default manager, so a
set declared with `exclude` on a model that reaches the parent twice renders the sibling relation
as a chooser over every parent record. Row identity is not at risk — the formset's queryset is
already parent-scoped — but the documentation must tell developers to name `fields` explicitly on
that shape. No code change. (S3R SEC-001.)

### `InlinesMixin` — the view side

- `get_inlines()` → the declaration classes, copied.
- `get_parent_model()` → `self.model`, else the loaded object's class, else
  `self.get_queryset().model` (FR-007), matching `ModelFormMixin.get_form_class`.
- `construct_inlines()` → one formset per declaration, memoised per request, raising
  `ImproperlyConfigured` on a duplicate prefix and naming both declarations and the fix.
- `get_context_data()` → `inlines` (the list) plus a flag saying whether any set needs multipart.
- `form_valid()` / `form_invalid()` → validate every set on **both** paths using Django's
  `all_valid` (R5, R11), then save inside one `transaction.atomic()`.
- **The parent form is saved only when the page has parent fields.** On a rows-only page the
  loaded instance already has a pk; its form is never saved, and its timestamp is touched
  separately if that is switched on (R8, R12).

**Memoisation is kept, and its stated reason is corrected.** FS-024's docstring says a rebuild
would leave the page blank. That is false: `get_formset_kwargs()` puts `data` and `files` in on
POST, so a rebuilt formset is bound to the same submission and re-renders the same values and the
same errors. The reasons that do hold, and that get stronger with several sets, are that one
construction per request avoids repeating N querysets and N configuration guards, and that the
formsets rendered are then the same objects that were validated. A fence with a false reason on it
is a fence someone removes later after checking. (S3R ARCH-004.)

### The rows-only page

`fields = []` on an update view. No new view class, no new attribute for the page itself — the
emptiness *is* the configuration, which is what folds a second view class into this one.

Guards: create with no parent fields raises (FR-017); update with neither parent fields nor any
set raises (FR-018). Both at page-build time, with the class name and the fix in the message.

**The parent form is never saved here, and the parent's timestamp is touched instead** (FR-015,
FR-016). These are two separate statements and both are load-bearing:

- An empty `ModelForm` is always valid, and its `save()` issues a full `UPDATE` of every column
  from values read when the page was opened. Measured in R12: that silently discards a change
  another writer made while the page was open. So the form is not saved.
- Recording that something changed is still wanted, and is done by writing only the model's
  `auto_now` fields (`instance.save(update_fields=[...])`). R12 measures that this bumps the
  timestamp and leaves a concurrent write to other fields intact.

**On by default**, switchable off with one attribute on the view. The default is safe because a
model with no `auto_now` field has nothing to write, so the touch is a no-op there — it acts only
where the developer has already said, by declaring such a field, that they care when the record
last changed. It happens inside the same transaction as the rows, and it fires the model's save
signals and any lifecycle hooks, which is the point rather than a side effect.

### Templates

**`form_view.html` gains the `inlines` loop and keeps `formset`.** FS-024 delivered a second,
documented capability through the same template: any packaged form view that puts a `formset` in
its context renders it, with no parent record involved. That case is documented in
`docs/formsets.md` under "The standalone case", rendered by the demo, and pinned by a test at
`tests/test_views/test_edit.py:2091`. Replacing the variable would delete a shipped feature this
plan declares out of scope. The two coexist: `formset` for the standalone case, `inlines` for the
configured page. (S3R ARCH-001.)

The template's two media blocks iterate the sets as well as the standalone formset. They currently
emit `{{ formset.media.css }}` and `{{ formset.media.js }}`; against a list those resolve to
nothing and a row form whose widget carries media renders without it, silently. (S3R SPEC-004.)

**The multipart decision stays on the component, as an attribute.** Article XI and the house rule
that Cotton components are configured by attributes both forbid reading it from ambient context,
and `tests/test_components/test_form_index.py:41` renders `c-form` directly with a `formset`
attribute and asserts the encoding. The component keeps its existing `formset` attribute and gains
one for the list; the decision is `form_obj` or `formset` or any set needing it (FR-012). (S3R
ARCH-002.)

## Story plan

Six phases. US1 is foundational and sequential; nothing else can start before it.

| Phase | Story | Depends on |
|---|---|---|
| 1 | US1 — the declaration class, one set end to end | — |
| 2 | US2 — several sets, prefixes, transaction, multipart | US1 |
| 3 | US3 — every set validated on both paths | US1 |
| 4 | US4 — the rows-only page | US1, US2 |
| 5 | US5 — docs, changelog, glossary, demo | all |
| 6 | Converge — simplify pass, stylesheet check, full gates | all |

US2 and US3 are independent of each other and can run in parallel after US1.

## Risks

- **The invalid-parent path is the one most likely to be got wrong**, because lazy template
  evaluation makes a missing explicit validation look like it works. US3's tests assert on
  `formset.errors` from the response context, not on rendered HTML alone.
- **The collision check must fire at build time, not render time.** A check that only trips when a
  template happens to touch both prefixes is not FR-005.
- **Removing the `inline_*` attributes touches the demo and the docs**, and a missed reference is a
  silently wrong instruction. US5 scenario 4 is a repository-wide search, not a spot check.
- **`fields = []` versus `fields = None`.** `None` means "not configured" and must keep raising
  Django's own error; only an empty collection selects the rows-only page. The tests pin both.
- **The parent touch is a write on a page that claims not to write the parent.** The distinction
  between "does not change field values" and "does not write at all" has to survive into the tests
  and the documentation, or the next reader will collapse them. The concurrency test is what pins
  it, and it is the one test here that would pass against the naive implementation only by luck.
- **`sort_forms` must not reach saving.** A display-order hook that reordered `formset.forms` would
  change which submitted row maps to which record. The test asserts the saved order is unaffected.

## Complexity Tracking

None.
