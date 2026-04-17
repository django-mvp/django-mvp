# Tasks: Django Tables2 Integration

**Input**: Design documents from `/specs/007-datatables-integration/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Workflow**: Following Design-First approach - implement and verify design BEFORE writing tests. Tests are REQUIRED for behavior changes but come AFTER design verification. Use pytest + pytest-django for backend/integration and pytest-playwright for UI behavior. End-to-end tests with playwright are REQUIRED for all features. UI changes MUST be verified using chrome-devtools-mcp DURING implementation. Use context7 for up-to-date library documentation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. Each story follows: Design → Implement → Verify → Test.

## Format: `- [ ] [ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency configuration

- [X] T001 Add django-tables2>=2.0.0,<3.0.0 to pyproject.toml [tool.poetry.extras] section as "datatables2" optional dependency
- [X] T002 [P] Add django-tables2>=2.0.0,<3.0.0 to pyproject.toml [tool.poetry.group.dev.dependencies] section
- [X] T003 [P] Run poetry lock to update lock file with new dependencies
- [X] T004 Update CHANGELOG.md with new feature: Django Tables2 integration as optional dependency

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Verify existing Product model has adequate fields for table demo (demo/models.py lines 34-80)
- [X] T006 Verify existing generate_dummy_data command creates sufficient products (demo/management/commands/generate_dummy_data.py)
- [X] T007 Run generate_dummy_data command to ensure test data exists: `poetry run python manage.py generate_dummy_data`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Installing DataTables Support (Priority: P1) 🎯 MVP

**Goal**: Enable developers to install django-tables2 as an optional dependency using pip extras syntax

**Independent Test**: Run `pip install django-mvp[datatables2]` in a clean environment and verify django-tables2 is installed

### Design & Implementation for User Story 1

> **NOTE: Implementation is configuration-only - no runtime code needed**

- [X] T008 [US1] Verify pyproject.toml [tool.poetry.extras] includes datatables2 = ["django-tables2"]
- [X] T009 [US1] Verify pyproject.toml [tool.poetry.group.dev.dependencies] includes django-tables2
- [X] T010 [US1] Test installation in clean virtual environment: `pip install -e .[datatables2]`

### Verification for User Story 1

- [X] T011 [US1] Verify django-tables2 package is importable after pip install with extras
- [X] T012 [US1] Verify poetry install --extras datatables2 works correctly

### Tests for User Story 1

> **NOTE: Packaging tests are manual verification - no automated tests needed for dependency installation**

**Checkpoint**: At this point, User Story 1 should be fully functional - developers can install django-mvp with DataTables support

---

## Phase 4: User Story 2 - Viewing DataTables Demo Page (Priority: P2)

**Goal**: Create a demo page accessible via sidebar menu that displays a working data table within MVP layout

**Independent Test**: Navigate to DataTables Demo menu item and verify table displays with Product data

### Design & Implementation for User Story 2

- [X] T013 [P] [US2] Create ProductTable class in demo/tables.py with django-tables2 Table configuration
- [X] T014 [US2] Define ProductTable.Meta: model=Product, template_name, attrs for Bootstrap 5 + ARIA
- [X] T015 [P] [US2] Configure ProductTable columns: price (text-end), status (text-center), category (FK accessor), rating, stock, dates
- [X] T016 [P] [US2] Set ProductTable empty_text: "No products available. Run 'poetry run python manage.py generate_dummy_data' to create sample data."
- [X] T017 [US2] Create DataTablesView class in demo/views.py extending SingleTableView
- [X] T018 [US2] Configure DataTablesView: model=Product, table_class=ProductTable, template_name="demo/datatables_demo.html", paginate_by=25
- [X] T019 [US2] Override get_context_data() in DataTablesView to add page_title='Django Tables2 Demo' and breadcrumbs
- [X] T020 [US2] Add URL pattern in demo/urls.py: path('datatables-demo/', DataTablesView.as_view(), name='datatables_demo')
- [X] T021 [US2] Create demo/templates/demo/datatables_demo.html extending mvp/base.html (standard mode first)
- [X] T022 [US2] Implement datatables_demo.html blocks: page_title, breadcrumbs, content with card wrapper
- [X] T023 [US2] Add {% load render_table from django_tables2 %} and {% render_table table %} in template content block
- [X] T024 [US2] Register new "Integrations" MenuGroup in demo/menus.py (register EARLY for correct positioning)
- [X] T025 [US2] Add "DataTables Demo" MenuItem under Integrations group with route='datatables_demo', icon='table', text='DataTables Demo'

### Verification for User Story 2

- [X] T026 [US2] Use chrome-devtools-mcp to navigate to /datatables-demo/ URL
- [X] T027 [US2] Take snapshot with chrome-devtools-mcp to verify MVP layout (header, sidebar, content, footer)
- [X] T028 [US2] Verify "Integrations" menu group appears before "Tools & Utilities" in sidebar
- [X] T029 [US2] Verify table displays Product data with 18 columns and 27+ rows
- [X] T030 [US2] Verify sorting works: click column headers and verify sort indicators
- [X] T031 [US2] Verify pagination works: navigate between pages
- [X] T032 [US2] Verify empty state: empty_text configured in ProductTable.Meta with helpful message

### Tests for User Story 2 (AFTER design verification)

- [X] T033 [P] [US2] Unit test ProductTable configuration in tests/test_datatables_integration.py
- [X] T034 [P] [US2] Unit test DataTablesView attributes (model, table_class, template_name, paginate_by)
- [X] T035 [P] [US2] Integration test URL routing: test client.get('/datatables-demo/') returns 200
- [X] T036 [P] [US2] Integration test template rendering: verify 'table' in response.context
- [X] T037 [P] [US2] Integration test template uses correct base template
- [ ] T038 [US2] End-to-end test with pytest-playwright in tests/test_datatables_e2e.py: navigate to demo page and verify table renders
- [ ] T039 [US2] E2E test sorting: click column header and verify rows reorder
- [ ] T040 [US2] E2E test pagination: click page 2 and verify different products display
- [ ] T041 [US2] E2E test keyboard navigation: tab through table headers and pagination links

**Checkpoint**: At this point, User Story 2 should be fully functional - users can view a working data table in MVP layout

---

## Phase 5: User Story 3 - Fill Mode Table Display (Priority: P2)

**Goal**: Implement fill mode where table expands to viewport height with independent scrolling

**Independent Test**: Enable fill mode and verify table fills available vertical space and scrolls independently

### Design & Implementation for User Story 3

- [ ] T042 [US3] Create demo/templates/demo/datatables_demo_fill.html template extending mvp/base.html
- [ ] T043 [US3] Implement fill mode layout in datatables_demo_fill.html using Bootstrap 5 flexbox utilities (d-flex, flex-column, h-100)
- [ ] T044 [US3] Wrap table-responsive div with flex-grow-1 class to fill remaining vertical space
- [ ] T045 [US3] Add overflow-auto or overflow-hidden to table container for independent scrolling
- [ ] T046 [US3] Update DataTablesView to use datatables_demo_fill.html template for fill mode (separate route or view parameter)
- [ ] T047 [US3] (Optional Enhancement) Add mode toggle UI in template if implementing FR-015 (button/link to switch between standard and fill mode)

### Verification for User Story 3

- [ ] T048 [US3] Use chrome-devtools-mcp to navigate to datatables demo in fill mode
- [ ] T049 [US3] Take screenshot showing table fills viewport height between header and footer
- [ ] T050 [US3] Verify scrolling: use chrome-devtools-mcp to scroll within table and verify header/sidebar remain fixed
- [ ] T051 [US3] Resize browser window with chrome-devtools-mcp and verify table height adjusts to maintain fill
- [ ] T052 [US3] Test on mobile viewport (320px width) and verify responsive behavior
- [ ] T053 [US3] Verify horizontal scrolling works for 18 columns on narrow viewports

### Tests for User Story 3 (AFTER design verification)

- [ ] T054 [P] [US3] Integration test fill mode template selection based on configuration
- [ ] T055 [US3] E2E test fill mode in pytest-playwright: verify table height fills viewport
- [ ] T056 [US3] E2E test independent scrolling: scroll table and verify page doesn't scroll
- [ ] T057 [US3] E2E test responsive resize: resize window and verify table adjusts height
- [ ] T058 [US3] E2E test horizontal scroll: verify table scrolls horizontally on narrow viewport

**Checkpoint**: At this point, User Story 3 should be fully functional - fill mode works with independent table scrolling

---

## Phase 6: User Story 4 - Auto Height Mode Display (Priority: P3)

**Goal**: Ensure standard (non-fill) mode displays table with automatic content-based height

**Independent Test**: View demo in standard mode and verify table height matches content and page scrolls normally

### Design & Implementation for User Story 4

- [ ] T059 [US4] Verify demo/templates/demo/datatables_demo.html uses standard layout (content-based height)
- [ ] T060 [US4] Ensure no h-100 or flex-grow-1 classes on table container in standard mode
- [ ] T061 [US4] Verify table-responsive div allows normal page scrolling behavior

### Verification for User Story 4

- [ ] T062 [US4] Use chrome-devtools-mcp to navigate to datatables demo in standard mode
- [ ] T063 [US4] Take screenshot showing table height matches content (not filling viewport)
- [ ] T064 [US4] Verify page scrolling: scroll page and verify entire layout moves together (header, table, footer)
- [ ] T065 [US4] (Optional) Verify mode toggle if implemented: switch from fill to standard and verify layout updates without page reload

### Tests for User Story 4 (AFTER design verification)

- [ ] T066 [P] [US4] Integration test standard mode uses correct template
- [ ] T067 [US4] E2E test standard mode in pytest-playwright: verify table height is content-based
- [ ] T068 [US4] E2E test page scrolling: scroll page and verify all elements move together
- [ ] T069 [US4] E2E test mode toggle: switch modes and verify layout changes dynamically

**Checkpoint**: All user stories should now be independently functional - both fill and standard modes work correctly

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T070 [P] Create mvp/templates/django_tables2/ directory for template overrides
- [ ] T071 [P] Create mvp/templates/django_tables2/bootstrap5-responsive.html extending django_tables2 base template
- [ ] T072 [P] Override table.html block in bootstrap5-responsive.html to add AdminLTE 4 specific styling
- [ ] T073 [P] Add ARIA attributes to column headers in template override (role="columnheader", aria-sort)
- [ ] T074 [P] Customize pagination.html template override with Bootstrap 5 pagination and aria-label
- [ ] T075 [P] Add visually-hidden spans to sort links for screen reader support
- [ ] T076 [P] Update quickstart.md reference in main documentation (if applicable)
- [ ] T077 [P] Update README.md with DataTables integration example (if applicable)
- [ ] T078 [P] Verify ARIA compliance: run accessibility audit with chrome-devtools-mcp
- [ ] T079 [P] Verify keyboard navigation: test all interactive elements with Tab key
- [ ] T080 [P] Run djlint on all template files: `poetry run djlint mvp/templates/ demo/templates/`
- [ ] T081 [P] Run ruff linting: `poetry run ruff check .`
- [ ] T082 [P] Run ruff formatting: `poetry run ruff format .`
- [ ] T083 Run all tests: `poetry run pytest`
- [ ] T084 Verify demo works with different product counts (0, 10, 50, 100 products)
- [ ] T085 Performance verification: measure table load time (<1s) and interaction response (<200ms)
- [ ] T086 Final review: Follow quickstart.md validation steps to ensure feature works end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 (Installing) can complete first (just configuration)
  - US2 (Viewing Demo) provides base implementation
  - US3 (Fill Mode) and US4 (Auto Height) can proceed in parallel after US2
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1 - Installing)**: Can start after Setup (Phase 1) - No dependencies on other stories
- **User Story 2 (P2 - Viewing Demo)**: Can start after Foundational (Phase 2) - Requires Product model and data
- **User Story 3 (P2 - Fill Mode)**: Depends on User Story 2 completion - Extends base demo page
- **User Story 4 (P3 - Auto Height)**: Can verify in parallel with US3 - Uses base template from US2

### Within Each User Story

- Design & Implementation → Verification → Tests (design-first workflow)
- ProductTable before DataTablesView (table class needed by view)
- View before Template (view referenced in URL, template used by view)
- URL and Menu after View (need view to route to)
- Template overrides in Polish phase (after base functionality verified)

### Parallel Opportunities

**Setup Phase**:

- T002 (dev dependency) and T001 (optional dependency) can run in parallel
- T003 (poetry lock) must wait for T001 and T002

**Foundational Phase**:

- T005, T006 (verification tasks) can run in parallel
- T007 (run command) after verifications

**User Story 2**:

- T013, T015, T016 (ProductTable columns) can run in parallel
- T017-T019 (DataTablesView) after ProductTable
- T021-T023 (Template) can develop in parallel with View
- T024-T025 (Menu) can develop in parallel with Template

**User Story 2 Tests**:

- T033-T037 (unit/integration tests) can all run in parallel
- T038-T041 (E2E tests) can run in parallel

**User Story 3**:

- T042-T045 (template implementation) can proceed together
- T046-T047 (view updates) in parallel with template

**User Story 3 Tests**:

- T054 (integration) and T055-T058 (E2E) can run in parallel

**Polish Phase**:

- T070-T075 (template overrides) can run in parallel
- T076-T079 (documentation/verification) can run in parallel
- T080-T082 (linting/formatting) can run in parallel
- T083-T086 must run sequentially after other polish tasks

### Suggested MVP Scope (Single Developer)

**Minimum Viable Product (US1 + US2 only)**:

1. Complete Phase 1 (Setup) - ~30 min
2. Complete Phase 2 (Foundational) - ~15 min
3. Complete Phase 3 (US1) - ~30 min (mostly verification)
4. Complete Phase 4 (US2) - ~4-6 hours
5. Skip US3, US4 for initial MVP
6. Run critical polish tasks: T078-T086

**Estimated Time**: 6-8 hours for working demo page with basic table display

**Incremental Delivery**:

- MVP (US1+US2): Basic demo page with standard table display
- v1.1 (add US3): Fill mode support
- v1.2 (add US4): Verified auto height mode
- v1.3 (Polish): Template overrides, ARIA compliance, full test coverage

---

## Implementation Strategy

### Recommended Approach

1. **Start with MVP Scope**: Implement US1 (configuration) and US2 (basic demo page) first
2. **Verify Design Early**: Use chrome-devtools-mcp after each UI task to catch issues immediately
3. **Use Existing Infrastructure**: Leverage Product model and generate_dummy_data command (no new models needed)
4. **Test Incrementally**: Write tests after each user story is visually verified
5. **Polish Last**: Template overrides and advanced ARIA features in final phase

### Task Execution Tips

- Follow the checkbox format strictly: `- [ ] [ID] [P?] [Story] Description with file path`
- Mark tasks as complete by changing `- [ ]` to `- [x]`
- Use [P] marker to identify tasks that can run in parallel
- Reference file paths in every task description for clarity
- Run linting/formatting frequently during implementation
- Commit after each completed user story for incremental progress

### Testing Strategy

- **Unit Tests**: Verify table configuration, view context, column definitions
- **Integration Tests**: Test URL routing, template rendering, menu registration
- **E2E Tests**: Use pytest-playwright to test full user journeys (navigate, sort, paginate, scroll)
- **Visual Tests**: Use chrome-devtools-mcp snapshots to verify layout at key breakpoints
- **Accessibility Tests**: Verify ARIA attributes and keyboard navigation in E2E tests

---

## Total Task Count: 86 tasks

- Setup: 4 tasks
- Foundational: 3 tasks
- User Story 1 (P1): 5 tasks
- User Story 2 (P2): 29 tasks
- User Story 3 (P2): 17 tasks
- User Story 4 (P3): 11 tasks
- Polish: 17 tasks

**Estimated Effort**: 20-30 hours for complete implementation with full test coverage
**MVP Effort**: 6-8 hours (Setup + Foundational + US1 + US2 + critical polish)
