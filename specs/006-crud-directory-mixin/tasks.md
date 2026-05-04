---
description: "Task list for 006-crud-directory-mixin"
---

# Tasks: CRUD Directory Mixin

**Input**: Design documents from `/specs/006-crud-directory-mixin/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/mixin-api.md ✅, quickstart.md ✅

**Workflow**: Design-First — the full API redesign is already captured in data-model.md and contracts/mixin-api.md. Implement the redesign, verify using Playwright MCP server for UI stories, then add tests. Every phase touching Django code includes a `python manage.py check` validation task. pytest + pytest-django for unit/integration; pytest-playwright for E2E (US5). Use context7 for up-to-date Django CBV / `reverse()` docs if needed.

**Organization**: Tasks grouped by user story. Each story follows Design → Implement → Verify → Test.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other [P] tasks in the same phase
- **[Story]**: Which user story this task belongs to (US1–US5)

---

## Phase 1: Setup

**Purpose**: Confirm the test suite is green before any code changes.

- [X] T001 Run `pytest tests/` to establish a clean baseline — all existing tests MUST pass before any modification begins

---

## Phase 2: Foundational (Structural Cleanup — Prerequisite for All User Stories)

**Purpose**: Remove structural issues identified in research.md that are not user-story-specific but block clean implementation of every story.

**⚠️ CRITICAL**: Both tasks MUST be complete before any user story work begins.

- [X] T002 [P] Remove `_OBJECT_ACTIONS = _OBJECT_ACTIONS` class-level attribute from `CRUDDirectoryMixin` in `mvp/views/detail.py` (module-level frozenset remains; class must not re-expose it)
- [X] T003 [P] Remove redundant `ModelInfoMixin` from `PageObjectMixin`'s explicit base list in `mvp/views/detail.py` — `CRUDDirectoryMixin` already inherits it; the explicit entry creates MRO noise
- [X] T002a [P] Run `python manage.py check` — zero errors MUST be reported after structural cleanup
- [X] T002b [P] Run `pytest tests/` to confirm structural cleanup introduced no regressions

**Checkpoint**: Structural cleanup complete — user story implementation can begin

---

## Phase 3: User Story 1 — Declarative URL Resolution Without URL Wiring (Priority: P1) 🎯 MVP

**Goal**: A developer sets `directory = ["list", "detail", "update", "delete"]` on a view and the mixin resolves and injects the correct `{action}_url` entries into the template context — zero URL reversal code in the view or template.

**Independent Test**: A view with `directory = ["list", "detail"]`, `has_list_permission = True`, `has_detail_permission = True`, and a matching URL conf produces `{"list_url": "/products/", "detail_url": "/products/42/"}` in context. Verified with a minimal stub view + `RequestFactory`.

### Implementation for User Story 1

- [X] T004 [US1] Replace `get_lookup_kwargs()` with `get_url_kwargs(action: str) -> dict | None` in `CRUDDirectoryMixin` in `mvp/views/detail.py`. Default implementation: return `{}` when `action` is `"list"` or `"create"`; return `dict(self.kwargs) or None` for all other actions (object-level and custom). Update all internal callers. Remove the `_OBJECT_ACTIONS` class-level attribute from `CRUDDirectoryMixin`. Remove the module-level `_OBJECT_ACTIONS = frozenset(...)` constant — it is no longer referenced by any production code.
- [X] T006 [US1] Update `resolve_crud_url()` in `mvp/views/detail.py` to call `self.get_url_kwargs(action)` and suppress (return `None`) when the result is `None`. Remove the old `_OBJECT_ACTIONS` membership check. Pass the returned dict directly to `reverse()`. No other branching on action category is needed.
- [X] T007 [P] [US1] Replace `get_lookup_kwargs()` override in `MVPModelFormBase` in `mvp/views/edit.py` with `get_url_kwargs(self, action: str) -> dict | None`. Logic: call `super().get_url_kwargs(action)`; if result is **not `None`** (use `is not None` — not truthiness, since `{}` is a valid non-None return for collection actions), return it; otherwise fall back to `{self.pk_url_kwarg: obj.pk}` if `self.object` exists, else return `None`.

### Validation for User Story 1

- [X] T008 [US1] Run `python manage.py check` — zero errors MUST be reported
- [X] T009 [P] [US1] Write US1 unit tests in `tests/test_views/test_crud_directory_mixin.py`:
  - `directory = ["list"]` on a view with no URL kwargs → `list_url` resolves (default `get_url_kwargs("list")` returns `{}`)
  - `directory = ["detail", "update", "delete"]` on a view with `self.kwargs = {"pk": 42}` → object-level URLs resolved with `{"pk": 42}`
  - `directory = ["detail"]` on a view with no URL kwargs → `get_url_kwargs("detail")` returns `None` → `detail_url` absent, no error
  - `directory = []` → context `directory` key is `{}` (never absent)
  - Action in `directory` whose URL pattern does not exist → `NoReverseMatch` propagates (not swallowed)
  - Action in `directory` not present in `crud_views` → `ValueError` raised with action name in message
  - Two actions resolving to the same URL string → both `{action}_url` keys present (no deduplication)
- [X] T010 [US1] Run `pytest tests/test_views/test_crud_directory_mixin.py -k US1` — all US1 tests MUST pass

**Checkpoint**: User Story 1 complete — URL resolution works declaratively with zero wiring code

---

## Phase 4: User Story 2 — Permission-Gated Directory URLs (Priority: P1)

**Goal**: Each `{action}_url` entry appears only when the corresponding `has_{action}_permission` attribute evaluates to truthy for the current user. Absent attribute = denied. Callable attributes receive `request.user`.

**Independent Test**: A view with `has_delete_permission = False` and `directory = ["delete"]` produces `{}`. Same view with `has_delete_permission = True` produces `{"delete_url": "..."}`. Verified with `RequestFactory`.

### Implementation for User Story 2

- [X] T011 [US2] In `CRUDDirectoryMixin` in `mvp/views/detail.py`: rename `has_read_permission = False` → `has_detail_permission = False`; add `has_list_permission = False` as a new class attribute alongside the existing four permission attributes
- [X] T012 [P] [US2] Fix `MVPUpdateView.get_delete_url()` in `mvp/views/edit.py` to route through `self.resolve_crud_url("delete")` instead of calling `reverse()` directly — `has_delete_permission` must now gate this URL; preserve the `?back=...&next=...` query-string appending logic that follows the URL resolution. ⚠️ **Regression note**: any existing `MVPUpdateView` subclass that relied on `get_delete_url()` always resolving must explicitly set `has_delete_permission = True`.

### Validation for User Story 2

- [X] T013 [US2] Run `python manage.py check` — zero errors MUST be reported
- [X] T014 [P] [US2] Write US2 unit tests in `tests/test_views/test_crud_directory_mixin.py`:
  - `has_delete_permission = False` → `delete_url` absent from context
  - `has_detail_permission = True` → `detail_url` present (confirms rename from `has_read_permission`)
  - `has_list_permission = True` → `list_url` present
  - Callable `has_create_permission` returning `True` for user → `create_url` present
  - Callable `has_create_permission` returning `False` for user → `create_url` absent
  - Permission attribute entirely absent (not declared) → URL excluded, no `AttributeError`
  - Callable permission that raises `ValueError` → exception propagates (not swallowed)
  - All permissions `False` → context contains `directory` as `{}` (key always present)
- [X] T015 [US2] Run `pytest tests/test_views/test_crud_directory_mixin.py -k US2` — all US2 tests MUST pass

**Checkpoint**: User Stories 1 + 2 complete — permission-gated URL resolution fully working

---

## Phase 5: User Story 5 — Render Navigation Links Only for Available Actions (Priority: P1)

**Goal**: End user sees action buttons only for operations they are permitted to perform. Admin role sees edit/delete buttons; read-only role does not. Neither role sees broken links.

**Independent Test**: Two fixture users (admin, read-only) request the same `ProductDetailView`. Admin's rendered HTML contains edit and delete anchor elements; read-only user's HTML does not. Neither page contains broken links. Verified with Playwright MCP server.

### Implementation for User Story 5

- [X] T016 [US5] Add `ProductDetailView` to `demo/views.py`:
  - `model = Product`
  - `directory = ["list", "detail", "update", "delete"]`
  - `has_list_permission = True` (always show back link)
  - `has_detail_permission = True`
  - `has_update_permission` and `has_delete_permission` as callables checking `request.user.is_staff`
- [X] T017 [P] [US5] Add `product-detail` URL pattern in `demo/urls.py`: `path("products/<int:pk>/", ProductDetailView.as_view(), name="product-detail")`
- [X] T018 [P] [US5] Create `demo/templates/demo/product_detail.html` — consult `django-cotton-bs5` component library first for action button markup before writing any raw HTML (skill: `demo-views`); extend `base.html`; render action buttons using `{% if directory.update_url %}` / `{% if directory.delete_url %}` / `{% if directory.list_url %}` conditionals; no hardcoded URLs

### Verification for User Story 5

- [X] T019 [US5] Verify demo page using Playwright MCP server — navigate to `/products/<pk>/` as staff user: assert edit and delete buttons are visible; navigate as non-staff user: assert edit and delete buttons are absent; assert list link present for both roles; assert zero broken links (all href values resolve to non-404 responses)

### Tests for User Story 5 (AFTER Playwright verification)

- [X] T020 [P] [US5] Write E2E Playwright tests in `tests/test_views/test_crud_directory_mixin_e2e.py` covering US5 acceptance scenarios:
  - Staff user: edit button visible, delete button visible, list link present
  - Read-only user: edit button absent, delete button absent, list link present
  - Mark with `@pytest.mark.e2e` and `@pytest.mark.django_db`

### Story 5 Validation

- [X] T021 [US5] Run `python manage.py check` — zero errors MUST be reported
- [X] T022 [US5] Run `pytest tests/test_views/test_crud_directory_mixin_e2e.py -m e2e` — all US5 E2E tests MUST pass

**Checkpoint**: User Stories 1, 2 + 5 complete — full end-user experience verified with Playwright

---

## Phase 6: User Story 3 — Override URL Kwargs for Nested Resource URLs (Priority: P2)

**Goal**: A developer can override `get_url_kwargs(action)` to return the appropriate kwargs per action — stripping or injecting parent-resource kwargs as needed for nested URL patterns. No new production code required — this story is fully served by the single-method design implemented in Phase 3.

**Independent Test**: A view stub with `self.kwargs = {"project_pk": 7, "pk": 42}` overrides `get_object_url_kwargs()` to return only `{"pk": 42}`. Object-level URL reversal succeeds; collection URL (which uses `get_collection_url_kwargs()` = `{}`) also succeeds.

### Tests for User Story 3

- [X] T023 [P] [US3] Write US3 unit tests in `tests/test_views/test_crud_directory_mixin.py`:
  - Override `get_url_kwargs(action)` to return `{"project_pk": ..., "pk": ...}` for object-level actions and `{"project_pk": ...}` for `"list"`/`"create"` → all URLs resolve without reversal errors
  - `get_url_kwargs(action)` returns `None` for an action → that action’s URL is silently excluded, no `NoReverseMatch` raised
  - No override → `get_url_kwargs("list")` default returns `{}` → flat list URL resolves correctly
  - Custom action `"archive"` in `directory` with no URL kwargs (`self.kwargs = {}`) → `get_url_kwargs("archive")` returns `None` → `archive_url` absent from context, no error raised
- [X] T024 [US3] Run `pytest tests/test_views/test_crud_directory_mixin.py -k US3` — all US3 tests MUST pass

**Checkpoint**: User Story 3 complete — nested URL pattern override verified

---

## Phase 7: User Story 4 — Customize View Name Convention (Priority: P2)

**Goal**: A developer sets a custom `crud_views` mapping with non-standard URL name patterns. The directory resolves against the custom names, not the defaults. No new production code required — `crud_views` attribute already exists.

**Independent Test**: A view with `crud_views = {"list": "my_app:my-{model_name}-index", "detail": "my_app:my-{model_name}-view"}` and matching URL patterns resolves `list_url` and `detail_url` using the custom names.

### Tests for User Story 4

- [X] T025 [P] [US4] Write US4 unit tests in `tests/test_views/test_crud_directory_mixin.py`:
  - Custom `crud_views` with non-default name patterns → resolved URLs use custom names
  - `{model_name}` token in custom pattern → substituted with `model_meta.model_name`
  - `{app_name}` token in custom pattern → substituted with `model_meta.app_label`
  - Action in `directory` not present in custom `crud_views` → `ValueError` with action name in message
- [X] T026 [US4] Run `pytest tests/test_views/test_crud_directory_mixin.py -k US4` — all US4 tests MUST pass

**Checkpoint**: User Story 4 complete — custom URL naming convention verified

---

## Final Phase: Polish & Cross-Cutting Concerns

**Purpose**: Documentation update, full regression pass, final health check.

- [X] T027 [P] Update `skills/django-mvp/SKILL.md` to reflect the public API change: replace `get_lookup_kwargs()` references with `get_url_kwargs(action: str)`; replace `has_read_permission` with `has_detail_permission`; add `has_list_permission`
- [X] T028 Run full pytest suite `pytest tests/` — all tests MUST pass (no regressions across all stories)
- [X] T029 [P] Run `python manage.py check` — zero errors MUST be reported across the full project

---

## Dependencies

```
Phase 1 (Setup)
    └── Phase 2 (Foundational Cleanup)
            ├── Phase 3 (US1 — URL Resolution) [P1] 🎯 MVP
            │       └── Phase 4 (US2 — Permission Gating) [P1]
            │               ├── Phase 5 (US5 — Demo + Playwright) [P1]
            │               ├── Phase 6 (US3 — Nested Kwargs Tests) [P2]  ← can run in parallel with Phase 5
            │               └── Phase 7 (US4 — Custom crud_views Tests) [P2] ← can run in parallel with Phase 5
            │                       └── Final Phase (Polish)
```

**US3 and US4 (Phase 6 + 7) can run in parallel with Phase 5 (US5) once Phase 4 is complete** — they operate on the test file only and do not touch demo/ or the production source.

---

## Parallel Execution Examples

**After Phase 4 completes** (T015 done), all three of the following can proceed simultaneously:

| Stream A | Stream B | Stream C |
|---|---|---|
| T016 → T017 + T018 → T019 → T020 → T021 → T022 | T023 → T024 | T025 → T026 |
| US5 (demo + playwright) | US3 (nested kwargs tests) | US4 (custom crud_views tests) |

**Within Phase 3**, T006 and T007 can run in parallel (different files).

**Within Phase 4**, T011 + T012 can run in parallel (different locations in different class hierarchies).

---

## Implementation Strategy

**MVP** (deliver first, before P2 stories): Phases 1–5 = US1 + US2 + US5

This delivers the complete fix for all identified bugs (`has_read_permission` dead attribute, URL kwargs leak, permission bypass in `get_delete_url()`), full unit test coverage for both P1 developer stories, and a live Playwright-verified demo page. US3 and US4 are additive test-only phases that validate already-working behaviour.

---

## Summary

| Metric | Value |
|---|---|
| Total tasks | 30 |
| Phase 3 (US1) tasks | 6 |
| Phase 4 (US2) tasks | 5 |
| Phase 5 (US5) tasks | 7 |
| Phase 6 (US3) tasks | 2 |
| Phase 7 (US4) tasks | 2 |
| Setup + Foundational tasks | 5 |
| Polish tasks | 3 |
| Parallel opportunities | 4 (within Phase 3, Phase 4; Phases 6+7 alongside Phase 5) |
| Production files modified | 2 (`mvp/views/detail.py`, `mvp/views/edit.py`) |
| New files | 3 (`tests/test_views/test_crud_directory_mixin.py`, `tests/test_views/test_crud_directory_mixin_e2e.py`, `demo/templates/demo/product_detail.html`) |
| Modified files | 3 (`demo/views.py`, `demo/urls.py`, `skills/django-mvp/SKILL.md`) |
| Suggested MVP scope | Phases 1–5 (US1 + US2 + US5) |
