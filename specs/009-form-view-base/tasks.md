# Tasks: Form View Base Classes

**Input**: Design documents from `specs/009-form-view-base/`
**Prerequisites**: [plan.md](plan.md) · [spec.md](spec.md) · [research.md](research.md) · [data-model.md](data-model.md)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to ([US1], [US2], [US3])
- Exact file paths in descriptions

---

## Phase 1: Setup (Baseline Verification)

**Purpose**: Confirm the existing implementation is green before making any changes.
This feature has two targeted code changes and seven new tests; all existing tests
must pass before work begins.

- [x] T001 Run `poetry run pytest tests/test_views/test_edit_view.py -q --tb=short` and record the passing count as the baseline in `tests/test_views/test_edit_view.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No new infrastructure is required. Eight of ten FRs are already satisfied
by the existing implementation. The two gaps (FR-007 and FR-008) are addressed per user
story below. Proceed directly to user story phases.

*(No tasks — skip to Phase 3)*

---

## Phase 3: User Story 1 — Subclass a Form View and Get Layout, Redirects, and Messages for Free (Priority: P1) 🎯 MVP

**Goal**: Explicit tests document the already-complete layout and baseline redirect
contracts (`base_template_name`, `page_class`, `ImproperlyConfigured` for `MVPFormBase`)
so these class-level contracts are regression-protected.

**Independent Test**: A `TestMVPFormBase` class in `tests/test_views/test_edit_view.py`
with three passing tests that describe the observable contract without any implementation
changes.

### Tests for User Story 1

> **NOTE**: These tests document existing behavior. They should pass immediately.
> Add them to `tests/test_views/test_edit_view.py` in a new `TestMVPFormBase` class.

- [x] T002 [P] [US1] Write test T-FM-006 asserting `MVPFormBase.base_template_name == "form_view.html"` in `tests/test_views/test_edit_view.py`
- [x] T003 [P] [US1] Write test T-FM-007 asserting `MVPFormBase.page_class == "mvp-form-page"` in `tests/test_views/test_edit_view.py`
- [x] T004 [US1] Write test T-FM-005 asserting `MVPFormBase.get_success_url()` raises `ImproperlyConfigured` when neither `next` parameter nor `success_url` is configured, in `tests/test_views/test_edit_view.py`
- [x] T005 [US1] Run `poetry run pytest tests/test_views/test_edit_view.py -q --tb=short -k "TestMVPFormBase"` and confirm T-FM-005, T-FM-006, T-FM-007 all pass

**Checkpoint**: US1 attribute contracts are regression-protected. All three new tests pass.

---

## Phase 4: User Story 2 — Success Messages on Model Forms Automatically Name the Model (Priority: P1)

**Goal**: Fix FR-007 gap — `MVPModelFormBase.get_success_message()` raises `KeyError`
when `success_message` contains field-value placeholders (e.g. `%(name)s`) and
`cleaned_data` is absent (delete views). Fix by wrapping with `defaultdict(str, ...)`.

**Independent Test**: A `TestGetSuccessMessage` class in `tests/test_views/test_edit_view.py`
with three tests: T-FM-001 passes before the fix (documents existing behavior), T-FM-002
must FAIL before the fix (confirms the bug), T-FM-003 may or may not pass depending on
test fixture. All three must pass after the fix.

### Tests for User Story 2

> **NOTE**: Write T-FM-001, T-FM-002, T-FM-003 first, then run to observe T-FM-002 FAIL.
> Then implement the fix and confirm all three pass.

- [x] T006 [P] [US2] Write test T-FM-001 asserting `get_success_message({})` with `success_message = "%(verbose_name)s created."` returns `"<verbose_name> created."` using a create view fixture, in `tests/test_views/test_edit_view.py`
- [x] T007 [P] [US2] Write test T-FM-002 asserting `get_success_message({})` with `success_message = "%(verbose_name)s %(name)s deleted."` returns `"<verbose_name>  deleted."` (empty string for `%(name)s`) without raising an error, in `tests/test_views/test_edit_view.py`
- [x] T008 [P] [US2] Write test T-FM-003 asserting `get_success_message({"name": "Widget A"})` with `success_message = "%(verbose_name)s %(name)s updated."` returns `"<verbose_name> Widget A updated."`, in `tests/test_views/test_edit_view.py`
- [x] T009 [US2] Run `poetry run pytest tests/test_views/test_edit_view.py -q --tb=short -k "TestGetSuccessMessage"` and confirm T-FM-002 **fails** (KeyError raised) before implementing the fix

### Implementation for User Story 2

- [x] T010 [US2] Add `from collections import defaultdict` import at the top of `mvp/views/edit.py` (if not already present)
- [x] T011 [US2] Replace the plain dict interpolation in `MVPModelFormBase.get_success_message()` with `defaultdict(str, cleaned_data)` per the plan.md Change 1 design in `mvp/views/edit.py`
- [x] T012 [US2] Run `python manage.py check` (no errors) then `poetry run pytest tests/test_views/test_edit_view.py -q --tb=short` and confirm T-FM-001, T-FM-002, T-FM-003 all pass (baseline + 6)

**Checkpoint**: US2 is fully functional. `%(verbose_name)s` interpolates on all model form
views; missing field placeholders silently produce `""` on delete views.

---

## Phase 5: User Story 3 — Redirect Destination Resolves Through a Predictable Priority Chain (Priority: P2)

**Goal**: Fix FR-008 gap — `MVPModelFormBase.get_success_url()` currently returns `None`
when `resolve_crud_url("list")` cannot resolve a list URL (no `crud_views` configured, no
`success_url` set). This causes a cryptic crash inside Django's redirect machinery. Fix by
raising `ImproperlyConfigured` with a clear message, symmetric with FR-005.

**Existing coverage note**: US3 acceptance scenarios 1, 2, and 5 (redirect priority chain —
`next` wins, `success_url` wins, post-create pk) are already covered by the baseline 35-test
suite per research.md (FR-004, FR-006, FR-009 — all complete). Only scenario 4 (clear error
when list URL unresolvable) requires a new task.

**Independent Test**: A test in `tests/test_views/test_edit_view.py` that asserts
`get_success_url()` raises `ImproperlyConfigured` (not `NoReverseMatch` or `AttributeError`)
when the list URL is unresolvable. Must FAIL before the fix, PASS after.

### Tests for User Story 3

> **NOTE**: Write T-FM-004 first, run to confirm it FAILS, then implement the fix.

- [x] T013 [US3] Write test T-FM-004 asserting `MVPModelFormBase.get_success_url()` raises `ImproperlyConfigured` (not `None`) when `resolve_crud_url("list")` cannot resolve and no `success_url` is set, in `tests/test_views/test_edit_view.py`
- [x] T014 [US3] Run `poetry run pytest tests/test_views/test_edit_view.py -q --tb=short -k "T_FM_004 or test_get_success_url"` and confirm T-FM-004 **fails** before implementing the fix

### Implementation for User Story 3

- [x] T015 [US3] Update `MVPModelFormBase.get_success_url()` to raise `ImproperlyConfigured` when `resolve_crud_url("list")` returns `None`, per the plan.md Change 2 design in `mvp/views/edit.py`
- [x] T016 [US3] Run `python manage.py check` (no errors) then `poetry run pytest tests/test_views/test_edit_view.py -q --tb=short` and confirm T-FM-004 passes (baseline + 7)

**Checkpoint**: US3 is fully functional. All three user stories complete.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Docstring updates for changed methods, final full-suite validation, and
quickstart walkthrough.

- [x] T017 [P] Update docstring on `MVPModelFormBase.get_success_message()` to document the `defaultdict(str)` behavior and the `%(verbose_name)s` guarantee in `mvp/views/edit.py`
- [x] T018 [P] Update docstring on `MVPModelFormBase.get_success_url()` to document the `ImproperlyConfigured` raise when list URL is unresolvable in `mvp/views/edit.py`
- [x] T019 Run `python manage.py check` and confirm no Django system check errors
- [x] T020 Run `poetry run pytest tests/test_views/ -q --tb=short` and confirm full test suite passes (42 tests minimum)
- [ ] T021 Walk through `specs/009-form-view-base/quickstart.md` scenarios manually and confirm each example behaves as documented

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Empty — no blocking prerequisites
- **Phase 3 (US1)**: Depends on Phase 1 baseline confirmation
- **Phase 4 (US2)**: Depends on Phase 1; can start in parallel with Phase 3
- **Phase 5 (US3)**: Depends on Phase 1; can start in parallel with Phase 3 and Phase 4
- **Phase 6 (Polish)**: Depends on Phase 3, 4, and 5 completion

### User Story Dependencies

- **US1 (P1)**: Independent — documents existing behavior only
- **US2 (P1)**: Independent — isolated to `get_success_message()` in `mvp/views/edit.py`
- **US3 (P2)**: Independent — isolated to `get_success_url()` in `mvp/views/edit.py`

US2 and US3 both modify `mvp/views/edit.py` but different methods — can be authored in
parallel by different contributors, but should be merged and validated sequentially
(T012 before T016).

### Within Each User Story

- Tests MUST be written before implementation
- For US2: T-FM-002 MUST be observed failing before T010–T011 are implemented
- For US3: T-FM-004 MUST be observed failing before T015 is implemented
- For US1: Tests should pass immediately (existing behavior) — no failure step needed

---

## Parallel Opportunities

### Phase 3 (US1): T002 and T003 can run in parallel
```
Agent A: T002 — Write test T-FM-006 (base_template_name)
Agent B: T003 — Write test T-FM-007 (page_class)
→ Then both: T004 — Write test T-FM-005 (ImproperlyConfigured)
→ Then: T005 — Run US1 tests
```

### Phase 4 (US2): T006, T007, T008 can run in parallel
```
Agent A: T006 — Write T-FM-001
Agent B: T007 — Write T-FM-002
Agent C: T008 — Write T-FM-003
→ All agents: T009 — Run to confirm T-FM-002 fails
→ Sequential: T010 → T011 → T012
```

### Phase 6 (Polish): T017 and T018 can run in parallel
```
Agent A: T017 — Docstring for get_success_message()
Agent B: T018 — Docstring for get_success_url()
→ Then: T019 → T020 → T021
```

---

## Implementation Strategy

**MVP Scope**: Phase 3 + Phase 4 (US1 + US2)
- T002–T012: 11 tasks, one file changed (`mvp/views/edit.py`), one file extended (`tests/test_views/test_edit_view.py`)
- Delivers: regression-protected attribute contracts + correct success message interpolation

**Full Scope**: All phases (T001–T021, 21 tasks total)
- Adds US3 (FR-008 fix) and polish (docstrings, final validation)
- Both code changes touch different methods in the same file — no merge conflicts

**Test Count Progression**:
- Baseline: recorded in T001
- After Phase 3 (US1): baseline + 3
- After Phase 4 (US2): baseline + 6
- After Phase 5 (US3): baseline + 7
