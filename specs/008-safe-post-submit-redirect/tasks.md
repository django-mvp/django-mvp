---
description: "Task list for Safe Post-Submit Redirect"
---

# Tasks: Safe Post-Submit Redirect

**Propagated**: 2026-05-04 — Updated from spec.md refinement (FR-001a: `get_next_candidate()` override point)

**Input**: Design documents from `/specs/008-safe-post-submit-redirect/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Workflow**: Gap-filling approach — existing `NextURLMixin` code already satisfies FR-001 through FR-005a, FR-007, FR-008, FR-010, FR-011. This task list targets the 5 identified gaps: FR-001a (`get_next_candidate()` override point), FR-005b (DEBUG logging), FR-006 (shorthand in all form views), FR-009 (`success_url` priority step), FR-012 (shorthand preserved on re-render). Implementation precedes tests in Phases 3 and 6 (explicit TDD exception: changes are small, targeted, fully described by `contracts/next-url-mixin.md`, and the risk of design churn is negligible). Use `RequestFactory` for unit tests, `Client` for integration. Every phase that touches `mvp/views/edit.py` must run `python manage.py check`.

**MVP Scope**: Phase 1 + Phase 2 + Phase 3 (US4) + Phase 4 (US1) + Phase 5 (US2) — all P1 stories.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no unresolved dependencies)
- **[Story]**: User story label — US1 through US5

---

## Phase 1: Setup

**Purpose**: Create the test file skeleton before any implementation begins.

- [X] T001 Create `tests/test_views/test_edit_view.py` — empty module with standard imports (`pytest`, `RequestFactory`, `override_settings`) and a brief module docstring referencing `mvp/views/edit.py`

---

## Phase 2: Foundational

**Purpose**: Add the logging infrastructure that all subsequent phases depend on.

**⚠️ CRITICAL**: Phase 3 (US4 — FR-005b) cannot begin until this is complete.

- [X] T002 Add `import logging` and `logger = logging.getLogger(__name__)` at module level in `mvp/views/edit.py` (below existing imports, above `class NextURLMixin`)
- [X] T002a [FR-001a] Add `get_next_candidate()` method to `NextURLMixin` in `mvp/views/edit.py` — returns `self.request.POST.get("next")` on POST and `self.request.GET.get("next")` on GET; gives subclasses a single override point for the candidate source without reimplementing validation
- [X] T002b [FR-001a] Refactor `NextURLMixin.get_next_url()` to call `candidate = self.get_next_candidate()` instead of duplicating the POST/GET read inline
- [X] T002c [FR-001a] Refactor `MVPFormBase.get_next_url()`, `MVPFormBase.get_context_data()`, and `MVPFormBase.get_success_url()` to call `self.get_next_candidate()` wherever they currently read `self.request.POST.get("next")` or `self.request.GET.get("next")` directly
- [X] T002d [P] [FR-001a] Test `get_next_candidate()` directly — `tests/test_views/test_edit_view.py`: (a) POST request with `next=foo` returns `"foo"`; (b) GET request with `?next=bar` returns `"bar"`; (c) absent `next` returns `None`; (d) POST request reads POST body, not query string
- [X] T003 Run `python manage.py check` — zero errors MUST be reported

**Checkpoint**: Logger available — US4 implementation can begin.

---

## Phase 3: User Story 4 — Open-Redirect Protection (Priority: P1) 🎯 MVP

**Goal**: Developers see a `logger.warning` in their Django logs when a `next` value is rejected due to unsafe URL, helping diagnose misconfigured links without exposing anything in production.

**Independent Test**: Submit a form with `next=https://evil.com/` — with `DEBUG=True` a warning is logged; with `DEBUG=False` nothing is logged. The response never redirects to `evil.com` in either case.

### Implementation for User Story 4

- [X] T004 [US4] In `NextURLMixin.get_next_url()` in `mvp/views/edit.py`: after the `url_has_allowed_host_and_scheme` check returns `False`, add `from django.conf import settings` import (top of file) and emit `logger.warning("next parameter %r rejected (unsafe or cross-origin); falling back to default destination.", candidate)` guarded by `if candidate and settings.DEBUG and not (hasattr(self, "crud_views") and candidate in self.crud_views)` — the extra guard suppresses false-positive warnings for recognized CRUD shorthands (e.g., `"list"`) that fail URL validation but will be resolved later in `get_success_url()`

### Tests for User Story 4

- [X] T005 [P] [US4] Test: `get_next_url()` with `next=https://evil.com/` logs a warning when `DEBUG=True` (use `pytest.warns` or `caplog`) — `tests/test_views/test_edit_view.py`
- [X] T006 [P] [US4] Test: `get_next_url()` with `next=https://evil.com/` emits NO log when `DEBUG=False` — `tests/test_views/test_edit_view.py` *(see also T040 — related scenario from fallback-chain angle)*
- [X] T007 [P] [US4] Test: `get_next_url()` with `next=javascript:alert(1)` logs a warning in `DEBUG=True` — `tests/test_views/test_edit_view.py`
- [X] T008 [P] [US4] Test: `get_next_url()` with `next=//evil.com/path` logs a warning in `DEBUG=True` — `tests/test_views/test_edit_view.py`
- [X] T009 [P] [US4] Test: absent `next` parameter emits NO log even when `DEBUG=True` — `tests/test_views/test_edit_view.py`
- [X] T010 [P] [US4] Test: empty-string `next` emits NO log even when `DEBUG=True` — `tests/test_views/test_edit_view.py`
- [X] T010a [P] [US4] Test: `get_next_url()` with `next=list` (recognized CRUD shorthand) emits NO warning even when `DEBUG=True` — shorthands are not unsafe URLs, they are valid inputs resolved downstream — `tests/test_views/test_edit_view.py`

### Story 4 Validation

- [X] T011 [US4] Run `python manage.py check` — zero errors MUST be reported
- [X] T012 [US4] Run `pytest tests/test_views/test_edit_view.py` — all pass

**Checkpoint**: US4 fully functional and tested. Security protection is verified.

---

## Phase 4: User Story 1 — Chain Form Views with a URL Destination (Priority: P1) 🎯 MVP

**Goal**: Tests confirm the existing URL-validation behaviour that already satisfies FR-001 through FR-005a, FR-010, FR-011. No new code required in this phase.

**Independent Test**: GET with `?next=/records/` → `next_url` in context is `/records/`. POST with `next=/records/` → `get_next_url()` returns `/records/`.

### Tests for User Story 1

- [X] T013 [P] [US1] Test: `get_next_url()` on GET request with `?next=/safe/path/` returns `"/safe/path/"` — `tests/test_views/test_edit_view.py`
- [X] T013a [P] [US1] Test: subclass overrides `get_next_candidate()` to return a fixed value — verify `get_next_url()` and `get_context_data()` use the overridden value, not the request directly; confirms FR-001a hook works — `tests/test_views/test_edit_view.py`
- [X] T014 [P] [US1] Test: `get_next_url()` on POST request with `next=/safe/path/` in POST data returns `"/safe/path/"` — `tests/test_views/test_edit_view.py`
- [X] T015 [P] [US1] Test: POST `next` value takes precedence when both POST data and GET query string contain `next` — `tests/test_views/test_edit_view.py`
- [X] T016 [P] [US1] Test: `get_context_data()` on GET injects `next_url` into template context with the validated URL — `tests/test_views/test_edit_view.py`
- [X] T017 [P] [US1] Test: `next_url` is `None` in context when `next` is absent from the request — `tests/test_views/test_edit_view.py`
- [X] T018 [P] [US1] Test: `next_url` is `None` in context when `next` is an empty string — `tests/test_views/test_edit_view.py`
- [X] T019 [P] [US1] Test: `get_next_url()` returns `None` (not empty string) for an absent `next` parameter — `tests/test_views/test_edit_view.py`

### Story 1 Validation

- [X] T020 [US1] Run `pytest tests/test_views/test_edit_view.py` — all pass

**Checkpoint**: US1 fully covered. Existing redirect-by-URL behaviour is locked in with tests.

---

## Phase 5: User Story 2 — Redirected Back to the Right Place (Priority: P1) 🎯 MVP

**Goal**: End-to-end test confirms the complete user journey: click a "Create" link that embeds `?next=<url>`, submit the form, land back at the correct page — with no custom view code required.

**Independent Test**: Playwright test navigates to the demo create view with `?next=/demo/records/`, submits a valid form, and asserts the final URL is `/demo/records/`.

### Tests for User Story 2

- [X] T021 [US2] Create `tests/test_views/test_edit_view_e2e.py` — Playwright E2E test file with marker `@pytest.mark.e2e`
- [X] T021a [US2] Update the demo app's create/update form template to include `{% if next_url %}<input type="hidden" name="next" value="{{ next_url }}">{% endif %}` — required for `next_url` to be present in POST data on submission, without which T022/T023 and T035a/T035b will fail; check `demo/templates/` for the relevant base form template
- [X] T022 [US2] In `tests/test_views/test_edit_view_e2e.py`: test that navigating to the demo create URL with `?next=/demo/records/`, submitting a valid form, results in a final page URL of `/demo/records/` — asserts the full round-trip redirect
- [X] T023 [US2] In `tests/test_views/test_edit_view_e2e.py`: test that a failed form submission (e.g., blank required field) re-renders the form with `next_url` still present as a hidden field, so the destination is preserved for retry
- [ ] T024 [US2] Run `pytest tests/test_views/test_edit_view_e2e.py -m e2e` — all pass

**Checkpoint**: US1 + US2 + US4 verified. MVP is complete and ready to demo.

---

## Phase 6: User Story 3 — CRUD Action Shorthand Destinations (Priority: P2)

**Goal**: Developers can pass `?next=list`, `?next=detail`, or any registered CRUD action name. All form views attempt resolution; shorthands survive failed POST re-renders unchanged in the template context.

**Independent Test**: `MVPCreateView` with POST `next=list` → redirects to list URL. POST `next=detail` after creation → redirects to the new object's detail URL. Failed POST with `next=list` → re-rendered form still has `next_url = "list"` in context.

### Implementation for User Story 3

> **Implement first; tests follow.**

- [X] T025 [US3] Add `MVPFormBase.get_success_url()` to `mvp/views/edit.py` — three-step chain: (1) `if next_url := self.get_next_url(): return next_url`, (2) shorthand attempt guarded by `if hasattr(self, "crud_views")` — reads `self.request.POST.get("next")`, checks `next_key in self.crud_views`, calls `self.resolve_crud_url(next_key)`; if resolution returns a falsy result (URL pattern missing, permission denied), emit `logger.warning("next shorthand %r could not be resolved; falling back to default destination.", next_key)` guarded by `settings.DEBUG`; if `next_key` is not in `crud_views`, skip silently (not a developer error); (3) `return super().get_success_url()`
- [X] T026 [US3] Replace `MVPModelFormBase.get_success_url()` in `mvp/views/edit.py` with a minimal override that wraps `super().get_success_url()` in `try/except ImproperlyConfigured` and falls back to `self.resoluve_crud_url("list")` — the URL and shorthand logic is now inherited from `MVPFormBase`
- [X] T027 [US3] Add shorthand-preservation to `get_context_data()` in `MVPFormBase` in `mvp/views/edit.py` — after `super().get_context_data()` sets `context["next_url"]`, if `context["next_url"] is None`: read raw `next` from POST (on POST) or GET (on GET); if raw value is truthy and `hasattr(self, "crud_views")` and `raw in self.crud_views`, set `context["next_url"] = raw`

### Tests for User Story 3

- [X] T028 [P] [US3] Test: `MVPCreateView` POST with `next=list` → `get_success_url()` returns the list URL — `tests/test_views/test_edit_view.py`
- [X] T029 [P] [US3] Test: `MVPCreateView` POST with `next=detail` → `get_success_url()` returns the new object's detail URL — `tests/test_views/test_edit_view.py`
- [X] T030 [P] [US3] Test: `MVPUpdateView` POST with `next=update` → `get_success_url()` returns the update URL — `tests/test_views/test_edit_view.py`
- [X] T031 [P] [US3] Test: unrecognised shorthand (e.g., `next=foobar`) falls through silently to `success_url` — `tests/test_views/test_edit_view.py`
- [X] T032 [P] [US3] Test: `get_context_data()` with POST `next=list` → `context["next_url"]` is `"list"` (shorthand preserved on re-render) — `tests/test_views/test_edit_view.py`
- [X] T033 [P] [US3] Test: `get_context_data()` with GET `?next=detail` → `context["next_url"]` is `"detail"` (shorthand injected on initial render) — `tests/test_views/test_edit_view.py`
- [X] T034 [P] [US3] Test: `MVPFormView` (no `crud_views`) with POST `next=list` → shorthand silently skipped, falls through to `super().get_success_url()` which uses `success_url` — `tests/test_views/test_edit_view.py`
- [X] T035 [P] [US3] Test: `MVPDeleteView` POST with `next=list` → still uses its own `get_success_url()` override (no regression) — `tests/test_views/test_edit_view.py`
- [X] T035a [US3] In `tests/test_views/test_edit_view_e2e.py`: E2E test — navigate to demo create URL with `?next=list`, submit valid form, assert final URL matches the model's list URL (Playwright; `@pytest.mark.e2e`) — required by Constitution §VIII and SC-003
- [X] T035b [US3] In `tests/test_views/test_edit_view_e2e.py`: E2E test — navigate to demo create URL with `?next=detail`, submit valid form, assert final URL matches the newly created object's detail URL (Playwright; `@pytest.mark.e2e`) — required by Constitution §VIII

### Story 3 Validation

- [X] T036 [US3] Run `python manage.py check` — zero errors MUST be reported
- [X] T037 [US3] Run `pytest tests/test_views/test_edit_view.py` — all pass

**Checkpoint**: US3 fully functional and tested. CRUD shorthand round-trips work end-to-end.

---

## Phase 7: User Story 5 — Graceful Fallback (Priority: P2)

**Goal**: Tests confirm the full priority chain (validated URL → shorthand → `success_url` → `c`) by exercising each step as the fallback of the one before it. Implementation was delivered in T025–T026.

**Independent Test**: No `next` param + `success_url` set → redirects to `success_url`. No `next` + no `success_url` on model form → redirects to list URL. `next=garbage` → falls through to `success_url`.

### Tests for User Story 5

- [X] T038 [P] [US5] Test: `MVPCreateView` POST with no `next` and `success_url = "/done/"` → `get_success_url()` returns `"/done/"` — `tests/test_views/test_edit_view.py`
- [X] T039 [P] [US5] Test: `MVPCreateView` POST with no `next` and no `success_url` → `get_success_url()` returns `resoluve_crud_url("list")` result — `tests/test_views/test_edit_view.py`
- [X] T040 [P] [US5] Test: `MVPCreateView` POST with `next=https://evil.com/` (rejected) and `success_url = "/done/"` → `get_success_url()` returns `"/done/"` — `tests/test_views/test_edit_view.py`
- [X] T041 [P] [US5] Test: `MVPCreateView` POST with `next=` (empty string) and `success_url = "/done/"` → returns `"/done/"` — `tests/test_views/test_edit_view.py`
- [X] T042 [P] [US5] Test: `MVPFormView` (no model) POST with no `next` and `success_url = "/done/"` → `get_success_url()` returns `"/done/"` without raising — `tests/test_views/test_edit_view.py`
- [X] T043 [US5] Run `pytest tests/test_views/test_edit_view.py` — all pass

**Checkpoint**: All 5 user stories are independently functional and fully tested.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Documentation updates and final validation.

- [X] T044 [P] Update docstring on `NextURLMixin.get_next_url()` in `mvp/views/edit.py` — note the `settings.DEBUG` logging behaviour
- [X] T045 [P] Update docstring on `MVPFormBase.get_success_url()` in `mvp/views/edit.py` — document the three-step priority chain
- [X] T046 [P] Update docstring on `MVPModelFormBase.get_success_url()` in `mvp/views/edit.py` — document the four-step priority chain with `resoluve_crud_url("list")` fallback
- [X] T047 [P] Update `skills/django-mvp/SKILL.md` — add a section on `NextURLMixin` usage, `?next=` parameter, and CRUD shorthands
- [ ] T048 Run `quickstart.md` developer scenarios manually to verify examples match the implemented behaviour — `specs/008-safe-post-submit-redirect/quickstart.md`
- [X] T049 Run full test suite `pytest tests/` — all pass, zero regressions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1
- **US4 (Phase 3)**: Depends on Phase 2 (needs logger)
- **US1 (Phase 4)**: Depends on Phase 2; can run in parallel with Phase 3
- **US2 (Phase 5)**: Depends on Phase 2; can run in parallel with Phases 3 and 4 — E2E tests exercise existing redirect behaviour with no runtime dependency on Phase 4 unit tests completing first
- **US3 (Phase 6)**: Depends on Phase 3 (FR-006 builds on the same `get_next_url()` method)
- **US5 (Phase 7)**: Depends on Phase 6 (implementation in T025–T026; only tests remain)
- **Polish (Phase 8)**: Depends on all story phases completing

### User Story Dependencies

- **US4 (P1)**: Depends on Foundational (Phase 2) only — no dependency on other stories
- **US1 (P1)**: Depends on Foundational (Phase 2) only — tests existing code
- **US2 (P1)**: Depends on Phase 2 only — E2E exercises existing redirect behaviour (no runtime dependency on Phase 4 unit test completion; can be parallelised)
- **US3 (P2)**: Depends on US4 (Phase 3) — reuses the same `get_next_url()` that was just tested
- **US5 (P2)**: Depends on US3 (Phase 6) — implementation is in Phase 6; US5 only adds tests

### Parallel Opportunities

- T005–T010 (US4 tests): all independent, run together
- T013–T019 (US1 tests): all independent, run together
- T028–T035 (US3 tests): all independent, run together
- T038–T042 (US5 tests): all independent, run together
- T044–T047 (Polish docs): all independent, run together
- Phase 3 (US4) and Phase 4 (US1) can be worked on simultaneously once Phase 2 is done

---

## Parallel Example: User Story 3

```bash
# Launch all US3 tests together after T025–T027 implementation:
pytest tests/test_views/test_edit_view.py -k "us3 or shorthand or crud"

# Individual parallel tasks within US3:
Task T028: test next=list → list URL
Task T029: test next=detail → new object's detail URL
Task T030: test next=update → update URL
Task T031: test unrecognised shorthand → fallback
Task T032: test shorthand preserved in context on re-render (POST)
Task T033: test shorthand injected in context on GET
Task T034: test MVPFormView silently skips shorthand
Task T035: test MVPDeleteView not regressed
```

---

## Implementation Strategy

### MVP First (P1 Stories Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: US4 — Open-Redirect Protection
4. Complete Phase 4: US1 — URL Destination
5. Complete Phase 5: US2 — E2E user flow
6. **STOP and VALIDATE**: `pytest tests/test_views/test_edit_view.py tests/test_views/test_edit_view_e2e.py` — all pass
7. **MVP deliverable**: Security + URL redirect are fully tested and working

### Incremental Delivery

1. MVP (Phases 1–5) → Foundation + security stories done
2. Add US3 (Phase 6) → CRUD shorthand round-trips work
3. Add US5 (Phase 7) → Fallback chain fully tested
4. Polish (Phase 8) → Docs and final suite run

### Task Count Summary

| Phase | Story | Priority | Tasks | Code Changed? |
|-------|-------|----------|-------|---------------|
| 1 | Setup | — | 1 | New file (skeleton) |
| 2 | Foundational | — | 6 | `edit.py` (logging import + `get_next_candidate()` + refactor callers) |
| 3 | US4 | P1 | 10 | `edit.py` (FR-005b) + T010a |
| 4 | US1 | P1 | 9 | Tests only (+T013a for FR-001a hook) |
| 5 | US2 | P1 | 5 | Demo template + new E2E file (T021a) |
| 6 | US3 | P2 | 15 | `edit.py` (FR-006, FR-012) + tests + T035a/T035b E2E |
| 7 | US5 | P2 | 6 | Tests only |
| 8 | Polish | — | 6 | Docs |
| **Total** | | | **58** | |
