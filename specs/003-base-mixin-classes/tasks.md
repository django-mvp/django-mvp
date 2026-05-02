---
description: "Task list for: Document and Test Core View Mixins"
---

# Tasks: Document and Test Core View Mixins

**Input**: Design documents from `/specs/003-base-mixin-classes/`
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ quickstart.md ✅

**Workflow**: Design-first. Behaviour changes to `mvp/views/base.py` are implemented and verified before tests are written. No UI changes → no Playwright tasks. All phases touching Django code include `python manage.py check`. Tests are written after implementation verification.

**Source files touched**:
- `mvp/views/base.py` — behaviour changes + docstrings
- `tests/test_views/test_base.py` — new test file
- `skills/django-mvp/SKILL.md` — API update for `breadcrumbs` attr

---

## Phase 1: Setup

**Purpose**: Confirm the test infrastructure is in place before any implementation work begins.

- [X] T001 Verify `tests/test_views/` directory exists and has `__init__.py`; create both if missing
- [X] T002 [P] Read `tests/test_views/test_delete_view.py` to understand current test conventions (fixtures, `RequestFactory` usage, class structure) before writing new tests

---

## Phase 2: Foundational — Behaviour Changes to `mvp/views/base.py`

**Purpose**: Apply the two small agreed behaviour changes. All user stories depend on this correct implementation existing before docstrings and tests are written.

**⚠️ CRITICAL**: Must be complete before user story phases begin.

- [X] T003 In `mvp/views/base.py`: add `from django.core.exceptions import ImproperlyConfigured` import; change `BaseTemplateNameMixin.base_template_name = ""` to `base_template_name = None`; update `get_template_names()` to raise `ImproperlyConfigured` with message `"{ClassName} requires a 'base_template_name' attribute to be set."` when `base_template_name is None`
- [X] T004 In `mvp/views/base.py`: add `breadcrumbs: list = []` class attribute to `PageMixin` (after `page_class = ""`); update `get_breadcrumbs()` to return `self.breadcrumbs` instead of `[]`
- [X] T005 Run `python manage.py check` — zero errors MUST be reported
- [X] T006 Run `poetry run pytest tests/test_smoke.py` — all smoke tests pass (confirms existing imports still work)

**Checkpoint**: Behaviour changes are live and project is not broken.

---

## Phase 3: User Story 1 — New Developers Learn Mixin Architecture (Priority: P1)

**Goal**: `BaseTemplateNameMixin` and `PageMixin` have comprehensive Google-style docstrings so that a new developer can understand each mixin's purpose, attributes, and extension points from IDE tooltips alone.

**Independent Test**: Open `mvp/views/base.py` in an IDE and hover over `BaseTemplateNameMixin`, `PageMixin`, and each of their public methods — each should show meaningful help text with parameter descriptions, return types, and a usage example.

### Implementation for User Story 1

- [X] T007 [US1] Write Google-style class docstring for `BaseTemplateNameMixin` in `mvp/views/base.py`: explain purpose (fallback base template), document `base_template_name` attribute (type, default, required), include a usage example showing a concrete subclass, and list the primary known subclasses by name (FR-009: `MVPDetailView`, `MVPListViewMixin`, `MVPFormBase`, `MVPDeleteView`, `MVPTableView`)
- [X] T008 [US1] Write Google-style method docstring for `BaseTemplateNameMixin.get_template_names()` in `mvp/views/base.py`: document `Args` (none beyond self), `Returns` (list[str] with explanation of ordering), `Raises` (`ImproperlyConfigured` when `base_template_name is None`), and `Example`
- [X] T009 [US1] Write Google-style class docstring for `PageMixin` in `mvp/views/base.py`: explain purpose (page context injection), document all five class attributes (`page_title`, `page_subtitle`, `page_icon`, `page_class`, `breadcrumbs`) with types, defaults, and the attribute-vs-override guidance; list the primary views that use it (FR-009: `MVPTemplateView`, `MVPDetailView`, `MVPListViewMixin`, `MVPFormBase`)
- [X] T010 [US1] Write Google-style method docstrings for `PageMixin.get_context_data()` and `PageMixin.get_page_context()` in `mvp/views/base.py`: document the `page` context dict shape (keys: `title`, `subtitle`, `icon`, `class`, `breadcrumbs`) and the reason for grouping under a single key
- [X] T011 [P] [US1] Write Google-style method docstrings for `PageMixin.get_page_title()`, `get_page_subtitle()`, `get_page_icon()` in `mvp/views/base.py`: document `Returns`, note these are override hooks, include one `Example` per method
- [X] T012 [P] [US1] Write Google-style method docstrings for `PageMixin.get_page_class()` and `get_breadcrumbs()` in `mvp/views/base.py`: document `Returns`, note `get_page_class()` always prefixes `"mvp-page"`, note `get_breadcrumbs()` returns `self.breadcrumbs`, include one `Example` per method

### Story 1 Validation

- [X] T013 [US1] Run `python manage.py check` — zero errors MUST be reported
- [X] T014 [US1] Run `poetry run ruff check mvp/views/base.py` — zero lint violations
- [X] T015 [US1] Run `poetry run ruff format --check mvp/views/base.py` — no format changes needed

**Checkpoint**: All public methods and classes have complete Google-style docstrings. A developer hovering in an IDE sees meaningful help text.

---

## Phase 4: User Story 2 — Code Maintainers Verify Mixin Behaviour with Tests (Priority: P1)

**Goal**: Comprehensive pytest coverage for both mixins in `tests/test_views/test_base.py` — 100% line and branch coverage, all tests pass in < 2 seconds.

**Independent Test**: Run `poetry run pytest tests/test_views/test_base.py -v` — all tests pass and coverage report shows 100% for `mvp/views/base.py`.

### Implementation for User Story 2

- [X] T016 [US2] Create `tests/test_views/test_base.py` with module docstring, imports (`pytest`, `django.test.RequestFactory`, `django.core.exceptions.ImproperlyConfigured`, `django.views.generic.TemplateView`, `mvp.views.base.BaseTemplateNameMixin`, `mvp.views.base.PageMixin`), and two minimal view stub classes used across all tests:
  - `ConcreteTemplateView(BaseTemplateNameMixin, TemplateView)` with `base_template_name = "base.html"` and `template_name = "specific.html"`
  - `ConcretePage(PageMixin, TemplateView)` with `template_name = "page.html"`
- [X] T017 [US2] Add `TestBaseTemplateNameMixin` class in `tests/test_views/test_base.py` with tests:
  - `test_appends_base_template_name` — assert `base.html` is last in the list
  - `test_specific_template_comes_first` — assert view-specific template precedes base template
  - `test_raises_when_base_template_name_is_none` — assert `ImproperlyConfigured` raised
  - `test_error_message_includes_class_name` — assert `ImproperlyConfigured` message contains the class name
- [X] T018 [US2] Add `TestPageMixinDefaults` class in `tests/test_views/test_base.py` with tests for all default attribute values using a bare `ConcretePage` instance:
  - `test_page_title_default` → `""`
  - `test_page_subtitle_default` → `""`
  - `test_page_icon_default` → `None`
  - `test_page_class_default` → `""`
  - `test_breadcrumbs_default` → `[]`
- [X] T019 [US2] Add `TestPageMixinGetters` class in `tests/test_views/test_base.py` testing each getter method:
  - `test_get_page_title_returns_attribute`
  - `test_get_page_subtitle_returns_attribute`
  - `test_get_page_icon_returns_attribute`
  - `test_get_page_class_always_includes_mvp_page`
  - `test_get_page_class_with_extra_class`
  - `test_get_page_class_with_empty_page_class`
  - `test_get_page_class_with_none_page_class` — assert `page_class = None` still yields `"mvp-page"` (edge case A1)
  - `test_get_breadcrumbs_returns_attribute`
- [X] T020 [US2] Add `TestPageMixinGetPageContext` class in `tests/test_views/test_base.py` testing `get_page_context()`:
  - `test_returns_all_expected_keys` — assert dict has keys `title`, `subtitle`, `icon`, `class`, `breadcrumbs`
  - `test_context_values_match_getters` — assert each value equals the corresponding `get_*()` return
- [X] T021 [US2] Add `TestPageMixinGetContextData` class in `tests/test_views/test_base.py` testing `get_context_data()`:
  - `test_injects_page_key` — assert `"page"` key present in context
  - `test_page_value_is_page_context` — assert `context["page"]` equals `get_page_context()` output
  - `test_preserves_existing_context_keys` — assert other context keys (e.g., `view`) are not removed
  - (Use `RequestFactory().get("/")`, attach to view instance, call `setup()` and `get_context_data()`)

### Story 2 Validation

- [X] T022 [US2] Run `python manage.py check` — zero errors MUST be reported
- [X] T023 [US2] Run `poetry run pytest tests/test_views/test_base.py -v` — all tests pass
- [X] T024 [US2] Run `poetry run pytest tests/test_views/test_base.py --cov=mvp/views/base --cov-report=term-missing` — 100% line and branch coverage on `mvp/views/base.py`

**Checkpoint**: All mixin behaviour is covered by tests. Regressions will be caught automatically.

---

## Phase 5: User Story 3 — View Developers Understand Extension Points (Priority: P2)

**Goal**: Docstrings and tests explicitly document and exercise the override-hook pattern for all `PageMixin` getters, so developers know which methods to override and what contract they must maintain.

**Independent Test**: Create a custom view subclassing `PageMixin` that overrides `get_breadcrumbs()` — the test in `test_base.py` covering this pattern passes cleanly.

### Implementation for User Story 3

- [X] T025 [US3] **Enhance** the docstrings written in T011/T012 for `get_page_title()`, `get_page_subtitle()`, `get_page_icon()`, `get_page_class()`, `get_breadcrumbs()` in `mvp/views/base.py` by adding the canonical override-hook sentence: *"This method is the override hook for dynamic values. To set a static value, assign the corresponding class attribute instead."* and an `Example` block showing the override pattern for `get_page_title()` and `get_breadcrumbs()` specifically
- [X] T026 [US3] Update `BaseTemplateNameMixin.get_template_names()` docstring in `mvp/views/base.py` to include an `Example` showing the override pattern (inserting a conditional template before calling `super()`)
- [X] T027 [US3] Add `TestPageMixinOverridePattern` class in `tests/test_views/test_base.py` with tests using a custom subclass that overrides `get_page_title()` to return a dynamic value and `get_breadcrumbs()` to return a custom list:
  - `test_overridden_get_page_title_used_in_context`
  - `test_overridden_get_breadcrumbs_used_in_context`
  - `test_parent_page_class_still_applied`

### Story 3 Validation

- [X] T028 [US3] Run `python manage.py check` — zero errors MUST be reported
- [X] T029 [US3] Run `poetry run pytest tests/test_views/test_base.py -v` — all tests pass (including new override-pattern tests)
- [X] T030 [US3] Run `poetry run ruff check mvp/views/base.py` — zero lint violations

**Checkpoint**: Override patterns are documented and tested. Developers can answer *"When do I set `page_title` vs. override `get_page_title()`?"* by reading the docstring alone.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Skill update, final lint pass, and full test suite run.

- [X] T031 [P] Update `skills/django-mvp/SKILL.md`: add documentation for the `breadcrumbs` class attribute on `PageMixin` — include type (`list`), default (`[]`), and a usage example alongside the existing `page_title`/`page_subtitle` attr docs
- [X] T032 Run `poetry run ruff check mvp/views/base.py tests/test_views/test_base.py` — zero violations
- [X] T033 Run `poetry run ruff format --check mvp/views/base.py tests/test_views/test_base.py` — no format changes needed
- [X] T034 Run full test suite: `poetry run pytest tests/ -v` — all tests pass, no regressions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — **BLOCKS all user story phases**
- **Phase 3 (US1)**: Depends on Phase 2 — can start immediately after
- **Phase 4 (US2)**: Depends on Phase 2 — can start immediately after (parallel with Phase 3)
- **Phase 5 (US3)**: Depends on Phase 2 — builds on Phase 3/4 docstrings and tests
- **Phase 6 (Polish)**: Depends on all story phases complete

### User Story Dependencies

- **US1 (P1)**: Depends only on Phase 2; independent of US2/US3
- **US2 (P1)**: Depends only on Phase 2; independent of US1/US3 (can be worked in parallel with US1)
- **US3 (P2)**: Depends on Phase 2; extends US1 docstrings and US2 test file; start after US1+US2 are complete

### Parallel Opportunities

- T001 and T002 (Phase 1) can run in parallel
- T007–T008 (US1, `BaseTemplateNameMixin` docstrings) can run in parallel with T009–T012 (US1, `PageMixin` docstrings)
- T011 and T012 (US1, individual getter docstrings) can run in parallel
- T016–T021 (US2, individual test classes) are independent and can be written in parallel once T016 stub setup is done
- T031 (skills update) can run in parallel with T032–T033 (lint checks)

---

## Parallel Example: User Story 2

```bash
# After T016 creates the stub classes, these test classes can be written in parallel:
T017 - TestBaseTemplateNameMixin (tests/test_views/test_base.py)
T018 - TestPageMixinDefaults     (tests/test_views/test_base.py)
T019 - TestPageMixinGetters      (tests/test_views/test_base.py)
T020 - TestPageMixinGetPageContext (tests/test_views/test_base.py)
T021 - TestPageMixinGetContextData (tests/test_views/test_base.py)
```

---

## Implementation Strategy

### MVP First (US1 + US2 only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational behaviour changes
3. Complete Phase 3: US1 docstrings
4. Complete Phase 4: US2 tests
5. **STOP and VALIDATE**: `pytest tests/test_views/test_base.py --cov` shows 100%
6. Ship: docstrings + tests are the full deliverable; US3 is additive polish

### Incremental Delivery

- After Phase 3: IDE tooltips work → US1 done
- After Phase 4: 100% test coverage → US2 done
- After Phase 5: Override patterns documented and tested → US3 done
- After Phase 6: Skills updated, full suite clean → feature complete

---

## Summary

| Metric | Value |
|--------|-------|
| Total tasks | 34 |
| Phase 1 (Setup) | 2 tasks |
| Phase 2 (Foundational) | 4 tasks |
| Phase 3 (US1 — Docstrings) | 9 tasks |
| Phase 4 (US2 — Tests) | 9 tasks |
| Phase 5 (US3 — Extension Points) | 6 tasks |
| Phase 6 (Polish) | 4 tasks |
| Parallelizable tasks | 10 tasks marked [P] |
| New files created | 1 (`tests/test_views/test_base.py`) |
| Files modified | 2 (`mvp/views/base.py`, `skills/django-mvp/SKILL.md`) |
| Playwright tasks | 0 (no UI changes) |
| End-to-end tests | 0 (pure Python library; exempted by constitution) |
| Suggested MVP scope | Phases 1–4 (US1 + US2): behaviour changes + docstrings + 100% test coverage |
