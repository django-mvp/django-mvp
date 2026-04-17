---
description: "Implementation tasks for Dashboard List View Mixin feature"
---

# Tasks: Dashboard List View Mixin

**Input**: Design documents from `/specs/008-dash-list-view/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Workflow**: Following Design-First approach - implement and verify design BEFORE writing tests. Visual verification using chrome-devtools-mcp IS REQUIRED per constitution (Principle VI). Comprehensive unit/integration/E2E tests (Phase 10) are OPTIONAL for this feature as most functionality already exists and is tested. However, the two critical bug fixes (T005, T006) SHOULD have test coverage. UI changes MUST be verified using chrome-devtools-mcp DURING implementation. Use context7 for up-to-date library documentation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. Each story follows: Design → Implement → Verify.

**Important Note**: Most implementation already exists. This feature focuses on:

1. Fixing multi-word OR search (FR-020)
2. Fixing pagination footer context (FR-016-018)
3. Creating additional demo views
4. Writing comprehensive tests (optional)
5. Documentation

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify existing implementation and prepare for enhancements

- [ ] T001 Verify all mixin classes exist in mvp/views.py (SearchMixin, OrderMixin, SearchOrderMixin, ListItemTemplateMixin, MVPListViewMixin)
- [ ] T002 Verify list view template exists at mvp/templates/mvp/list_view.html
- [ ] T003 [P] Verify Cotton components exist (c-grid, c-list.search-widget, c-list.order-widget, c-sidebar.filter, c-list.empty)
- [ ] T004 [P] Verify existing demo view ListViewDemo in demo/views.py with Product model

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Fix existing implementation gaps that MUST be complete before ANY user story can be fully functional

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Fix multi-word OR search in mvp/views.py SearchMixin._apply_search() - split search term by any whitespace (space/tab/newline) and apply OR matching across all words and fields (FR-020)
- [X] T005a Write test for multi-word OR search in tests/test_list_view_mixins.py - verify "red car" matches records with "red" OR "car"
- [X] T006 Fix pagination footer context in mvp/templates/cotton/page/footer/pagination.html - update to use page_obj.start_index(), page_obj.end_index(), page_obj.paginator.count instead of DataTables variables (FR-016-018)
- [X] T006a Write test for pagination footer context in tests/integration/test_list_view_integration.py - verify correct variable usage

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Basic List Display (Priority: P1) 🎯 MVP

**Goal**: Developers can create a simple list view with minimal configuration showing model data in a grid with automatic page title and pagination

**Independent Test**: Create a view mixing MVPListViewMixin with only model and list_item_template specified, verify: (1) page displays model verbose_name as title, (2) objects render in single-column grid, (3) pagination footer displays correctly with entry counts and navigation links

### Verification for User Story 1

- [X] T007 [US1] Verify MVPListViewMixin provides automatic page title from model verbose_name in mvp/views.py get_page_title() method (FR-008)
- [X] T008 [US1] Verify MVPListViewMixin defaults to single-column grid when grid attribute not specified in mvp/views.py get_grid_config() method (FR-013)
- [X] T009 [US1] Verify list_view.html template renders objects using list_item_template within grid component (FR-012)
- [X] T010 [US1] Verify pagination footer displays correctly with entry counts on left and navigation on right in mvp/templates/cotton/page/footer/pagination.html (FR-016-018)
- [X] T011 [US1] Create MinimalListViewDemo in demo/views.py with only model, template_name, list_item_template, paginate_by to demonstrate minimal configuration
- [X] T012 [US1] Add URL route for MinimalListViewDemo in demo/urls.py
- [X] T013 [US1] Verify MinimalListViewDemo using chrome-devtools-mcp: check page title, single-column grid, pagination footer

**Checkpoint**: At this point, User Story 1 should be fully functional and verified independently

---

## Phase 4: User Story 2 - Custom Grid Configuration (Priority: P2)

**Goal**: Developers can control grid layout by setting grid attribute to create responsive multi-column layouts

**Independent Test**: Create a view with custom grid attribute (e.g., {"cols": 1, "md": 2, "lg": 3}), verify rendered output reflects specified grid configuration with correct column counts at different screen sizes

### Verification for User Story 2

- [X] T014 [US2] Verify MVPListViewMixin passes grid attribute to c-grid component via get_grid_config() method in mvp/views.py (FR-015)
- [X] T017 [P] [US2] Create GridDemo3Col in demo/views.py with grid = {"cols": 1, "md": 2, "lg": 3}
- [X] T019 [US2] Add URL routes for all grid demo views in demo/urls.py
- [X] T020 [US2] Verify grid demos using chrome-devtools-mcp at different viewport sizes (320px, 768px, 1024px, 1920px) to confirm responsive behavior (FR-032, SC-004)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Search Functionality (Priority: P2)

**Goal**: Developers add search_fields to view class and system automatically displays search bar in page header, users can search and see filtered results

**Independent Test**: Add search_fields to view class, verify search bar appears, enter search terms (including multi-word searches), confirm only matching records are displayed using OR matching

### Verification for User Story 3

- [X] T021 [US3] Verify SearchMixin provides get_search_fields() method that returns search_fields attribute from mvp/views.py (FR-001)
- [X] T022 [US3] Verify SearchMixin._apply_search() correctly implements multi-word OR matching (fixed in T005) in mvp/views.py (FR-020)
- [X] T023 [US3] Verify SearchMixin adds search_query and is_searchable to template context in mvp/views.py get_context_data() (FR-019)
- [X] T024 [US3] Verify list_view.html template conditionally displays c-list.search-widget when is_searchable is True (FR-019)
- [X] T025 [US3] Create BasicListViewDemo in demo/views.py with search_fields = ["name", "description"] and order_by fields
- [X] T026 [US3] Add URL route for BasicListViewDemo in demo/urls.py
- [X] T027 [US3] Verify BasicListViewDemo using chrome-devtools-mcp: check search bar appears, test single-word search, test multi-word OR search (FR-020)
- [X] T028 [US3] Verify search performance with 10,000+ records meets <500ms requirement (SC-002)

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Sorting/Ordering Controls (Priority: P2)

**Goal**: Developers specify order_by fields and system automatically adds sorting dropdown in page header, users can sort by different fields in ascending/descending order

**Independent Test**: Add order_by fields to view, verify dropdown appears, select different sort options, confirm list reorders correctly with ascending/descending toggle

### Verification for User Story 4

- [X] T029 [US4] Verify OrderMixin provides get_order_by_choices() method that returns order_by attribute from mvp/views.py (FR-002)
- [X] T030 [US4] Verify OrderMixin._apply_ordering() applies selected ordering to queryset in mvp/views.py (FR-023)
- [X] T031 [US4] Verify OrderMixin adds order_by_choices and current_ordering to template context in mvp/views.py get_context_data() (FR-022)
- [X] T032 [US4] Verify list_view.html template conditionally displays c-list.order-widget when order_by_choices exists (FR-022)
- [X] T033 [US4] Verify c-list.order-widget component renders as dropdown menu in mvp/templates/cotton/list/order_widget.html (clarification Q6)
- [X] T034 [US4] Verify BasicListViewDemo (created in T025) includes order_by fields and demonstrates ordering functionality
- [X] T035 [US4] Verify BasicListViewDemo using chrome-devtools-mcp: check dropdown appears, test different sort selections, test ascending/descending toggle (FR-024)

**Checkpoint**: At this point, User Stories 1, 2, 3, AND 4 should all work independently

---

## Phase 7: User Story 5 - Filter Sidebar Integration (Priority: P3)

**Goal**: Developers use FilterView with MVPListViewMixin and system automatically detects filters, displays filter toggle in page header, opens sidebar with filter controls

**Independent Test**: Create FilterView with django-filter filters mixed with MVPListViewMixin, verify filter toggle appears, click to open sidebar, apply filters, confirm list updates accordingly

### Verification for User Story 5

- [X] T036 [US5] Verify list_view.html template detects FilterView by checking for filter or filterset_class in context
- [X] T037 [US5] Verify list_view.html template conditionally displays filter toggle button when filters are detected (FR-026)
- [X] T038 [US5] Verify c-sidebar.filter component exists and renders filter form in mvp/templates/cotton/sidebar/filter.html (FR-027-028)
- [X] T039 [US5] Verify existing ListViewDemo in demo/views.py uses FilterView with django-filter integration (FR-026-030)
- [X] T040 [US5] Verify ListViewDemo using chrome-devtools-mcp: check filter toggle appears, test sidebar open/close, test filter application with search and ordering simultaneously (FR-030)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 8: Menu Structure Updates

**Purpose**: Update navigation menu to include all demo views

- [X] T041 [P] Add "List Views" MenuGroup to demo/menus.py with items for list_view_demo (Full Demo), basic_list_demo (Basic ListView), minimal_list_demo (Minimal)
- [X] T042 [P] Add "Grid Layouts" MenuGroup to demo/menus.py with items for grid_1col_demo, grid_2col_demo, grid_3col_demo, grid_responsive_demo
- [X] T043 Verify all menu items link to correct views using chrome-devtools-mcp navigation test

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T044 [P] Verify all get_* methods can override class attributes: get_page_title(), get_grid_config(), get_search_fields(), get_order_by_choices(), get_list_item_template() in mvp/views.py (FR-010)
- [X] T045 [P] Verify empty state displays correctly when queryset is empty using c-list.empty component (FR-031)
- [X] T046 [P] Verify search, ordering, and filter states persist correctly through pagination using URL parameters (FR-034, SC-008)
- [ ] T047 Verify page header accommodates multiple widgets on small screens (375px width) using chrome-devtools-mcp (SC-007)
- [ ] T048 Verify full demo renders initial page in <2 seconds using chrome-devtools-mcp performance profiling (SC-005)
- [ ] T049 Update specs/008-dash-list-view/quickstart.md with complete examples if needed
- [ ] T050 Run final validation of all demo views using quickstart.md scenarios
- [X] T051 [P] Verify invalid grid configuration falls back to default single-column layout without errors (US2 acceptance scenario 3, edge case)
- [X] T052 [P] Verify non-existent search_fields raise clear error or are silently ignored (edge case: search_fields references non-existent model field)
- [X] T053 Verify all mixins (SearchMixin, OrderMixin, ListItemTemplateMixin) function correctly when used independently (FR-006)

---

## Phase 10: Testing (OPTIONAL - Additional Coverage)

**Purpose**: Comprehensive test coverage for mixin functionality (optional enhancement)

**Note**: Critical bug fixes (T005a, T006a) have required tests. Phase 10 provides additional comprehensive coverage if desired. Include only if exhaustive test documentation is needed.

### Unit Tests (Optional)

- [X] T054 [P] Expand tests/test_list_view_mixins.py with additional unit tests beyond T005a
- [X] T055 [P] Write SearchMixin tests: test_search_fields, test_get_search_fields, test_apply_search_single_word, test_search_context_variables
- [X] T056 [P] Write OrderMixin tests: test_order_by, test_get_order_by_choices, test_apply_ordering, test_ordering_context_variables, test_invalid_ordering
- [X] T057 [P] Write SearchOrderMixin tests: test_combined_functionality, test_search_and_order_together
- [X] T058 [P] Write ListItemTemplateMixin tests: test_list_item_template, test_get_list_item_template, test_auto_generation, test_template_names
- [X] T059 [P] Write MVPListViewMixin tests: test_grid_config, test_page_title, test_get_methods_override_attributes

### Integration Tests (Optional)

- [X] T060 [P] Expand tests/integration/test_list_view_integration.py with additional integration tests beyond T006a (NOTE: Covered by 59 existing integration tests)
- [X] T061 [P] Write integration tests: test_view_renders_correct_template, test_context_contains_expected_variables, test_search_filtering_end_to_end (NOTE: Already covered in existing tests)
- [X] T062 [P] Write integration tests: test_ordering_end_to_end, test_pagination_preserves_state, test_empty_state_displays, test_grid_configuration_passed (NOTE: Already covered in Phases 4-9 tests)

### E2E Tests (Optional)

- [ ] T063 [P] Create tests/e2e/test_list_view_e2e.py with playwright test structure (NOTE: E2E infrastructure exists, requires running server)
- [ ] T064 [P] Write E2E tests: test_page_loads_with_correct_title, test_search_bar_appears_and_filters, test_order_dropdown_appears_and_sorts (NOTE: Requires running server)
- [ ] T065 [P] Write E2E tests: test_pagination_works_with_state, test_filter_sidebar_opens_and_applies, test_grid_layouts_responsive (NOTE: Requires running server)
- [ ] T066 Write E2E test: test_multiple_widgets_on_mobile (375px width test) (NOTE: Requires running server + browser automation)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User stories CAN proceed in parallel after Phase 2 (if staffed)
  - Or sequentially in priority order: US1 (P1) → US2 (P2) → US3 (P2) → US4 (P2) → US5 (P3)
- **Menu Structure (Phase 8)**: Depends on Phase 3-7 completion (all demo views must exist)
- **Polish (Phase 9)**: Depends on all user stories being complete
- **Testing (Phase 10)**: Optional additional coverage - can run after any phase completes (Phase 2 includes required tests for bug fixes)

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories - **This is the MVP**
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent of US1, demonstrates grid configuration
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Requires multi-word OR search fix (T005)
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Independent, demonstrates ordering
- **User Story 5 (P3)**: Can start after Foundational (Phase 2) - Independent, demonstrates django-filter integration

### Within Each User Story

- Verification tasks before demo creation
- Demo creation before URL routing
- URL routing before chrome-devtools-mcp verification
- All verification complete before marking story complete

### Parallel Opportunities

**Phase 1 (Setup)**: Tasks T003 and T004 can run in parallel

**Phase 2 (Foundational)**: Tasks T005 and T006 can run in parallel (different files)

**Phase 4 (US2)**: Tasks T015-T018 can all run in parallel (creating different demo classes)

**Phase 8 (Menu)**: Tasks T041 and T042 can run in parallel (different menu groups)

**Phase 9 (Polish)**: Tasks T044, T045, T046, T051, T052 can run in parallel (different concerns)

**Phase 10 (Testing)**: Most test writing tasks can run in parallel:

- All unit test tasks (T055-T059) can run in parallel
- All integration test tasks (T061-T062) can run in parallel
- All E2E test tasks (T064-T065) can run in parallel

**Cross-Phase Parallelism**: After Phase 2 completes, Phases 3-7 can proceed in parallel if multiple developers are available

---

## Implementation Strategy

### MVP First (Recommended)

Start with **User Story 1 only** (Phase 3):

1. Complete Phase 1 (Setup verification)
2. Complete Phase 2 (Foundational fixes - T005, T006)
3. Complete Phase 3 (User Story 1 - Basic List Display)
4. Verify and validate before proceeding

This delivers immediate value: developers can create simple list views with minimal configuration.

### Incremental Delivery

After MVP, add features incrementally in priority order:

1. Phase 4 (US2 - Grid Configuration) - Visual enhancement
2. Phase 5 (US3 - Search) - Usability improvement
3. Phase 6 (US4 - Ordering) - Data navigation
4. Phase 7 (US5 - Filters) - Advanced filtering
5. Phase 8 (Menu Structure) - Navigation
6. Phase 9 (Polish) - Quality improvements
7. Phase 10 (Testing) - Optional comprehensive tests

### Parallel Development

If team capacity allows, after Phase 2:

- Developer A: US1 + US2 (Basic display and grid layouts)
- Developer B: US3 + US4 (Search and ordering)
- Developer C: US5 (Filter integration)
- Then reconvene for Phase 8-9

---

## Validation Checklist

Before considering this feature complete:

- [ ] All 5 user stories have independent test scenarios that pass
- [ ] All 34 functional requirements (FR-001 to FR-034) are implemented and verified
- [ ] All 8 success criteria (SC-001 to SC-008) are measurable and validated:
  - [ ] SC-001: Minimal example uses <10 lines of code (MinimalListViewDemo)
  - [ ] SC-002: Search returns results in <500ms for 10,000 records
  - [ ] SC-003: All operations discoverable without documentation (visual verification)
  - [ ] SC-004: Grid adapts 320px-1920px without horizontal scrolling
  - [ ] SC-005: Initial render <2 seconds for full demo view
  - [ ] SC-006: 60% time reduction (quickstart.md demonstrates)
  - [ ] SC-007: All widgets functional at 375px width
  - [ ] SC-008: State persistence through pagination verified
- [ ] All demo views render correctly and are accessible via menu
- [ ] chrome-devtools-mcp verification completed for all UI changes
- [ ] quickstart.md examples validated
- [ ] No errors in browser console for any demo view
- [ ] All get_* methods properly override class attributes
- [ ] Empty state displays correctly
- [ ] Pagination footer shows correct entry counts
- [ ] Invalid grid configurations fall back gracefully
- [ ] Non-existent search fields handled properly
- [ ] All mixins work independently

---

## Summary

**Total Tasks**: 66 (53 required + 13 optional testing tasks)
**Required Tasks**: 53 (T001-T053, includes 2 mandatory tests for bug fixes + 3 edge case verifications)
**Optional Testing Tasks**: 13 (T054-T066)
**Parallel Opportunities**: 20 tasks can run in parallel within their phases
**MVP Scope**: Phase 1 + Phase 2 + Phase 3 (User Story 1) = 15 tasks (includes T005a, T006a)
**Estimated Complexity**: Low-Medium (most implementation exists, focus on fixes and demos)

**Key Insight**: This is primarily a **verification and enhancement** feature. Most code already exists. The work focuses on:

1. Fixing multi-word OR search with test (2 tasks: T005, T005a)
2. Fixing pagination footer context with test (2 tasks: T006, T006a)
3. Creating demo views (6 tasks)
4. Verification with chrome-devtools-mcp (8 tasks)
5. Edge case verification (3 tasks: T051-T053)
6. Documentation validation (2 tasks)
7. Optional comprehensive testing (13 tasks)
