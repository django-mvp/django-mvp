---
description: "Task list for implementing configurable site navigation menu system"
---

# Tasks: Configurable Site Navigation Menu System

**Input**: Design documents from `/specs/004-site-navigation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests are REQUIRED for all behavior changes. Use pytest + pytest-django for backend/menu rendering.

**Constitutional Requirements (v1.1.0)**:

- **Test-First (I)**: All tests MUST be written and FAIL before implementation
- **Documentation-First (II)**: Context7 MUST be used for up-to-date library documentation
- **UI Verification (VI)**: chrome-devtools-mcp MUST verify UI changes in browser
- **E2E Testing (VIII)**: playwright MUST test complete user workflows

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

### Context7 Documentation Retrieval (Constitutional Requirement VII)

- [X] T001 [P] Retrieve django-flex-menus documentation via Context7 for current API patterns
- [X] T002 [P] Retrieve django-cotton documentation via Context7 for component best practices
- [X] T003 [P] Retrieve AdminLTE 4 documentation via Context7 for navigation CSS classes

### Project Setup

- [X] T004 Create empty AppMenu instance in mvp/menus.py with django-flex-menus
- [X] T005 [P] Create AdminLTERenderer class scaffold in mvp/renderers.py
- [X] T006 [P] Create template directory structure: mvp/templates/menus/ and mvp/templates/cotton/app/sidebar/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Verify django-flex-menus is installed and properly configured in INSTALLED_APPS
- [X] T008 [P] Create base renderer template structure: menus/container.html for depth 0
- [X] T009 [P] Implement AdminLTERenderer.templates dict with depth-based template mapping
- [X] T010 [P] Create test fixtures and utilities in tests/conftest.py for menu testing

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 3 & 4 - Empty Menu & Python API (Priority: P1) 🎯 MVP

**Goal**: Provide empty AppMenu that developers can populate programmatically using Python

**Independent Test**: Install django-mvp, verify sidebar renders empty, then add one MenuItem via Python and confirm it appears

**Why grouped**: These stories are tightly coupled - the empty menu IS the Python API foundation. They must work together.

### Tests for US3 & US4 (Write FIRST, ensure they FAIL)

- [X] T011 [P] [US3] Test empty AppMenu renders without items in tests/test_menu_definition.py
- [X] T012 [P] [US3] Test sidebar renders empty menu structure in tests/test_menu_rendering.py
- [X] T013 [P] [US4] Test MenuItem creation with name and view_name in tests/test_menu_definition.py
- [X] T014 [P] [US4] Test MenuItem with extra_context (label, icon) in tests/test_menu_definition.py
- [X] T015 [P] [US4] Test adding MenuItem to AppMenu.children in tests/test_menu_definition.py

### Implementation for US3 & US4

- [X] T016 [US3] [US4] Implement AppMenu = Menu("AppMenu", children=[]) in mvp/menus.py
- [X] T017 [US3] Update mvp app ready() method to ensure menus module loads
- [X] T018 [P] [US4] Document AppMenu usage in mvp/menus.py docstring
- [X] T019 [US4] Create demo/menus.py showing how to import and extend AppMenu

**Checkpoint**: Developers can now define menus in Python. AppMenu is empty by default.

---

## Phase 4: User Story 1 - Single Top-Level Menu Items (Priority: P1)

**Goal**: Render single menu items (no children) at the top of the sidebar

**Independent Test**: Define 2-3 MenuItem instances without children, verify they render as links in correct order

### Tests for US1 (Write FIRST, ensure they FAIL)

- [X] T020 [P] [US1] Test single item renders with label and URL in tests/test_menu_rendering.py
- [X] T021 [P] [US1] Test single item renders with icon in tests/test_menu_rendering.py
- [X] T022 [P] [US1] Test multiple single items render in declaration order in tests/test_menu_rendering.py
- [X] T023 [P] [US1] Test single items appear before groups in tests/test_menu_rendering.py

### Implementation for US1

- [X] T024 [P] [US1] Create menus/single-item.html template for leaf items
- [X] T025 [US1] Implement AdminLTERenderer.get_context_data() to extract label, url, icon from extra_context in mvp/renderers.py
- [X] T026 [US1] Implement AdminLTERenderer.sort_items() to separate singles from groups in mvp/renderers.py
- [X] T027 [US1] Update AdminLTERenderer to use sort_items() at depth 1 in mvp/renderers.py
- [X] T028 [P] [US1] Integrate django-easy-icons in single-item.html template for icon rendering
- [X] T029 [P] [US1] Add URL resolution via Django reverse() in get_context_data() in mvp/renderers.py

**Checkpoint**: Single menu items render correctly at the top of the sidebar with labels, URLs, and icons

---

## Phase 5: User Story 2 - Hierarchical Menu Groups (Priority: P2)

**Goal**: Render menu items with children as expandable groups with headers

**Independent Test**: Define MenuItem with children, verify it renders as group with header below single items

### Tests for US2 (Write FIRST, ensure they FAIL)

- [X] T030 [P] [US2] Test parent item with children renders below singles in tests/test_menu_rendering.py
- [X] T031 [P] [US2] Test group header renders when group_header in extra_context in tests/test_menu_rendering.py
- [X] T032 [P] [US2] Test nested children render indented under parent in tests/test_menu_rendering.py
- [X] T033 [P] [US2] Test multiple groups render in declaration order in tests/test_menu_rendering.py
- [X] T034 [P] [US2] Test nested items use nav-treeview class in tests/test_menu_rendering.py

### Implementation for US2

- [X] T035 [P] [US2] Create menus/parent-item.html template for items with children
- [X] T036 [P] [US2] Create menus/nested-item.html template for depth 2+ leaf items
- [X] T037 [P] [US2] Create menus/nested-parent.html template for depth 2+ parent items
- [X] T038 [US2] Add has_children detection in get_context_data() in mvp/renderers.py
- [X] T039 [US2] Add group_header rendering logic in parent-item.html template
- [X] T040 [US2] Implement nav-arrow icon for expandable parents in parent-item.html
- [X] T041 [US2] Add nav-treeview nested list structure in parent-item.html
- [X] T042 [P] [US2] Update AdminLTERenderer templates dict to map depth 2+ to nested templates in mvp/renderers.py

**Checkpoint**: Hierarchical menus render correctly with groups appearing after singles, proper nesting, and headers

---

## Phase 6: Active State & Additional Features

**Goal**: Highlight current page and add badge support

### Tests for Active State

- [X] T043 [P] Test active state detection compares request URL with view_name in tests/test_custom_renderer.py
- [X] T044 [P] Test active class applied to current menu item in tests/test_menu_rendering.py
- [X] T045 [P] Test menu-open class applied to parent with active child in tests/test_custom_renderer.py

### Implementation for Active State

- [X] T046 [P] Implement is_active detection in get_context_data() using request.resolver_match in mvp/renderers.py
- [X] T047 [P] Implement _has_active_descendant() helper method in mvp/renderers.py
- [X] T048 [P] Add is_open flag for parents with active children in get_context_data() in mvp/renderers.py
- [X] T049 [P] Update single-item.html and parent-item.html to apply active/menu-open classes

### Tests for Badges

- [X] T047 [P] Test badge renders when badge in extra_context in tests/test_menu_rendering.py
- [X] T048 [P] Test badge_classes applied correctly in tests/test_menu_rendering.py

### Implementation for Badges

- [X] T049 [P] Add has_badge flag to get_context_data() in mvp/renderers.py
- [X] T050 [P] Add badge rendering in parent-item.html template with nav-badge class

### UI Verification (Constitutional Requirement VI)

- [ ] T051 [P] Use chrome-devtools-mcp to verify menu items render without all having active class
- [ ] T052 [P] Use chrome-devtools-mcp to verify active menu item highlights correctly on current page
- [ ] T053 [P] Use chrome-devtools-mcp to verify menu groups expand when parent has active child
- [ ] T054 [P] Use chrome-devtools-mcp to verify badge rendering appears correctly on menu items

### End-to-End Testing (Constitutional Requirement VIII)

- [ ] T055 [P] Create playwright test for complete menu navigation workflow from page load to menu click
- [ ] T056 [P] Create playwright test for active state highlighting during page navigation
- [ ] T057 [P] Create playwright test for hierarchical menu expansion and collapse functionality
- [ ] T058 [P] Create playwright test for menu accessibility (keyboard navigation, screen reader support)

---

## Phase 7: Integration & Multi-App Support

**Goal**: Support multiple Django apps contributing menu items

### Tests for Integration

- [X] T059 [P] Test menu items from multiple apps render in INSTALLED_APPS order in tests/test_menu_integration.py
- [X] T060 [P] Test menu survives app reload without errors in tests/test_menu_integration.py
- [X] T061 [P] Test parameterized URLs resolve correctly in tests/test_menu_integration.py

### Implementation for Integration

- [X] T062 [P] Update demo/menus.py with comprehensive examples showing all features
- [X] T063 [P] Create demo/apps.py with ready() method importing menus module
- [X] T064 [P] Add example URL patterns in demo/urls.py for menu testing

---

## Phase 8: Cotton Components (Optional Sugar)

**Goal**: Provide reusable Cotton components for custom menu implementations

### Tests for Cotton Components

- [X] T065 [P] Test menu.item.html component renders with c-vars in tests/test_menu_rendering.py
- [X] T066 [P] Test menu-header.html component renders with c_label in tests/test_menu_rendering.py
- [X] T067 [P] Test menu.item with children slot renders correctly in tests/test_menu_rendering.py

### Implementation for Cotton Components

- [X] T068 [P] Create cotton/app/sidebar/menu.item.html component with c-vars
- [X] T069 [P] Create cotton/app/sidebar/menu-header.html component with c_label
- [X] T070 [P] Create cotton/app/sidebar/menu.html container component (optional)

---

## Phase 9: Documentation & Polish

**Purpose**: Finalize documentation and ensure everything is production-ready

- [X] T071 [P] Update README.md with navigation menu example and quickstart link
- [X] T072 [P] Add menu system section to docs/index.md
- [X] T073 [P] Create docs/navigation.md with detailed menu documentation
- [X] T074 [P] Add inline docstrings to AdminLTERenderer methods in mvp/renderers.py
- [X] T075 [P] Add type hints to AppMenu and renderer methods in mvp/menus.py and mvp/renderers.py
- [X] T076 [P] Update CHANGELOG.md with menu system feature
- [X] T077 Run pytest to verify all tests pass
- [X] T078 Run ruff check and format on mvp/ directory
- [X] T079 Run djlint on templates in mvp/templates/
- [X] T080 Validate quickstart.md works end-to-end with fresh Django project

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **US3 & US4 (Phase 3)**: Depend on Foundational - Foundation for all other stories
- **US1 (Phase 4)**: Depends on Phase 3 - Can run independently after
- **US2 (Phase 5)**: Depends on Phase 4 (needs single-item rendering working)
- **Active State (Phase 6)**: Depends on Phase 4 & 5 (needs menu rendering complete)
- **Integration (Phase 7)**: Depends on all previous user stories
- **Cotton Components (Phase 8)**: Depends on Phase 4 & 5 (optional enhancement)
- **Documentation (Phase 9)**: Depends on all implementation phases

### User Story Completion Order

1. **MVP (Phase 3)**: US3 & US4 together - Empty menu + Python API
2. **Phase 4**: US1 - Single menu items (builds on MVP)
3. **Phase 5**: US2 - Hierarchical groups (builds on US1)
4. **Phase 6+**: Enhancements (active state, badges, etc.)

### Within Each Phase

- Tests MUST be written and FAIL before implementation
- Core renderer logic before templates
- Templates before integration
- Each user story complete before moving to next priority

### Parallel Opportunities Per User Story

#### Phase 3 (US3 & US4) - Can run in parallel after foundational

```bash
# Terminal 1: Write tests
pytest tests/test_menu_definition.py::test_empty_menu
pytest tests/test_menu_definition.py::test_menuitem_creation

# Terminal 2: Implement AppMenu
# Edit mvp/menus.py

# Terminal 3: Create examples
# Edit demo/menus.py
```

#### Phase 4 (US1) - Can run in parallel after Phase 3

```bash
# Terminal 1: Write all tests (T017-T020)
pytest tests/test_menu_rendering.py::test_single_item*

# Terminal 2: Create templates (T021)
# Edit menus/single-item.html

# Terminal 3: Implement renderer (T022-T024, T026)
# Edit mvp/renderers.py
```

#### Phase 5 (US2) - Can run in parallel after Phase 4

```bash
# Terminal 1: Write all tests (T027-T031)
pytest tests/test_menu_rendering.py::test_group*

# Terminal 2: Create templates (T032-T034)
# Edit menus/parent-item.html, nested-*.html

# Terminal 3: Update renderer (T035, T039)
# Edit mvp/renderers.py
```

---

## Implementation Strategy

### MVP-First Approach

**Minimum Viable Product** = Phase 1 + Phase 2 + Phase 3 (US3 & US4)

This delivers:

- Empty AppMenu instance
- Python API for defining menus
- Developer can import AppMenu and add items

**Time estimate**: ~4-6 hours

### Incremental Delivery

1. **MVP (Phases 1-3)**: Empty menu + Python API - Developers can define menus
2. **+ US1 (Phase 4)**: Single items render - Basic navigation works
3. **+ US2 (Phase 5)**: Hierarchical menus - Full navigation system
4. **+ Enhancements (Phase 6-8)**: Active state, badges, Cotton components
5. **+ Documentation (Phase 9)**: Production-ready release

### Validation Checkpoints

After each phase, validate:

- [ ] All tests for that phase pass
- [ ] Ruff linting passes
- [ ] djlint passes on templates
- [ ] Manual smoke test of feature works
- [ ] Documentation updated for new behavior

---

## Test Coverage Requirements

### Required Test Coverage

- Menu definition API (MenuItem creation, AppMenu extension)
- Menu rendering (single items, groups, nesting)
- Renderer logic (sorting, template selection, context enrichment)
- Active state detection
- Integration (multi-app, URL resolution)

### Test Organization

```text
tests/
├── test_menu_definition.py      # T011-T015: MenuItem & AppMenu API
├── test_menu_rendering.py       # T020-T023, T027-T031, T047-T048: Template rendering
├── test_custom_renderer.py      # T040-T042: Renderer logic
└── test_menu_integration.py     # T051-T053: Multi-app integration
```

### Constitution Compliance

✅ **Test-First**: All behavior tests written before implementation
✅ **Documentation**: README, docs/, inline docstrings, quickstart.md
✅ **Quality Gates**: pytest, ruff, djlint all pass before merge

---

## Summary

**Total tasks**: 80 (+8 constitutional requirements)
**User story phases**: 3 (US3+US4, US1, US2)
**Test tasks**: 29 (36%) - includes constitutional E2E testing
**Implementation tasks**: 51 (64%)

**Constitutional Compliance Tasks**:

- **Context7 Documentation**: T001-T003 (3 tasks)
- **UI Verification**: T051-T054 (4 tasks)
- **E2E Testing**: T055-T058 (4 tasks)

**Parallel opportunities**:

- Phase 1: 2 of 3 tasks can run in parallel
- Phase 2: 3 of 4 tasks can run in parallel
- Phase 3: 4 of 5 test tasks can run in parallel
- Phase 4: Tests, templates, and renderer can proceed in parallel
- Phase 5: Tests, templates, and renderer updates can proceed in parallel
- Phase 6-9: Most tasks can run in parallel

**MVP Scope**: Phases 1-3 (Tasks T001-T016) = ~20% of total work
**Full Feature**: All phases = 100%

**Suggested approach**: Implement MVP first, validate with users, then incrementally add US1 → US2 → enhancements.
