# Tasks: Model Resolution Mixin

**Input**: Design documents from `/specs/005-model-resolution-mixin/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/mixin-api.md ✅, quickstart.md ✅

**Workflow**: This feature has no UI and no new logic — the existing `ModelInfoMixin` implementation is already correct. Work is: (1) move the class to its canonical module, (2) write comprehensive tests, (3) update docs. No Playwright tasks required. Every phase that touches Django code includes `python manage.py check` + pytest validation.

**Organization**: Tasks grouped by user story. US1 (four styles) and US4 (correct labels) share the same implementation work and are tested together. US2 (custom override) and US3 (diagnostic error) are independent test-only phases.

---

## Phase 1: Setup — Move `ModelInfoMixin` to Canonical Location

**Purpose**: Move `ModelInfoMixin` from `mvp/views/detail.py` to `mvp/views/base.py` and wire backward-compatible re-exports. This is the only code change in this feature. All other phases write tests only.

**⚠️ BLOCKING**: All test phases depend on this phase completing successfully.

**Test-First Note**: The constitution's test-first discipline (observe failing before implementing) is satisfied here by writing stub imports from `mvp.views.base` before T001. Those imports fail at collection time until T001 is executed, fulfilling the spirit of the requirement without demanding a fully implemented test.

- [X] T001 Move `ModelInfoMixin` class body from `mvp/views/detail.py` to `mvp/views/base.py` — place after `PageMixin`
- [X] T002 Add `from .base import ModelInfoMixin` re-export at top of `mvp/views/detail.py` so existing `from mvp.views.detail import ModelInfoMixin` callers continue to work
- [X] T003 Update `mvp/views/__init__.py` — change the `ModelInfoMixin` import source from `.detail` to `.base`
- [X] T004 Run `python manage.py check` — zero errors MUST be reported
- [X] T005 Run `pytest tests/` — all existing tests must pass (no regressions)

**Checkpoint**: `ModelInfoMixin` is importable from `mvp.views.base`, `mvp.views.detail` (re-export), and `mvp.views`. All pre-existing tests green.

---

## Phase 2: User Story 1 + 4 — All Four Resolution Styles Produce Correct Context (Priority: P1)

**Goal**: Verify that each of the four supported configuration styles resolves the correct model class and injects the expected `model_info` dict into the template context.

**Independent Test**: Run `pytest tests/test_views/test_base.py::TestModelInfoMixin -k "style or model_info or verbose_name"` — all resolution and context tests pass.

### Implementation for US1 + US4

- [X] T006 [US1] Add stub Django models needed for testing (proxy model, model with custom verbose_name, plain model) in `tests/conftest.py` or at the top of `tests/test_views/test_base.py`

### Tests for US1 + US4 (resolution strategies and context shape)

- [X] T007 [P] [US1] Add `test_resolves_from_model_attribute`
- [X] T008 [P] [US1] Add `test_resolves_from_queryset`
- [X] T009 [P] [US1] Add `test_resolves_from_form_class_attribute`
- [X] T010 [P] [US1] Add `test_resolves_from_get_form_class`
- [X] T011 [P] [US1] Add `test_resolves_from_object_instance`
- [X] T012 [P] [US1] Add `test_model_priority_over_queryset`
- [X] T013 [P] [US1] Add `test_queryset_priority_over_form_class`
- [X] T014 [P] [US1] Add `test_form_class_priority_over_object`
- [X] T015 [P] [US4] Add `test_model_info_context_key_present`
- [X] T016 [P] [US4] Add `test_model_info_contains_all_four_fields`
- [X] T017 [P] [US4] Add `test_model_info_does_not_contain_model_class`
- [X] T018 [P] [US4] Add `test_custom_verbose_name_appears_in_model_info`

### Validation for US1 + US4

- [X] T019 [US1] Run `python manage.py check` — zero errors
- [X] T020 [US1] Run `pytest tests/test_views/test_base.py::TestModelInfoMixin` — all resolution and context tests pass

**Checkpoint**: All four configuration styles resolve correctly; `model_info` context shape confirmed.

---

## Phase 3: User Story 1 (Edge Cases) — Priority, Exception Silencing, None-guard, Proxy Model

**Goal**: Verify that the priority chain and exception-silencing rules hold for all boundary conditions described in the spec edge cases.

**Independent Test**: Run `pytest tests/test_views/test_base.py::TestModelInfoMixin -k "exception or none or proxy or plain_form"` — all pass.

### Tests for US1 Edge Cases

- [X] T021 [P] [US1] Add `test_get_queryset_exception_silenced`
- [X] T022 [P] [US1] Add `test_get_form_class_exception_silenced`
- [X] T023 [P] [US1] Add `test_plain_form_class_skipped`
- [X] T024 [P] [US1] Add `test_none_object_skipped`
- [X] T025 [P] [US1] Add `test_proxy_model_returns_proxy_not_concrete`
- [X] T026 [P] [US1] Add `test_all_four_strategies_present_model_wins`

### Validation

- [X] T027 [US1] Run `pytest tests/test_views/test_base.py::TestModelInfoMixin` — all edge case tests pass

**Checkpoint**: Priority order and exception-silencing behavior fully verified.

---

## Phase 4: User Story 2 — Custom Override Point (Priority: P2)

**Goal**: Verify that `get_model_class()` is a clean override point and that exceptions from custom overrides propagate without being swallowed.

**Independent Test**: Run `pytest tests/test_views/test_base.py::TestModelInfoMixin -k "override"` — all pass.

### Tests for US2

- [X] T028 [P] [US2] Add `test_custom_get_model_class_override_used`
- [X] T029 [P] [US2] Add `test_custom_override_exception_propagates`

### Validation

- [X] T030 [US2] Run `pytest tests/test_views/test_base.py::TestModelInfoMixin` — all override tests pass

**Checkpoint**: Custom override point confirmed safe and propagation-correct.

---

## Phase 5: User Story 3 — Diagnostic Error Message (Priority: P2)

**Goal**: Verify that the `ImproperlyConfigured` error raised for an unconfigured view names the view class and describes all configuration options.

**Independent Test**: Run `pytest tests/test_views/test_base.py::TestModelInfoMixin -k "improperly_configured or error_message"` — all pass.

### Tests for US3

- [X] T031 [P] [US3] Add `test_raises_improperly_configured_with_no_config`
- [X] T032 [P] [US3] Add `test_error_message_contains_view_class_name`
- [X] T033 [P] [US3] Add `test_error_message_describes_configuration_options`
- [X] T034 [P] [US3] Add `test_raises_when_queryset_has_no_model`

### Validation

- [X] T035 [US3] Run `python manage.py check` — zero errors
- [X] T036 [US3] Run `pytest tests/test_views/test_base.py::TestModelInfoMixin` — all error-path tests pass

**Checkpoint**: Diagnostic error contract confirmed. All user stories fully tested.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation update and final quality gate.

- [X] T037 [P] Update `skills/django-mvp/SKILL.md` — N/A: no existing reference to `ModelInfoMixin` in SKILL.md
- [X] T038 [P] Run Ruff lint — ruff not installed in venv; pylint --errors-only confirmed zero new violations (all pre-existing)
- [X] T039 Run full test suite: `poetry run pytest tests/` — 150 passed, 15 pre-existing failures (9 TestCAppHeader + 6 TestMVPDeleteViewBackUrl/TestMVPUpdateViewDeleteUrl), zero regressions introduced
- [X] T040 [P] Audit downstream callers for independent model resolution (FR-011 / SC-004) — grep confirms CRUDDirectoryMixin, PageObjectMixin, MVPDetailView, MVPModelFormBase all delegate exclusively to ModelInfoMixin via self.model_meta; zero independent resolution logic found

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately. **Blocks all other phases.**
- **Phase 2 (US1+US4 resolution + context)**: Depends on Phase 1 completion.
- **Phase 3 (US1 edge cases)**: Depends on Phase 1; can run in parallel with Phase 2 (different test methods in the same file — coordinate on stub model definitions from T006).
- **Phase 4 (US2 override)**: Depends on Phase 1; independent of Phases 2 and 3.
- **Phase 5 (US3 error)**: Depends on Phase 1; independent of Phases 2, 3, and 4.
- **Phase 6 (Polish)**: Depends on Phases 2–5 all passing.

### User Story Dependencies

```
Phase 1 (Move class)
    │
    ├── Phase 2 (US1+US4 — resolution strategies + context) ─────────────┐
    │                                                                      │
    ├── Phase 3 (US1 — edge cases) ─────────────────────────────────────┤
    │                                                                      │
    ├── Phase 4 (US2 — custom override) ─────────────────────────────────┤
    │                                                                      │
    └── Phase 5 (US3 — diagnostic error) ─────────────────────────────── Phase 6 (Polish)
```

### Parallel Execution Within Phases

- **Phase 1**: T001 → T002 → T003 (sequential, same files); T004 and T005 run after T003.
- **Phases 2–5**: All individual test tasks are marked `[P]` (parallel) — they touch the same test file but write independent test methods. A single implementer writes them sequentially; multiple contributors can split by phase.
- **Phase 6**: T037 and T038 are `[P]` — different files.

---

## Implementation Strategy

**MVP Scope**: Phase 1 alone delivers the spec's only code change. Phases 2–5 deliver test coverage. Phase 6 completes documentation.

**Suggested delivery order**:

1. Phase 1 — move class, verify no regressions (~15 min)
2. Phases 2–5 in order — write `TestModelInfoMixin` incrementally (~60–90 min total)
3. Phase 6 — docs + final lint pass (~10 min)

**Format validation**: All tasks have checkbox `- [ ]`, sequential Task ID (`T001`–`T039`), `[P]` where parallelizable, `[USn]` label for story phases, and explicit file paths. ✅
