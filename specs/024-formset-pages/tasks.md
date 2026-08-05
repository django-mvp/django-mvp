# Tasks: Formset Pages

**Input**: Design documents in `specs/024-formset-pages/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`

**Revision**: re-planned 2026-08-05 after the S3R design panel. Every accepted finding is applied
here; the panel's reports are archived in the run record and the decisions they produced are
D17–D23 in `decisions.md`. Task ids were renumbered in that pass, so a reference to a task id from
before the re-plan does not resolve.

**Tests**: Mandatory. Article I of the constitution is test-first — every behaviour task is
preceded by a test task that fails first. Test tasks are not optional here and are not to be
folded into the implementation task.

## Format: `[ID] [P?] [Story] Description`

- **[P]** — may run in parallel with other `[P]` tasks in the same phase; different files, no
  shared dependency.
- **[Story]** — the user story the task serves.
- Paths are repository-relative.

## Path conventions

Single Python package. Source in `mvp/`, demo application in `demo/`, tests in `tests/`,
documentation in `docs/`. Component templates under `mvp/templates/cotton/`, where the directory
is the Cotton namespace. No new test directory is created — the browser test lives in
`tests/test_components/`, which is already declared under
`[tool.forge.conformance] non-mirror-paths`.

---

## Phase 1: Foundational — User Story 1 (Priority: P1)

**Goal**: The packaged form rendering works on a clean install. Nothing else in this feature is
true until it is.

**⚠️ Blocking**: every later phase renders through this path.

- [X] T001 [US1] Write a failing test in `tests/test_smoke.py` that parses `pyproject.toml` with `tomllib` and asserts `django-crispy-forms` and `crispy-tailwind` appear in `[project].dependencies` (FR-001). Parse the file, not the installed distribution metadata — `.dist-info/METADATA` is written at install time and would not change when T002 edits the source, so the test would stay red after the fix that should turn it green. `tests/test_smoke.py` is chosen because Article X exempts it from the mirror rule, and because `tests/test_integrations.py` is about the guarded optional integrations that T005 stops crispy from being.
- [X] T002 [US1] Move `django-crispy-forms` and `crispy-tailwind` from `[tool.poetry.group.dev.dependencies]` to `[project].dependencies` in `pyproject.toml`, and regenerate `poetry.lock`.
- [X] T003 [US1] Add both distribution names to `[tool.deptry.per_rule_ignores] DEP002` in `pyproject.toml`, with a comment stating they are reached through `{% load %}` and `INSTALLED_APPS` rather than a Python import — the same shape as the existing `django-flex-menus` entry. Confirm `poetry run deptry .` is green.
- [X] T004 [P] [US1] Rewrite the crispy section of `docs/integrations.md`: it is required setup, not an optional add-on. Move the `INSTALLED_APPS` entries and the two `CRISPY_*` settings into the required setup in `README.md` and `docs/getting-started.md`, keeping the existing ordering note that `mvp` precedes `crispy_tailwind` so the packaged `help_text.html` override wins. Also drop "crispy forms" from the integrations row of the guide table in `docs/index.md`, which describes it as an optional third-party integration — the same standing falsehood T005 corrects in `pyproject.toml`.
- [X] T005 [US1] Update the standing comment under `[project].dependencies` in `pyproject.toml` — it currently says crispy is an optional integration living behind a guarded import, which this change makes false.

**Checkpoint**: `poetry run deptry .` green, the metadata names both packages, and the documented
setup gets a consumer to a rendered form page.

---

## Phase 2: User Story 2 — A formset renders with the packaged look (Priority: P1) 🎯 MVP

**Goal**: Hand any formset to the packaged rendering and get the packaged look, anywhere the
packaged form components already render.

- [X] T006 [US2] Write failing component tests in `tests/test_components/test_form_formset.py` for `<c-form.formset.row>`: every hidden field is rendered; every visible field except `DELETE` is rendered through crispy's field template; `DELETE` is present as a hidden input and not as a visible checkbox; the form's non-field errors render inside the row. Use the compiled-source `render()` helper already established in `tests/test_components/test_form_field.py`. These are written before the template exists and fail with `TemplateDoesNotExist` first, which is the red state — the empty-context floor is supplied automatically by `test_render_all.py`, so do not write a separate test for it.
- [X] T007 [US2] Write failing component tests in the same module for `<c-form.formset>`: the management form is present; one row per form in formset order; blank extra rows are indistinguishable from populated ones; `empty_form` appears exactly once inside a `<template>` and carries `__prefix__`. Same red-state note as T006.
- [X] T008 [US2] Create `mvp/templates/cotton/form/formset/row.html` per `contracts/formset-component.md`. Render hidden fields directly, visible fields through `|as_crispy_field` skipping `DELETE`, and `DELETE` as a hidden input. Declare `class` in `<c-vars>` — the root element carries literal classes and spreads `{{ attrs }}`, which is the duplicate-attribute defect `tests/test_components/test_class_attribute_merge.py` exists to catch. It must render with an empty context; `test_render_all.py` enrols it automatically and no `SKIP` entry may be added.
- [X] T009 [US2] Create `mvp/templates/cotton/form/formset/index.html` per the same contract: management form, rows, the `<template>` blank row. Error rendering and the add control arrive in phases 4 and 5; leave their places rather than stubbing behaviour. Same empty-context requirement as T008.
- [X] T010 [US2] Write a failing test in `tests/test_components/test_form_index.py` that `<c-form>` sets `enctype="multipart/form-data"` when its `formset` is multipart and its `form_obj` is not.
- [X] T011 [US2] Add the `formset` attribute to `<c-vars>` in `mvp/templates/cotton/form/index.html` and consult `formset.is_multipart` alongside `form_obj.is_multipart` in the `enctype` condition.
- [X] T012 [US2] Write a failing view test in `tests/test_views/test_edit.py` that a formset placed in an `MVPFormView`'s context renders on the page — US2 scenario 4, the standalone case.
- [X] T013 [US2] Add `{% block formset %}` to `mvp/templates/form_view.html` inside the `<c-form>` body and above `{% block actions %}`, defaulting to `<c-form.formset>` when a `formset` is in context. Pass `:formset="formset"` to `<c-form>`. Emit `formset.media.css` and `formset.media.js` alongside the existing `form.media` in the `head` and `extra_js` blocks.

**Checkpoint**: a formset renders with the packaged look on any packaged form page, including one
with no parent object. SC-008 is provable.

---

## Phase 3: User Story 3 — A record and its rows on one page (Priority: P1)

**Goal**: Configure one view and get the parent-and-rows page, with one submission and no partial
save.

**Depends on Phase 2.** The view only puts `formset` in the context, so there is no code
dependency — but T015, T016, T018 and T019 assert against rendered rows, and rows only reach the
page through the `{% block formset %}` that T013 adds. A worktree branched before Phase 2 cannot
turn these green.

- [X] T014 [US3] Write a failing test in `tests/test_views/test_inline.py` that a view with `inline_model` unset raises `ImproperlyConfigured` naming the attribute. Only that one guard: Django's own `modelform_factory` already raises a clear `ImproperlyConfigured` when neither fields nor a form class is given, so a second check would duplicate it.
- [X] T015 [US3] Write failing tests in the same module for the `GET` page: the parent's form and one row per existing related record render together, plus `inline_extra` blank rows.
- [X] T016 [US3] Write failing tests for the valid submission: both parent and rows persist, and the redirect follows the same rule the packaged single-form pages use (FR-012). Assert in the same task that the parent is saved **exactly once** per submission — the natural way to produce the flash after the transaction re-enters `ModelFormMixin.form_valid` and saves it a second time, and nothing else in this phase would catch that. Exercise FR-012 on the **create** path with an object-dependent success URL — either no `success_url` and a model defining `get_absolute_url()`, or `success_url = "detail"` — not only `success_url = "list"`. `"list"` resolves without the object, so a fixture using it passes even when the URL is resolved before the parent exists.
- [X] T017 [US3] Write a failing test for atomicity: force a failure while saving rows and assert the parent's changes are not persisted either (FR-011, SC-006). Assert in the same test that no success message survives the rollback — Django's message storage is not transactional, so a flash queued inside the block would outlive it.
- [X] T018 [US3] Write a failing test for an invalid parent with valid rows: nothing persists and the page re-renders with every submitted value still present in both parts (FR-013).
- [X] T019 [US3] Write a failing test for the mirror case — a **valid parent with an invalid row**: nothing persists, the page re-renders with every submitted value present in both parts, and the row carries its error (FR-010, FR-013, and the spec's edge case for one part valid and the other not). This is the branch `form_valid` adds, and without it the formset-validation guard can be deleted with every other Phase 3 test still passing.
- [X] T020 [US3] Write a failing test for the create case: a new parent is created and its rows are attached to it (FR-014, US3 scenario 5).
- [X] T021 [US3] Write two failing tests about the cap. First, a submission whose `TOTAL_FORMS` exceeds the configured `inline_max_num` is rejected with a set-level error and persists nothing — the browser control is presentation, and this is the enforcement. Second, and equally important, a submission that is **within** the cap once removals are counted is **accepted**: with a cap of three, a page that added four rows and removed two submits five forms with two `DELETE` flags and must save. That second test is what pins `absolute_max` to Django's default; deriving it from the cap makes this exact submission fail and silently drops the fifth row's values.
- [X] T022 [US3] Create `mvp/views/inline.py` with `InlineFormsetMixin` per `contracts/inline-view.md`: the six configuration attributes, `get_formset_factory_kwargs()`, `get_formset_class()`, `get_formset_kwargs()`, a memoising `get_formset()`, and `get_context_data()` injecting `formset`. Three details are load-bearing and specified rather than left to judgement. `get_formset_factory_kwargs()` derives its dictionary from the six attributes and is documented as super-and-extend. It sets `validate_max=True` whenever `inline_max_num` is set, and **leaves `absolute_max` at Django's default** — deriving it from the cap rejects submissions that are within the cap and drops rows before validation, per the contract. And the memoisation is not an optimisation: a second construction inside `form_invalid` would discard the bound formset and blank the page.
- [X] T023 [US3] Implement `form_valid()` on the mixin: validate the formset, delegate to `form_invalid` when it fails, then inside one `transaction.atomic()` block save the parent, assign `formset.instance`, and save the formset. The success URL, the message and the redirect are all produced **after** the block exits, and **not by calling `super().form_valid()` at all** — that reaches `SuccessMessageMixin`, which delegates to `ModelFormMixin.form_valid`, which saves the parent again. Queue the message with `messages.success` and return `HttpResponseRedirect` directly. Resolve the URL **after** the saves, never before: on the create path `self.object` is `None` until then, and `get_success_url()` either raises or silently returns an unresolved shorthand as a literal path, with the rows already committed. `MVPDeleteView.form_valid` is the precedent for producing the message and redirect directly, not for the ordering — it resolves first only because its object is about to disappear.
- [X] T024 [US3] Add `MVPInlineCreateView` and `MVPInlineUpdateView` to the same module, extending `MVPCreateView` and `MVPUpdateView`, and export both from `mvp/views/__init__.py`. The mixin is not exported, per the rule already stated in that file.

**Checkpoint**: a developer reaches a working parent-and-rows page from configuration alone.
SC-002 and SC-006 are provable, and the configured cap is a cap.

---

## Phase 4: User Story 4 — Errors appear where the problem is (Priority: P2)

**Goal**: Every error renders at the level it belongs to.

Depends on Phase 2. **Runs before or after Phase 5, never beside it** — both phases edit
`mvp/templates/cotton/form/formset/index.html`.

- [X] T025 [US4] Write a failing test that proves row-level placement before anything is built on it: a row whose field fails validation renders its message inside that row, adjacent to the field, and no other row carries a message; and, in the same task, a formset with errors on **two different rows** renders a message inside each of them (FR-016, FR-019, US4 scenario 3). This placement is inherited from crispy's field template rather than written here, and the test is what turns that from an assumption into a fact.
- [X] T026 [US4] Write a failing test that `formset.non_form_errors` renders above the set, is structurally distinguishable from a row's error, and renders nothing when empty (FR-017).
- [X] T027 [US4] Write a failing test that no error is rendered only as a page-level summary, and that submitted values survive the re-render (FR-018, US4 scenario 4).
- [X] T028 [US4] Render `formset.non_form_errors` in `mvp/templates/cotton/form/formset/index.html`, above the rows, inside `<c-alert variant="error">`, only when non-empty. Do not reach for crispy's `errors_formset.html` — it emits raw utility colours rather than DaisyUI classes, which Article XI forbids in a component template.
- [X] T029 [US4] Write failing tests for the two set-level rules Django produces as non-form errors — too few rows under `validate_min` and too many under `validate_max` — and confirm both render above the set.

**Checkpoint**: SC-003 is provable. No error collapses to the top of the page.

---

## Phase 5: User Story 5 — Adding and removing rows in the browser (Priority: P2)

**Goal**: The user shapes the set while working, and nothing reaches the server until submission.

Depends on Phase 2. Shares `mvp/templates/cotton/form/formset/index.html` with Phase 4, so the
two are sequential.

- [x] T030 [US5] Write failing markup tests in `tests/test_components/test_form_formset.py`: no remove control renders when the formset forbids deletion; each row's remove control carries an accessible name; neither control submits the form; the add control is bound to the count of rows **not marked for removal**, so removing a row on a capped formset frees its slot rather than forfeiting it (FR-026).
- [x] T031 [US5] Write failing view tests in `tests/test_views/test_inline.py`: a submission whose existing row carries `DELETE` deletes that record; a submission whose *added* row carries `DELETE` creates nothing; a record whose row was removed on the page but never submitted is unchanged (FR-022, FR-023, SC-005).
- [x] T032 [US5] Add the Alpine root to `mvp/templates/cotton/form/formset/index.html`. Two counters, not one: a monotonic `total` that seeds `__prefix__` substitution and `TOTAL_FORMS`, and a `visible` count of rows not marked for removal, which is what the add control compares against `formset.max_num`. Seed `total` from `{{ formset.total_form_count }}` — an integer Django has already clamped — and never from the management-form input's DOM value, which is a string the server re-emits verbatim after an invalid submission. Adding a row clones the `<template>`, substitutes every `__prefix__` with `total`, appends the row and increments both counters and `TOTAL_FORMS`. Never decrement `TOTAL_FORMS`: Django reads rows by contiguous index and a decrement silently shifts every later row.
- [x] T033 [US5] Add the remove control and removed state to `mvp/templates/cotton/form/formset/row.html`: the control sets the row's removed state, the state drives the hidden `DELETE` value and decrements the set's `visible` count, and the row is hidden rather than detached. Initialise the state from `form.DELETE.value` so a removal survives an invalid submission.
- [x] T034 [US5] Add translatable labels for the add and remove controls with `{% trans %}`, defaulting per `contracts/formset-component.md` and overridable through the `add-label` and `remove-label` attributes (Article VIII).
- [x] T035 [US5] Write the one browser test as a class in `tests/test_components/test_form_formset.py`, with the `e2e` marker and the playwright `skipif` at **class** level — not module level, which would hide the unit tests underneath it (Article X), and following the precedent already set in `tests/test_views/test_error.py`. Assert: adding a row inserts a blank row without a reload and increments `TOTAL_FORMS`; removing a pre-rendered row hides it with no request; **removing the row that was just added** hides it and sets its `DELETE`, which is the one behaviour no server-side test can reach, because cloned markup appended into a live Alpine tree is inert until it is initialised; and submitting afterwards matches the database to what the page showed (SC-004, US5 scenario 3). Article XIV allows exactly this much — anything provable from rendered markup stays in T030 and T031.

**Checkpoint**: SC-004 and SC-005 are provable. No request is made between the first row change
and the submission.

---

## Phase 6: User Story 6 — The path from a model to a working page (Priority: P3)

**Goal**: A developer reaches a working page from the documentation alone.

Depends on every phase above — the capability has to exist before it is documented.

- [ ] T036 [US6] Add `ProductOrderLinesView` to `demo/views.py` using the existing `Product` and `OrderLine` models, and its route to `demo/urls.py`.
- [ ] T037 [US6] Give `demo.OrderLine`'s `product` and `quantity` fields `verbose_name` and `help_text` with `gettext_lazy`, and wrap its `Meta.verbose_name` strings, then generate the migration. Article IX makes both mandatory and applies to `demo/`, and this is the pair the worked example renders — a page demonstrating the packaged look cannot demonstrate help text with a field that has none.
- [ ] T038 [P] [US6] Write `docs/formsets.md`: the whole path from a model and its related model, through view configuration, to a rendered page, plus the standalone formset case (FR-027, FR-028). Add it to the guide table in `docs/index.md`.
- [ ] T039 [P] [US6] Add `<c-form.formset>` and `<c-form.formset.row>` to the component reference in `docs/components.md`, and the configured view to `docs/views.md`.
- [ ] T040 [P] [US6] Add a component doc page at `demo/templates/demo/components/formset.html` and register it in `demo/component_docs.py`, matching the existing per-component pages.
- [ ] T041 [P] [US6] Define the vocabulary this feature introduces in `CONTEXT.md` — row set, related row, and the two new components in the Forms block of the component inventory (FR-029).
- [ ] T042 [US6] Record the public surface in `CHANGELOG.md` under Unreleased, with an "On upgrade:" paragraph in the house style covering the two new `INSTALLED_APPS` entries a consumer must add (FR-030). Update the README's scope statement, which currently points at formsets as the example of what the package does not yet cover.
- [ ] T043 [US6] Annotate roadmap item R12 in `docs/ROADMAP.md` in place. Strike through its **second** deliverable in full — "Form and list pages rendering without any undeclared dependency, at a reduced but working level of polish" — and forward-tag it to this feature. Strike the first sentence of the prose above it for the same reason. Both pages loaded the same distribution, so declaring it settles the whole deliverable, and the reduced-polish framing goes with it. Leave the first, third and fourth deliverables intact: the guarded-or-declared rule, the unguarded module-level import, the documented-but-absent form renderer setting and the optional-dependency check all stay with R12. Strike through, never delete. See the refined Assumption in `spec.md` and D24 — an earlier reading had this as the first deliverable and as only half of it, and both were wrong.

**Checkpoint**: SC-007 is provable by following the document without opening the package source.

---

## Convergence (S5, not a story)

Run after every story is done. Not optional and not to be folded into a story's work.

- [ ] T044 Run `poetry run invoke build-stylesheet` and commit the rebuilt `mvp/static/css/django-mvp.css` and its brotli sibling (Article XV). CI cannot catch a miss — the Tailwind build is not byte-reproducible, so this is an author responsibility.
- [ ] T045 Apply the simplification pass to the feature diff. Cleanup stays inside this feature's blast radius; anything wider becomes an issue, not a commit.
- [ ] T046 Confirm the full machine gate: `pytest`, `ruff check`, `ruff format --check`, `mypy mvp`, `deptry .`, and the coverage floors (project ≥ 90%, patch ≥ 85%). Squash the branch's migrations — T037 introduces one — per Article IX.

---

## Dependency graph

```text
Phase 1 (US1)
    │
    └── Phase 2 (US2) ──┬── Phase 3 (US3) ──┐
                        │                   │
                        ├── Phase 4 (US4) ──┤
                        │        │          │
                        └── Phase 5 (US5) ──┴── Phase 6 (US6) ── Convergence
```

Phase 3 depends on Phase 2 for its rendered assertions, not for its code. Phases 4 and 5 are
sequential with each other because both edit
`mvp/templates/cotton/form/formset/index.html`; either order works.

## Parallelisation

Within a phase, `[P]` tasks touch different files and may run together. Across phases, Phase 3 is
independent of Phases 4 and 5 and could run beside them. **Phases 4 and 5 cannot run
concurrently** — T028 and T032 both edit
`mvp/templates/cotton/form/formset/index.html`, and T033 edits the row template Phase 4's tests
render through. The pipeline's current dispatch policy is one story at a time; this note exists
for when that changes, so it names the file rather than the phase.

## Task count

43 tasks across six stories, plus three convergence tasks.
