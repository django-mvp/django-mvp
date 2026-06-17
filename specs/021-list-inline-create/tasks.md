# Tasks: List View Inline Create

**Input**: Design documents from `specs/021-list-inline-create/`
**Prerequisites**: [plan.md](plan.md) ✅ · [spec.md](spec.md) ✅ · [research.md](research.md) ✅ · [data-model.md](data-model.md) ✅ · [quickstart.md](quickstart.md) ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

**Plan → Tasks phase mapping**:

| Plan Phase | Tasks Phase(s) | Tasks |
|---|---|---|
| Phase 1 — Mixin Extension | Phase 1 (Setup) + Phase 2 (Foundational) | T001–T007 |
| Phase 2 — Template Generalisation | Phase 3 (US1) | T008–T013 |
| Phase 3 — Demo Migration | Phase 6 (Polish) | T016–T019b |
| Phase 4 — Tests | Woven throughout phases 2–6 (T002, T014, T015, T018) | — |

**Test naming convention** (required for T014/T015 selectors to work):

- All inline-create tests MUST live in `TestListViewInlineCreate` in `tests/test_views/test_list_view.py`
- US2 tests MUST be named `test_fallback_*`; US3 tests MUST be named `test_permission_*`

---

## Phase 1: Setup

**Purpose**: Confirm baseline before any changes land

- [ ] T001 Verify existing test suite is clean before changes — `poetry run pytest tests/test_views/test_list_view.py -q` (record any pre-existing failures)

---

## Phase 2: Foundational — `MVPListViewMixin` Extension

**Purpose**: The mixin extension is a shared prerequisite for all three user stories. No user story work can begin until this phase is complete.

**⚠️ CRITICAL**: Must be complete before Phase 3, 4, and 5.

- [ ] T002 Write failing unit tests for all three user stories in class `TestListViewInlineCreate` in `tests/test_views/test_list_view.py`; observe ALL fail before proceeding. Tests MUST cover:
  - **Context injection** (US1, FR-002): `create_form` present in context when `create_form_class` set + permitted
  - **Auto-derived title** (US1, FR-007): `create_modal_title` == `"Add <VerboseName>"` when `create_modal_title = None`
  - **Title override** (US1, FR-007): explicit `create_modal_title` attribute is used verbatim
  - **`get_create_form()` hook** (US1, FR-005): override returns custom form instance
  - **Toolbar HTML — modal state** (FR-006): rendered HTML contains `data-bs-toggle="modal"` when both `create_url` and `create_form` present
  - **Toolbar HTML — fallback link state** (US2, FR-006): rendered HTML contains `<a href="...">` WITHOUT `data-bs-toggle="modal"` when `create_form_class = None` + `has_create_permission = True`; test named `test_fallback_*`
  - **Toolbar HTML — no button state** (FR-006): no create UI element when both absent
  - **Boolean permission gate** (US3, FR-004): `create_form` absent when `has_create_permission = False`; test named `test_permission_*`
  - **Callable permission gate** (US3, FR-004): `create_form` absent when callable returns `False`; test named `test_permission_*`
  - **`MVPCreateView` `?next=` redirect** (FR-010): POST to create URL with `?next=/products/` returns HTTP 302 to `/products/`
  - **Backward compat** (SC-004): list view with `create_form_class = None` renders identically to pre-feature behaviour (no context key, no create button)
- [ ] T003 Add `create_form_class = None` and `create_modal_title = None` class attributes to `MVPListViewMixin` in `mvp/views/list.py`
- [ ] T004 Add `get_create_form()` hook method to `MVPListViewMixin` in `mvp/views/list.py` — returns `self.create_form_class()` or `None`
- [ ] T005 Extend `MVPListViewMixin.get_context_data()` with permission-aware `create_form` and `create_modal_title` injection (boolean + callable `has_create_permission` check) in `mvp/views/list.py`
- [ ] T006 Update `MVPListViewMixin` docstring — add `create_form_class`, `create_modal_title` to Config section; `get_create_form()` to Override hooks; `create_form`, `create_modal_title` to Context section — in `mvp/views/list.py`
- [ ] T007 Validate Phase 2 — `poetry run python manage.py check` · `poetry run ruff check mvp/views/list.py` · `poetry run pytest tests/test_views/test_list_view.py -x -q`

**Checkpoint**: Mixin complete — all three user story tests pass. Template and demo work can now begin.

---

## Phase 3: User Story 1 — Inline Create via Modal (Priority: P1) 🎯 MVP

**Goal**: The list view template renders a generically-titled create modal with a `?next=`-aware form action when `create_form` is in context.

**Independent Test**: Visit the demo product list page; an "Add new" button opens a modal titled "Add Product"; the form action URL includes `?next=/products/`.

### Implementation for User Story 1

- [ ] T008 [US1] **Before editing**: consult the `django-cotton-bs5` skill (`.github/skills/django-cotton-bs5/SKILL.md`) to confirm no prebuilt component supersedes the planned changes — Constitution IX. Then wrap the `<c-modal id="createModal">` block in `{% if create_form %}...{% endif %}` in `mvp/templates/list_view.html`
- [ ] T009 [US1] Replace hardcoded `title="{% trans "Create product" %}"` with `title="{{ create_modal_title }}"` on `<c-form>` in `mvp/templates/list_view.html`
- [ ] T010 [US1] Append `?next={{ request.path }}` to the form action: `action="{{ directory.create_url }}?next={{ request.path }}"` in `mvp/templates/list_view.html`
- [ ] T011 [US1] Run djlint on modified template — `poetry run djlint mvp/templates/list_view.html --check`; fix any violations
- [ ] T012 [US1] Playwright-cli verification — open the demo product list page (`/products/`); assert: "Add new" button is visible in toolbar; click opens modal; modal header text is "Add Product" (not "Create product"); form `action` attribute contains `?next=`
- [ ] T013 [US1] Validate Phase 3 — `poetry run python manage.py check` · `poetry run pytest tests/test_views/test_list_view.py -x -q`

**Checkpoint**: User Story 1 fully functional — modal renders with auto-derived title and correct form action.

---

## Phase 4: User Story 2 — Fallback to Create Page Link (Priority: P2)

**Goal**: When `create_form_class` is absent and `has_create_permission = True`, the toolbar shows a link button to the create page (not a modal trigger). No template changes required — the toolbar already has this logic.

**Independent Test**: Request the list page with `create_form_class = None` and `has_create_permission = True`; toolbar contains an `<a href="...">` button without `data-bs-toggle="modal"`.

- [ ] T014 [US2] Validate that US2 tests written in T002 now pass — `poetry run pytest tests/test_views/test_list_view.py::TestListViewInlineCreate -k "fallback" -v`

**Checkpoint**: User Story 2 verified — fallback link button behaviour confirmed by automated tests.

---

## Phase 5: User Story 3 — Permission Gate Hides Form (Priority: P3)

**Goal**: When `has_create_permission` is `False` (or a callable returning `False`), `create_form` is absent from context and no create button appears regardless of `create_form_class`.

**Independent Test**: Request the list page with `create_form_class` set and `has_create_permission = False`; `"create_form"` is absent from `response.context`; no create button in rendered HTML.

- [ ] T015 [US3] Validate that US3 tests written in T002 now pass — `poetry run pytest tests/test_views/test_list_view.py::TestListViewInlineCreate -k "permission" -v`

**Checkpoint**: User Story 3 verified — permission gating confirmed for both boolean and callable permission values.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Demo migration, E2E regression suite, full validation.

- [ ] T016 Remove manual `get_context_data` override from `ProductListView` in `demo/views.py` (the `create_form_class = ProductForm` and `has_create_permission = True` attributes already on the class drive the mixin automatically)
- [ ] T016a Validate T016 — `poetry run python manage.py check` · `poetry run pytest tests/test_views/test_list_view.py -x -q` (Constitution I: Django code change requires immediate check)
- [ ] T017 Playwright-cli verification — reload demo product list (`/products/`); assert: modal "Add new" button still present; modal opens; submitting a valid product form redirects browser back to `/products/` and the new product appears; assert: `?next=` parameter is honoured by `MVPCreateView`
- [ ] T018 [P] Write E2E Playwright tests in `tests/test_views/test_list_view_e2e.py` covering: modal opens on button click (US1); modal title is auto-derived (US1, FR-007); valid submit redirects back to list URL (US1, scenario 2); invalid submit lands on create page (US1, scenario 3); no modal button when permission denied (US3)
- [ ] T019 Run unit + integration suite (excluding E2E) — `poetry run pytest tests/ -q --ignore=tests/test_views/test_list_view_e2e.py` · `poetry run ruff check` · `poetry run djlint mvp/templates/ --check` — confirm zero new failures
- [ ] T019a Run E2E suite — `poetry run pytest tests/test_views/test_list_view_e2e.py -v` (requires running dev server at `localhost:8000`; ensure `poetry run python manage.py runserver` is active)

---

## Dependencies

```
T001
 └── T002 (baseline + failing tests)
      └── T003
           └── T004
                └── T005
                     └── T006 (docstring — commit alongside T005)
                          └── T007 (validate)
                               ├── T008
                               │    └── T009
                               │         └── T010
                               │              ├── T011
                               │              ├── T012 (Playwright — requires server)
                               │              └── T013 (validate)
                               │                   ├── T014 (US2 checkpoint)
                               │                   └── T015 (US3 checkpoint)
                               │                        └── T016
                               │                             └── T016a (validate)
                               │                                  └── T017 (Playwright)
                               │                                       ├── T018 (parallel — different file)
                               │                                       ├── T019 (unit suite)
                               │                                       └── T019a (E2E suite)
```

## Parallel Execution Opportunities

- **T006** (docstring update) should be committed in the same PR as T005 since it is in the same file. It is NOT marked `[P]` because it edits the same class — commit them together, not concurrently.
- **T018** (E2E tests) can be written in parallel with T017 (Playwright-cli verification) since they target the same behaviour but are in a different file.

## Implementation Strategy

**MVP Scope (Phase 2 + Phase 3 only)**:

- Implement `MVPListViewMixin` extension (T002–T007)
- Generalise `list_view.html` modal (T008–T013)
- Delivers US1 (core inline create workflow) + implicitly validates US2/US3 via tests

**Incremental Delivery**:

1. Phase 2 alone delivers testable, working mixin logic (all 3 stories covered in tests)
2. Phase 3 delivers the visible modal UI (US1 fully functional)
3. Phases 4–5 are checkpoint verifications (no new code)
4. Phase 6 cleans up the demo and adds the Playwright regression suite

## Format Validation

All tasks follow the required checklist format:

- ✅ Every task starts with `- [ ]`
- ✅ Every task has a sequential `T###` ID (T016a / T019a are inserted tasks)
- ✅ `[P]` marker on genuinely parallelisable tasks only (T018)
- ✅ `[US1]`/`[US2]`/`[US3]` labels on User Story phase tasks only
- ✅ Every task includes an exact file path or command
- ✅ Test class naming convention documented in preamble for T014/T015 selectors
- ✅ `manage.py check` present after every Django code change phase (T007, T013, T016a, T019)
