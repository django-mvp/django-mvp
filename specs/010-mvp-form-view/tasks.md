# Tasks: MVPFormView — Non-Model Form View

**Input**: Design documents from `specs/010-mvp-form-view/`
**Branch**: `010-mvp-form-view`
**Date**: 2026-05-04
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Research**: [research.md](research.md)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story label from spec.md (US1–US4)
- Setup/Foundational phases carry no story label

## Implementation Strategy

**MVP scope**: US2 (P1) — the only new code required for P1 stories.

**8 of 10 FRs are already satisfied** by the existing `MVPFormView` stub through inheritance.
Only two method additions are needed:

1. `get_success_message()` on `MVPFormView` — for US2 / FR-005
2. `get_page_title()` on `MVPFormView` — for US4 / FR-008

US1 and US3 are pre-existing (verified by 7 existing tests); their phases are
verification-only with no new implementation.

**Test-first discipline**: For every implementation task, write and observe the failing
test(s) before writing the implementation.

---

## Phase 1: Setup — Baseline Verification

**Purpose**: Confirm the starting state before any changes are made.

**No new files or dependencies are required.** `MVPFormView` already exists in
`mvp/views/edit.py` and is exported from `mvp/views/__init__.py`.

- [X] T001 Run `poetry run pytest tests/test_views/test_edit_view.py -v` and confirm all existing tests pass before any changes

---

## Phase 2: Foundational — US1 & US3 Pre-existing Behaviour Verified

**Purpose**: Confirm that the existing stub already satisfies US1 (basic form view) and
US3 (redirect chain) with no new implementation work required.

**⚠️ GATE**: This verification must pass before US2/US4 implementation begins.

**US1 pre-existing coverage** (7 tests already in `tests/test_views/test_edit_view.py`):

- `test_form_view_no_next_with_success_url` — FR-003 (US1 Scenario 2)
- `test_get_success_url_raises_improperly_configured` — FR-006 (US3 Scenario 3)
- `test_base_template_name` — FR-001 (US1 Scenario 1)
- `test_page_class` — FR-001 class attribute
- `test_form_view_no_next_with_success_url` (no `model` arg) — FR-007 (US1 Scenario 4)
- US3 next=list fallthrough test (`test_next_list_not_resolved_on_form_view`) — FR-004 (US3 Scenario 1)

**Note — US3 priority**: US3 is listed as P2 in spec.md. Its behaviour is delivered by
`MVPFormBase`/`NextURLMixin` from spec 008 (`008-safe-post-submit-redirect`). No new
code is required here; these tasks confirm the inherited behaviour is intact.

**Note — US2 end-to-end dispatch (C2)**: T004 tests the `get_success_message()` string
output directly. The full `SuccessMessageMixin` dispatch path (framework posting the
message after `form_valid()`) is covered by Django's own test suite and the inherited
mixin contract. An integration test asserting `messages.get_messages()` is not required
for this feature unless a regression is detected.

- [X] T002 Run `python manage.py check` and confirm zero system errors (pre-implementation gate)
- [X] T003 Confirm `from mvp.views import MVPFormView` works and `MVPFormView` is in `mvp/views/__init__.py __all__` — satisfies FR-009

**Checkpoint**: Foundation verified — US2 and US4 implementation can now begin.

---

## Phase 3: User Story 2 — Success Messages (Priority: P1) 🎯 MVP

**Goal**: `get_success_message()` on `MVPFormView` safely substitutes `%(field_name)s`
tokens from `cleaned_data` without injecting `%(verbose_name)s` and without raising
`KeyError` for unknown tokens.

**Independent Test**: A `MVPFormView` subclass with
`success_message = "Thanks, %(email)s!"` and `email` in `cleaned_data` returns
`"Thanks, user@example.com!"`. A message with `%(verbose_name)s` (not in `cleaned_data`)
returns `""` (empty string — substituted silently by `defaultdict(str)`).

**Acceptance Scenarios covered**: US2 Scenarios 1, 2, 3 (spec.md)

### Tests (write first — observe failing before implementing)

- [X] T004 [US2] Add `class TestMVPFormView` to `tests/test_views/test_edit_view.py` with 3 failing tests for `get_success_message()`:
  - `test_field_placeholder_substituted_from_cleaned_data` — `%(email)s` + `email` in `cleaned_data` → substituted
  - `test_unknown_placeholder_substitutes_empty_string` — `%(foo)s` absent from `cleaned_data` → `""`, no `KeyError`
  - `test_verbose_name_not_injected_substitutes_empty_string` — `%(verbose_name)s` → `""` (not an error; not injected)

### Implementation

- [X] T005 [US2] Implement `get_success_message(self, cleaned_data)` on `MVPFormView` in `mvp/views/edit.py`:
  - Use `defaultdict(str, cleaned_data)` — same pattern as `MVPModelFormBase.get_success_message()`
  - Do NOT inject `verbose_name` into the dict
  - Return `self.success_message % data` (or `""` when `success_message` is falsy)
  - Add full docstring explaining the difference from `MVPModelFormBase`

### Validation

- [X] T006 [US2] Run `python manage.py check` — must pass with zero errors
- [X] T007 [US2] Run `poetry run pytest tests/test_views/test_edit_view.py -v` — T004 tests must now pass; all pre-existing tests must still pass

---

## Phase 4: User Story 4 — Page Context System (Priority: P2)

**Goal**: `get_page_title()` on `MVPFormView` returns `page_title` when set, or derives a
readable default from the class name using `camel_case_to_spaces()` when `page_title` is
falsy.

**Independent Test**: A subclass named `ContactFormView` with no `page_title` attribute
renders `"Contact Form View"` as the page title. A subclass with `page_title = "My Form"`
renders `"My Form"`.

**Acceptance Scenarios covered**: US4 Scenarios 1 and 2 (spec.md)

### Tests (write first — observe failing before implementing)

- [X] T008 [US4] Add 2 failing tests to `class TestMVPFormView` in `tests/test_views/test_edit_view.py`:
  - `test_default_title_derived_from_class_name` — subclass named `ContactFormView`, no `page_title` → `"Contact Form View"`
  - `test_explicit_page_title_returned_as_is` — `page_title = "My Form"` → `"My Form"` (existing `PageMixin` behaviour preserved)

### Implementation

- [X] T009 [US4] Implement `get_page_title(self)` on `MVPFormView` in `mvp/views/edit.py`:
  - Import `from django.utils.text import camel_case_to_spaces` (add to module imports)
  - When `self.page_title` is truthy: return `str(self.page_title)` (delegate to `PageMixin`)
  - When `self.page_title` is falsy: return `camel_case_to_spaces(self.__class__.__name__).title()`
  - Add docstring documenting both paths and the `camel_case_to_spaces` usage

### Validation

- [X] T010 [US4] Run `python manage.py check` — must pass with zero errors
- [X] T011 [US4] Run `poetry run pytest tests/test_views/test_edit_view.py -v` — T008 tests must now pass; all prior tests must still pass

---

## Final Phase: Polish & Cross-Cutting Concerns

**Purpose**: Code quality, linting, and full-suite regression check.

- [X] T012 Run `poetry run ruff check mvp/views/edit.py tests/test_views/test_edit_view.py` and fix any violations
- [X] T013 Run `poetry run ruff format mvp/views/edit.py tests/test_views/test_edit_view.py` and confirm no diff
- [X] T014 Run the full test suite `poetry run pytest` and confirm zero failures

---

## Dependencies

```
T001 (baseline)
  └── T002 (manage.py check)
        └── T003 (export verification)
              └── T004 (write US2 tests — failing)
                    └── T005 (implement get_success_message)
                          ├── T006 (manage.py check)
                          └── T007 (pytest — US2 passes)
                                └── T008 (write US4 tests — failing)
                                      └── T009 (implement get_page_title)
                                            ├── T010 (manage.py check)
                                            └── T011 (pytest — US4 passes)
                                                  ├── T012 (ruff check)
                                                  ├── T013 (ruff format)
                                                  └── T014 (full pytest)
```

**No parallel opportunities**: all tasks are sequential due to test-first discipline
(each test must fail before its matching implementation is written) and the single-file
scope of changes.

---

## Parallel Execution Examples

Not applicable for this feature. The two implementation tasks (`T005`, `T009`) touch
the same file (`mvp/views/edit.py`) and must be sequenced to avoid merge conflicts
and to preserve the test-first discipline.

---

## Implementation Summary

| Phase | Tasks | User Story | New Code |
|-------|-------|-----------|---------|
| Setup | T001 | — | None |
| Foundational | T002–T003 | US1 + US3 (pre-existing) | None |
| US2 | T004–T007 | US2 (P1) | `get_success_message()` |
| US4 | T008–T011 | US4 (P2) | `get_page_title()` |
| Polish | T012–T014 | All | None |
| **Total** | **14** | **4 stories** | **2 methods, 5 tests** |

**Suggested MVP**: Complete through T007 (US2 only). US4 (`get_page_title`) is P2 and can
be deferred without breaking any P1 acceptance criteria.
