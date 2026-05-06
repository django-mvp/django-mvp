---
description: "Task list for List Search and Ordering Mixins (014)"
---

# Tasks: List Search and Ordering Mixins

**Input**: Design documents from `specs/014-list-search-ordering/`  
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/view-api.md ✅, quickstart.md ✅

**Branch**: `014-list-search-ordering`

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1–US4)

---

## Phase 1: Setup

**Purpose**: Verify the existing codebase and confirm no external setup is needed before implementation begins.

- [ ] T001 Read `mvp/views/list.py` to confirm current `SearchMixin`, `OrderMixin`, `SearchOrderMixin`, and `MVPListViewMixin` implementations match plan expectations
- [ ] T002 Read `demo/views.py` to identify all `order_by` declarations that must be migrated to three-tuple format
- [ ] T003 Read `skills/django-mvp/SKILL.md` to understand the current documented API surface before making changes

**Checkpoint**: Existing code confirmed — implementation can begin.

---

## Phase 2: Foundational — OrderMixin Three-Tuple Migration

**Purpose**: Migrate `OrderMixin` from two-tuple to three-tuple format. This is a **breaking API change** that blocks all test tasks (tests assert the new format).

**⚠️ CRITICAL**: All US2 implementation and all test tasks depend on this phase being complete first.

- [ ] T004 Update `OrderMixin._apply_ordering()` in `mvp/views/list.py` to read `choice[0]` as the public key matched against `?o=` and `choice[2]` as the ORM expression passed to `queryset.order_by()` — the raw `?o=` value is NEVER passed to the ORM
- [ ] T005 Update `OrderMixin.get_context_data()` in `mvp/views/list.py` to inject `order_by_choices` as the full three-tuple list and `current_ordering` as the matched public key (or `""`) — only inject when `order_by` is configured
- [ ] T006 Migrate `demo/views.py` all `order_by` list declarations from two-tuple `(field, label)` to three-tuple `(public_key, label, orm_expression)` format — ensure public keys are URL-safe and do not expose column names
- [ ] T007 Run `python manage.py check` and `poetry run pytest tests/` to verify no regressions before writing new tests

**Checkpoint**: `OrderMixin` three-tuple migration complete and all existing tests pass.

---

## Phase 3: User Story 1 — Text Search (Priority: P1) 🎯 MVP

**Goal**: `SearchMixin` correctly implements Django admin-style multi-word OR text search across declared fields. Context sentinels `is_searchable` and `search_query` are always injected. Mixin is a complete no-op when `search_fields` is unconfigured.

**Independent Test**: Configure a stub view with `search_fields = ['name']`, create three `Product` records. Assert `?q=foo` returns only matching records; blank `?q=` returns all three; `search_fields = None` with `?q=foo` returns all three.

### Tests for User Story 1 *(write first — observe failures before implementing)*

- [ ] T011 [P] [US1] Create `tests/test_views/test_list_view.py` with test infrastructure: import stubs, `RequestFactory`, factory-boy factories for `Product`/`Category` (or inline model creation if one-off), and stub view classes used across all test classes
- [ ] T012 [P] [US1] Write `TestSearchMixin` class in `tests/test_views/test_list_view.py` with: `test_search_no_query_returns_all`, `test_search_single_word_filters`, `test_search_multi_word_or_semantics`, `test_search_case_insensitive`, `test_search_whitespace_only_query_no_filter`
- [ ] T013 [P] [US1] Write `TestSearchMixinNoConfig` class in `tests/test_views/test_list_view.py` with: `test_search_no_fields_configured_is_noop`, `test_search_is_searchable_false_when_unconfigured`, `test_search_context_always_injected_when_unconfigured`
- [ ] T014 [P] [US1] Write `TestSearchMixinAdvanced` class in `tests/test_views/test_list_view.py` with: `test_search_related_field_traversal` (using `category__name`), `test_search_distinct_deduplicates` (multi-field match produces one record)

### Implementation for User Story 1

- [ ] T008 [US1] Update `SearchMixin.get_queryset()` in `mvp/views/list.py` to confirm it strips `?q=` and applies no filter when the stripped value is empty — verify no queryset modification occurs when `search_fields` is `None` or empty (existing behaviour; verify and document)
- [ ] T009 [US1] Update `SearchMixin.get_context_data()` in `mvp/views/list.py` to always inject `is_searchable` (bool) and `search_query` (stripped `?q=` value or `""`) regardless of whether `search_fields` is configured — document this guarantee in the docstring
- [ ] T010 [US1] Rewrite `SearchMixin` class docstring in `mvp/views/list.py` to Constitution XII format: intended-use summary, `Config:` block listing `search_fields` with type/default/description, `Override hooks:` listing `get_search_fields()`, and a minimal usage example

- [ ] T015 [US1] Run `python manage.py check` and `poetry run pytest tests/test_views/test_list_view.py -k "Search"` — all search tests must pass

**Checkpoint**: US1 independently testable and passing. `?q=` search is fully implemented and verified.

---

## Phase 4: User Story 2 — Safe Column Ordering (Priority: P1) 🎯 MVP

**Goal**: `OrderMixin` correctly implements whitelist-only ordering using three-tuple `(public_key, label, orm_expression)` entries. Unrecognised `?o=` values are silently ignored. Context is only injected when `order_by` is configured.

**Independent Test**: Configure a stub view with three `order_by` entries. Verify each valid `?o=public_key` applies the correct `orm_expression` to the queryset; `?o=arbitrary_field` is ignored; unconfigured `OrderMixin` with `?o=` is a no-op.

### Tests for User Story 2 *(write first — observe failures before implementing)*

- [ ] T017 [P] [US2] Write `TestOrderMixin` class in `tests/test_views/test_list_view.py` with: `test_order_valid_key_applies_orm_expression` (asserts `queryset.order_by` called with `orm_expression`, not `public_key`), `test_order_invalid_key_ignored`, `test_order_absent_parameter_no_override`
- [ ] T018 [P] [US2] Write `TestOrderMixinSecurity` class in `tests/test_views/test_list_view.py` with: `test_order_public_key_not_equal_orm_expression` (public key differs from field; asserts ORM expression used, not public key), `test_order_raw_param_never_reaches_orm` (assert `queryset.order_by` is never called with the raw `?o=` value for unrecognised inputs)
- [ ] T019 [P] [US2] Write `TestOrderMixinNoConfig` class in `tests/test_views/test_list_view.py` with: `test_order_no_config_is_noop`, `test_order_context_not_injected_when_unconfigured`, `test_order_empty_list_is_noop`
- [ ] T020 [P] [US2] Write `TestOrderMixinContext` class in `tests/test_views/test_list_view.py` with: `test_order_context_choices_full_three_tuple_list`, `test_order_context_current_ordering_is_public_key`, `test_order_context_current_ordering_empty_on_invalid`

### Implementation for User Story 2

- [ ] T016 [US2] Rewrite `OrderMixin` class docstring in `mvp/views/list.py` to Constitution XII format: intended-use summary, `Config:` block documenting `order_by` as `list[tuple[str, str, str]]` with the three-tuple schema explained, security guarantee noted, `Override hooks:` listing `get_order_by_choices()`, and a minimal usage example showing opaque public keys

- [ ] T021 [US2] Run `python manage.py check` and `poetry run pytest tests/test_views/test_list_view.py -k "Order"` — all ordering tests must pass

**Checkpoint**: US2 independently testable and passing. `?o=` ordering with opaque key security is fully implemented and verified.

---

## Phase 5: User Story 3 — Combined Search and Ordering (Priority: P2)

**Goal**: `SearchOrderMixin` combines both mixins transparently. Combined `?q=&o=` produces correctly filtered and ordered results. Each parameter works independently when the other is absent.

**Independent Test**: Configure a view with both `search_fields` and `order_by`. Submit `?q=foo&o=name_desc` and assert results are filtered to "foo" matches and ordered by name descending. Submit `?q=foo` only and assert default ordering. Submit `?o=name_asc` only and assert all records in ascending name order.

### Implementation for User Story 3

- [ ] T022 [US3] Rewrite `SearchOrderMixin` class docstring in `mvp/views/list.py` to Constitution XII format: intended-use summary, combined `Config:` block listing both `search_fields` and `order_by`, MRO evaluation-order guarantee documented, `Override hooks:` listing both override methods, and a minimal usage example

### Tests for User Story 3

- [ ] T023 [P] [US3] Write `TestSearchOrderMixin` class in `tests/test_views/test_list_view.py` with: `test_combined_search_and_ordering`, `test_combined_search_only_retains_default_ordering`, `test_combined_ordering_only_returns_all_records`
- [ ] T024 [P] [US3] Write `TestSearchOrderMixinMROOrder` in `tests/test_views/test_list_view.py` with: `test_ordering_applied_before_distinct` — create records that would trigger PostgreSQL DISTINCT + ORDER BY conflict if evaluation order were reversed; assert correct results with correct order
- [ ] T025 [US3] Run `python manage.py check` and `poetry run pytest tests/test_views/test_list_view.py -k "SearchOrder"` — all combined tests must pass

**Checkpoint**: US3 independently testable and passing. Combined mixin delivers correct results for all parameter combinations.

---

## Phase 6: User Story 4 — django_filters Integration (Priority: P2)

**Goal**: `SearchMixin` and `OrderMixin` compose correctly with `django_filters.views.FilterView` when the MRO convention is followed. The filterset constraints are preserved when `?q=` and `?o=` are also present.

**Independent Test**: Create a stub view as `class StubView(SearchOrderMixin, FilterView)` with a `filterset_class` filtering by `category`. Submit `?category=<id>&q=python&o=name_asc` and assert only records matching both the filterset and the search term are returned in the correct order.

### Tests for User Story 4

- [ ] T026 [P] [US4] Write `TestDjangoFiltersComposition` class in `tests/test_views/test_list_view.py` with: `test_filterset_and_search_both_applied`, `test_filterset_and_ordering_both_applied`, `test_filterset_search_ordering_all_combined`
- [ ] T027 [P] [US4] Write `TestDjangoFiltersNoOpCases` in `tests/test_views/test_list_view.py` with: `test_no_search_fields_search_is_noop_with_filterset`, `test_no_order_by_ordering_is_noop_with_filterset`
- [ ] T028 [US4] Run `poetry run pytest tests/test_views/test_list_view.py -k "Filters"` — all django_filters composition tests must pass
- [ ] T029 [US4] Run `python manage.py check` and full `poetry run pytest tests/test_views/test_list_view.py` — entire test module must pass

**Checkpoint**: US4 independently testable and passing. django_filters integration verified.

---

## Phase 7: E2E — Demo View Playwright Tests

**Goal**: Verify the search and ordering UI on the demo `ProductListView` works end-to-end in a real browser.

**Independent Test**: Start the dev server and navigate to the product list demo page. Use Playwright to type into the search box, submit, and verify filtered results. Select an ordering option and verify the page re-renders with the correct order.

- [ ] T030 [P] Start the Django development server (`python manage.py runserver`) and navigate to the product list demo page using the Playwright MCP server to confirm the page loads and the search input and ordering control are present
- [ ] T031 [US1] Use Playwright MCP to type "widget" into the search input, submit the form, and assert that only records containing "widget" are displayed; assert the search input is pre-populated with "widget"
- [ ] T032 [US2] Use Playwright MCP to select the "Name (A–Z)" ordering option and assert the first visible product name comes before the last alphabetically; assert the select control shows the selected state
- [ ] T033 [US3] Use Playwright MCP to submit `?q=widget&o=name_desc` and assert results are filtered and in descending name order simultaneously
- [ ] T034 [P] Create `tests/test_views/test_list_view_e2e.py` with pytest-playwright tests covering: search input pre-population, filtered results on search submit, ordering dropdown selected state, combined search + ordering results

**Checkpoint**: All E2E Playwright tests pass. UI search and ordering behaviour verified in a real browser.

---

## Phase 8: Polish — Docstrings and Skill Update

**Purpose**: Finalise documentation, update the `skills/django-mvp/SKILL.md` for the breaking `order_by` API change, and update `MVPListViewMixin` docstring.

- [ ] T035 [P] Rewrite `MVPListViewMixin` class docstring in `mvp/views/list.py` to Constitution XII format: intended-use summary, `Config:` block listing all configurable attributes (`search_fields`, `order_by`, `grid`, `paginate_by`, `create_view_name`, `empty_state_heading`, `empty_state_message`, `directory`), `Override hooks:` listing overridable methods, and a minimal usage example
- [ ] T036 [P] Update `skills/django-mvp/SKILL.md` to document the new `order_by` three-tuple format `(public_key, label, orm_expression)`, the security guarantee (opaque keys), the `django_filters` MRO convention, and the `is_searchable`/`search_query` always-available context sentinels
- [ ] T040 Update `CHANGELOG.md` with a breaking change entry for the `order_by` two-tuple → three-tuple migration (include upgrade instructions), and bump the package version string in `pyproject.toml`
- [ ] T037 Run `poetry run ruff check mvp/views/list.py demo/views.py` and `poetry run ruff format mvp/views/list.py demo/views.py` — all linting and formatting must pass
- [ ] T038 Run `python manage.py check` and `poetry run pytest tests/` — full test suite must pass with no failures
- [ ] T039 Review `specs/014-list-search-ordering/quickstart.md` against the final implementation; update any examples that changed during implementation

**Checkpoint**: All linting, formatting, and tests pass. `skills/django-mvp/SKILL.md` reflects the new API. Feature is complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Phase 1. **Blocks all test tasks** (tests assert the new three-tuple format).
- **US1 (Phase 3)**: Depends on Phase 2 completion. Independently testable.
- **US2 (Phase 4)**: Depends on Phase 2 completion. Independently testable.
- **US3 (Phase 5)**: Depends on US1 (Phase 3) AND US2 (Phase 4).
- **US4 (Phase 6)**: Depends on Phase 2 + US1 (Phase 3) + US2 (Phase 4). Can start in parallel with US3 (Phase 5). Requires `django_filters` installed in dev environment.
- **E2E (Phase 7)**: Depends on US1 and US2. Dev server must be running.
- **Polish (Phase 8)**: Depends on all prior phases.

### User Story Dependencies

- **US1 (P1)**: Start after Phase 2. No story dependencies.
- **US2 (P1)**: Start after Phase 2. No story dependencies. Can run in parallel with US1.
- **US3 (P2)**: Requires US1 and US2 both complete.
- **US4 (P2)**: Requires Phase 2 + US1 (Phase 3) + US2 (Phase 4). Can proceed in parallel with US3 (Phase 5).

### Parallel Opportunities per Story

**US1 (Phase 3)**: T011–T014 can all be written in parallel (different test classes, same file).  
**US2 (Phase 4)**: T017–T020 can all be written in parallel.  
**US3 (Phase 5)**: T023–T024 can be written in parallel; T022 (docstring) can be written in parallel with both.  
**US4 (Phase 6)**: T026–T027 can be written in parallel.  
**Polish (Phase 8)**: T035 (docstring), T036 (SKILL.md), T040 (CHANGELOG), T037 (lint) can all run in parallel.

---

## Implementation Strategy

**MVP scope**: Phases 1–4 (Setup + Foundation + US1 + US2) deliver the complete P1 value: correct `SearchMixin` with always-injected sentinels and correct `OrderMixin` with opaque-key security. This is the minimal set that closes all P1 acceptance criteria.

**Full feature**: Phases 5–8 add the combined `SearchOrderMixin` tests (US3), `django_filters` integration tests (US4), E2E Playwright coverage, and final skill/docstring polish.

**Suggested execution order** (single developer, sequential):  
Phase 1 → Phase 2 → Phase 3 (US1 tests + impl) → Phase 4 (US2 tests + impl) → Phase 5 → Phase 6 → Phase 7 → Phase 8
