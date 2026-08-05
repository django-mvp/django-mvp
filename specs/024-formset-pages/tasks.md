# Tasks: Formset Pages

**Input**: Design documents in `specs/024-formset-pages/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`

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
is the Cotton namespace.

---

## Phase 1: Foundational — User Story 1 (Priority: P1)

**Goal**: The packaged form rendering works on a clean install. Nothing else in this feature is
true until it is.

**⚠️ Blocking**: every later phase renders through this path.

- [ ] T001 [US1] Write a failing check that `pyproject.toml` declares both crispy distributions as runtime dependencies, in `tests/test_integrations.py` — read `[project].dependencies` from the installed metadata and assert `django-crispy-forms` and `crispy-tailwind` are present.
- [ ] T002 [US1] Move `django-crispy-forms` and `crispy-tailwind` from `[tool.poetry.group.dev.dependencies]` to `[project].dependencies` in `pyproject.toml`, and regenerate `poetry.lock`.
- [ ] T003 [US1] Add both distribution names to `[tool.deptry.per_rule_ignores] DEP002` in `pyproject.toml`, with a comment stating they are reached through `{% load %}` and `INSTALLED_APPS` rather than a Python import — the same shape as the existing `django-flex-menus` entry. Confirm `poetry run deptry .` is green.
- [ ] T004 [P] [US1] Rewrite the crispy section of `docs/integrations.md`: it is required setup, not an optional add-on. Move the `INSTALLED_APPS` entries and the two `CRISPY_*` settings into the required setup in `README.md` and `docs/getting-started.md`, keeping the existing ordering note that `mvp` precedes `crispy_tailwind` so the packaged `help_text.html` override wins.
- [ ] T005 [US1] Update the standing comment under `[project].dependencies` in `pyproject.toml` — it currently says crispy is an optional integration living behind a guarded import, which this change makes false.

**Checkpoint**: `poetry run deptry .` green, the metadata names both packages, and the documented
setup gets a consumer to a rendered form page. Phases 2 through 6 may begin.

---

## Phase 2: User Story 2 — A formset renders with the packaged look (Priority: P1) 🎯 MVP

**Goal**: Hand any formset to the packaged rendering and get the packaged look, anywhere the
packaged form components already render.

- [ ] T006 [US2] Write failing component tests in `tests/test_components/test_form_formset.py` for `<c-form.formset.row>`: every hidden field is rendered; every visible field except `DELETE` is rendered through crispy's field template; `DELETE` is present as a hidden input and not as a visible checkbox; the form's non-field errors render inside the row. Use the compiled-source `render()` helper already established in `tests/test_components/test_form_field.py`.
- [ ] T007 [US2] Write failing component tests in the same module for `<c-form.formset>`: the management form is present; one row per form in formset order; blank extra rows are indistinguishable from populated ones; `empty_form` appears exactly once inside a `<template>` and carries `__prefix__`.
- [ ] T008 [US2] Write a failing test that both new templates render without error when given an empty context, matching the contract `tests/test_components/test_render_all.py` enforces on every packaged component.
- [ ] T009 [US2] Create `mvp/templates/cotton/form/formset/row.html` per `contracts/formset-component.md`. Render hidden fields directly, visible fields through `|as_crispy_field` skipping `DELETE`, and `DELETE` as a hidden input. Declare `class` in `<c-vars>` — the root element carries literal classes and spreads `{{ attrs }}`, which is the duplicate-attribute defect `tests/test_components/test_class_attribute_merge.py` exists to catch.
- [ ] T010 [US2] Create `mvp/templates/cotton/form/formset/index.html` per the same contract: management form, rows, the `<template>` blank row. Error rendering and the add control arrive in phases 4 and 5; leave their places rather than stubbing behaviour.
- [ ] T011 [US2] Write a failing test in `tests/test_components/test_form_index.py` that `<c-form>` sets `enctype="multipart/form-data"` when its `formset` is multipart and its `form_obj` is not.
- [ ] T012 [US2] Add the `formset` attribute to `<c-vars>` in `mvp/templates/cotton/form/index.html` and consult `formset.is_multipart` alongside `form_obj.is_multipart` in the `enctype` condition.
- [ ] T013 [US2] Write a failing view test in `tests/test_views/test_edit.py` that a formset placed in an `MVPFormView`'s context renders on the page — US2 scenario 4, the standalone case.
- [ ] T014 [US2] Add `{% block formset %}` to `mvp/templates/form_view.html` inside the `<c-form>` body and above `{% block actions %}`, defaulting to `<c-form.formset>` when a `formset` is in context. Pass `:formset="formset"` to `<c-form>`. Emit `formset.media.css` and `formset.media.js` alongside the existing `form.media` in the `head` and `extra_js` blocks.

**Checkpoint**: a formset renders with the packaged look on any packaged form page, including
one with no parent object. SC-008 is provable.

---

## Phase 3: User Story 3 — A record and its rows on one page (Priority: P1)

**Goal**: Configure one view and get the parent-and-rows page, with one submission and no
partial save.

Independent of phases 4 and 5.

- [ ] T015 [US3] Write failing tests in `tests/test_views/test_inline.py` for configuration errors: `inline_model` unset raises `ImproperlyConfigured` naming the attribute; neither `inline_form_class` nor `inline_fields` set raises `ImproperlyConfigured` naming both.
- [ ] T016 [US3] Write failing tests in the same module for the `GET` page: the parent's form and one row per existing related record render together, plus `inline_extra` blank rows.
- [ ] T017 [US3] Write failing tests for the valid submission: both parent and rows persist, and the redirect follows the same rule the packaged single-form pages use (FR-012).
- [ ] T018 [US3] Write a failing test for atomicity: force a failure while saving rows and assert the parent's changes are not persisted either (FR-011, SC-006).
- [ ] T019 [US3] Write a failing test for the invalid submission: an invalid parent with valid rows persists nothing and re-renders with every submitted value still present in both parts (FR-013).
- [ ] T020 [US3] Write a failing test for the create case: a new parent is created and its rows are attached to it (FR-014, US3 scenario 5).
- [ ] T021 [US3] Create `mvp/views/inline.py` with `InlineFormsetMixin` per `contracts/inline-view.md`: the six configuration attributes, `get_formset_factory_kwargs()`, `get_formset_class()`, `get_formset_kwargs()`, a memoising `get_formset()`, and `get_context_data()` injecting `formset`. The memoisation is load-bearing — a second construction inside `form_invalid` would discard the bound formset and blank the page.
- [ ] T022 [US3] Implement `form_valid()` on the mixin: validate the formset, delegate to `form_invalid` when it fails, then save the parent, assign `formset.instance`, and save the formset, all inside one `transaction.atomic()` block.
- [ ] T023 [US3] Add `MVPInlineCreateView` and `MVPInlineUpdateView` to the same module, extending `MVPCreateView` and `MVPUpdateView`, and export both from `mvp/views/__init__.py`. The mixin is not exported, per the rule already stated in that file.

**Checkpoint**: a developer reaches a working parent-and-rows page from configuration alone.
SC-002 and SC-006 are provable.

---

## Phase 4: User Story 4 — Errors appear where the problem is (Priority: P2)

**Goal**: Every error renders at the level it belongs to.

Depends on phase 2.

- [ ] T024 [US4] Write a failing test that proves row-level placement before anything is built on it: a row whose field fails validation renders its message inside that row, adjacent to the field, and no other row carries a message (FR-016, FR-019). This is inherited from crispy's field template rather than written here, and the test is what turns that from an assumption into a fact.
- [ ] T025 [US4] Write a failing test that `formset.non_form_errors` renders above the set, is structurally distinguishable from a row's error, and renders nothing when empty (FR-017).
- [ ] T026 [US4] Write a failing test that no error is rendered only as a page-level summary, and that submitted values survive the re-render (FR-018, US4 scenario 4).
- [ ] T027 [US4] Render `formset.non_form_errors` in `mvp/templates/cotton/form/formset/index.html`, above the rows, inside `<c-alert variant="error">`, only when non-empty. Do not reach for crispy's `errors_formset.html` — it emits raw utility colours rather than DaisyUI classes, which Article XI forbids in a component template.
- [ ] T028 [US4] Write failing tests for the two set-level rules that produce non-form errors through Django itself — too few rows under `validate_min` and too many under `validate_max` — and confirm both render above the set.

**Checkpoint**: SC-003 is provable. No error collapses to the top of the page.

---

## Phase 5: User Story 5 — Adding and removing rows in the browser (Priority: P2)

**Goal**: The user shapes the set while working, and nothing reaches the server until submission.

Depends on phase 2. Independent of phase 4.

- [ ] T029 [US5] Write failing markup tests in `tests/test_components/test_form_formset.py`: the add control is absent or disabled at `formset.max_num`; no remove control renders when the formset forbids deletion; each row's remove control carries an accessible name; neither control submits the form (FR-026).
- [ ] T030 [US5] Write failing view tests in `tests/test_views/test_inline.py`: a submission whose existing row carries `DELETE` deletes that record; a submission whose *added* row carries `DELETE` creates nothing; a record whose row was removed on the page but never submitted is unchanged (FR-022, FR-023, SC-005).
- [ ] T031 [US5] Add the Alpine root to `mvp/templates/cotton/form/formset/index.html`: row count and cap as state, an add handler that clones the `<template>`, substitutes every `__prefix__` with the current `TOTAL_FORMS` value, appends the row and increments `TOTAL_FORMS`. Never decrement it — Django reads rows by contiguous index and a decrement silently shifts every later row.
- [ ] T032 [US5] Add the remove control and removed state to `mvp/templates/cotton/form/formset/row.html`: the control sets the row's removed state, the state drives the hidden `DELETE` value, and the row is hidden rather than detached. Initialise the state from `form.DELETE.value` so a removal survives an invalid submission.
- [ ] T033 [US5] Add translatable labels for the add and remove controls with `{% trans %}`, defaulting per `contracts/formset-component.md` and overridable through the `add-label` and `remove-label` attributes (Article VIII).
- [ ] T034 [US5] Write the one browser test, in `tests/test_e2e/test_formset_rows.py`, scoped to the `e2e` marker at class level rather than module level: adding a row inserts a blank row without a reload and increments `TOTAL_FORMS`; removing a row hides it with no request; submitting afterwards matches the database to what the page showed (SC-004). Article XIV allows exactly this much — anything provable from rendered markup stays in T029 and T030.

**Checkpoint**: SC-004 and SC-005 are provable. No request is made between the first row change
and the submission.

---

## Phase 6: User Story 6 — The path from a model to a working page (Priority: P3)

**Goal**: A developer reaches a working page from the documentation alone.

Depends on every phase above — the capability has to exist before it is documented.

- [ ] T035 [US6] Add `ProductOrderLinesView` to `demo/views.py` using the existing `Product` and `OrderLine` models, and its route to `demo/urls.py`. No new model and no migration.
- [ ] T036 [P] [US6] Write `docs/formsets.md`: the whole path from a model and its related model, through view configuration, to a rendered page, plus the standalone formset case (FR-027, FR-028). Add it to the guide table in `docs/index.md`.
- [ ] T037 [P] [US6] Add `<c-form.formset>` and `<c-form.formset.row>` to the component reference in `docs/components.md`, and the configured view to `docs/views.md`.
- [ ] T038 [P] [US6] Add a component doc page at `demo/templates/demo/components/formset.html` and register it in `demo/component_docs.py`, matching the existing per-component pages.
- [ ] T039 [P] [US6] Define the vocabulary this feature introduces in `CONTEXT.md` — row set, related row, and the two new components in the Forms block of the component inventory (FR-029).
- [ ] T040 [US6] Record the public surface in `CHANGELOG.md` under Unreleased, with an "On upgrade:" paragraph in the house style covering the two new `INSTALLED_APPS` entries a consumer must add (FR-030). Update the README's scope statement, which currently points at formsets as the example of what the package does not yet cover.

**Checkpoint**: SC-007 is provable by following the document without opening the package source.

---

## Convergence (S5, not a story)

Run after every story is done. Not optional and not to be folded into a story's work.

- [ ] T041 Run `poetry run invoke build-stylesheet` and commit the rebuilt `mvp/static/css/django-mvp.css` and its brotli sibling (Article XV). CI cannot catch a miss — the Tailwind build is not byte-reproducible, so this is an author responsibility.
- [ ] T042 Apply the simplification pass to the feature diff. Cleanup stays inside this feature's blast radius; anything wider becomes an issue, not a commit.
- [ ] T043 Confirm the full machine gate: `pytest`, `ruff check`, `ruff format --check`, `mypy mvp`, `deptry .`, and the coverage floors (project ≥ 90%, patch ≥ 85%).

---

## Dependency graph

```text
Phase 1 (US1) ──┬── Phase 2 (US2) ──┬── Phase 4 (US4) ──┐
                │                   └── Phase 5 (US5) ──┤
                └── Phase 3 (US3) ──────────────────────┼── Phase 6 (US6) ── Convergence
                                                        │
```

Phase 3 does not depend on phase 2 in code — the view only puts `formset` in the context — but
its page tests assert against rendered output, so running it after phase 2 avoids writing
assertions against markup that does not exist yet.

## Parallelisation

Within a phase, `[P]` tasks touch different files and may run together. Across phases, phases 4
and 5 are genuinely independent of each other once phase 2 is done, and phase 3 is independent
of both. The pipeline's Phase 1 dispatch policy is one story at a time; the independence is
recorded here for when that changes.

## Task count

43 tasks across six stories and convergence.
