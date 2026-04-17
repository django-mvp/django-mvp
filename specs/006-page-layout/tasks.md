# Tasks: Inner Layout System

**Input**: Design documents from `/specs/006-page-layout/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Workflow**: Following Design-First approach - implement and verify design BEFORE writing tests. UI changes MUST be verified using chrome-devtools-mcp DURING implementation. Use context7 for up-to-date library documentation.

**Organization**: Tasks are grouped by user story (US1: Basic Layout, US2: Secondary Sidebar, US3: Template Configuration) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 0: Demo View & Navigation Setup ✅ COMPLETE

**Purpose**: Create demo page infrastructure to enable visual monitoring of implementation progress

- [x] T001 Create page_layout_demo view function in demo/views.py
- [x] T002 Add URL pattern to demo/urls.py for page-layout demo
- [x] T003 Create/update demo template at demo/templates/demo/page_layout.html
- [x] T004 Verify menu item exists in demo/menus.py

**Checkpoint**: Demo page accessible at `/page-layout/` with configuration form ✅

---

## Phase 1: Foundational (Blocking Prerequisites) ✅ COMPLETE

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 [P] Verify main component template mvp/templates/cotton/inner/index.html accepts all attributes (fixed_header, fixed_footer, fixed_sidebar, sidebar_expand, class)
- [x] T006 [P] Create SCSS base file mvp/static/mvp/scss/page-layout.scss with CSS Grid structure
- [x] T007 [P] Create JavaScript base file mvp/static/mvp/js/page-layout.js with sidebar toggle skeleton
- [x] T008 Add page-layout.scss import to main SCSS manifest file (already in base.html with django-compressor)
- [x] T009 Add page-layout.js script tag to base template or configure django-compressor (already in base.html)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel ✅

---

## Phase 2: User Story 1 - Basic Inner Layout Usage (Priority: P1) 🎯 MVP

**Goal**: Developers can create full-screen layouts with fixed toolbar and footer, content fills available space

**Independent Test**: Create a page with inner layout using toolbar and main content, verify content fills space and toolbar remains visible during scrolling

### Design & Implementation for User Story 1

> **NOTE: Implement FIRST, verify design meets expectations, THEN write tests**

#### Sub-Components (Parallel)

- [x] T010 [P] [US1] Create/verify toolbar component at mvp/templates/cotton/inner/toolbar.html
- [x] T011 [P] [US1] Create/verify footer component at mvp/templates/cotton/inner/footer.html
- [x] T012 [P] [US1] Create/verify toolbar widget component at mvp/templates/cotton/inner/toolbar/widget.html (expand/collapse icon)

#### CSS Grid Layout

- [x] T013 [US1] Implement CSS Grid structure in mvp/static/scss/page-layout.scss (.page-layout container with grid-template-areas)
- [x] T014 [US1] Add grid area assignments in page-layout.scss (.page-toolbar, .page-content, .page-footer)
- [x] T015 [US1] Implement toolbar styles in page-layout.scss (grid-area: toolbar, min-content height)
- [x] T016 [US1] Implement footer styles in page-layout.scss (grid-area: footer, min-content height)
- [x] T017 [US1] Implement main content area styles in page-layout.scss (grid-area: main, fills available space)

#### Sticky Positioning

- [x] T018 [US1] Add sticky toolbar styles in page-layout.scss (.page-layout.toolbar-fixed .page-toolbar with position: sticky, top: 0)
- [x] T019 [US1] Add sticky footer styles in page-layout.scss (.page-layout.footer-fixed .page-footer with position: sticky, bottom: 0)
- [x] T020 [US1] Add z-index management for sticky elements in page-layout.scss

#### Template Integration

- [x] T021 [US1] Update main component mvp/templates/cotton/inner/index.html to apply CSS classes based on toolbar_fixed attribute
- [x] T022 [US1] Update main component mvp/templates/cotton/inner/index.html to apply CSS classes based on footer_fixed attribute
- [x] T023 [US1] Ensure toolbar and footer slots render with correct grid areas in index.html

### Verification for User Story 1

- [ ] T024 [US1] Verify toolbar displays at top using chrome-devtools-mcp on demo page
- [ ] T025 [US1] Verify content area fills available space using chrome-devtools-mcp
- [ ] T026 [US1] Verify sticky toolbar behavior on scroll using chrome-devtools-mcp
- [ ] T027 [US1] Verify sticky footer behavior on scroll using chrome-devtools-mcp
- [ ] T028 [US1] Verify CSS Grid structure in DevTools (grid-template-areas, grid-template-rows)

### Tests for User Story 1 (AFTER design verification)

- [ ] T029 [P] [US1] Create unit test file tests/components/test_page_layout_basic.py
- [ ] T030 [P] [US1] Test toolbar slot rendering in test_page_layout_basic.py using cotton_render()
- [ ] T031 [P] [US1] Test footer slot rendering in test_page_layout_basic.py using cotton_render()
- [ ] T032 [P] [US1] Test toolbar_fixed attribute applies correct CSS class in test_page_layout_basic.py
- [ ] T033 [P] [US1] Test footer_fixed attribute applies correct CSS class in test_page_layout_basic.py
- [ ] T034 [P] [US1] Test main content area renders with default slot in test_page_layout_basic.py
- [ ] T035 [US1] Create E2E test file tests/e2e/test_page_layout_basic_e2e.py with pytest-playwright
- [ ] T036 [US1] Test sticky toolbar on scroll in test_page_layout_basic_e2e.py
- [ ] T037 [US1] Test sticky footer on scroll in test_page_layout_basic_e2e.py
- [ ] T038 [US1] Test content scrolling behavior in test_page_layout_basic_e2e.py

**Checkpoint**: At this point, User Story 1 should be fully functional - toolbar, footer, main content area with sticky positioning ✅

---

## Phase 3: User Story 2 - Secondary Sidebar Integration (Priority: P2)

**Goal**: Developers can add a right-side sidebar with configurable width and toggle functionality

**Independent Test**: Create a page with inner layout including right sidebar, verify sidebar displays correctly and content area adjusts

### Design & Implementation for User Story 2

> **NOTE: Implement FIRST, verify design meets expectations, THEN write tests**

#### Sidebar Component

- [x] T039 [US2] Create/verify sidebar component at mvp/templates/cotton/inner/sidebar.html with collapsed attribute
- [x] T040 [US2] Add sidebar grid area to CSS Grid in mvp/static/mvp/scss/_page-layout.scss (update grid-template-columns to include auto for sidebar)
- [x] T041 [US2] Update grid-template-areas in _page-layout.scss to include sidebar column
- [x] T042 [US2] Implement sidebar base styles in _page-layout.scss (.page-sidebar, grid-area: sidebar, default width)

#### Sidebar Toggle Functionality

- [x] T043 [US2] Implement collapsed state styles in _page-layout.scss (.page-sidebar.collapsed with width: 0, overflow: hidden)
- [x] T044 [US2] Add sidebar transition animation in _page-layout.scss (transition: width 0.3s ease)
- [x] T045 [US2] Implement toggle button functionality in mvp/static/mvp/js/page-layout.js (click handler for toolbar widget)
- [x] T046 [US2] Add CSS class toggle logic in page-layout.js to add/remove .collapsed class on sidebar
- [x] T047 [US2] Add sessionStorage persistence in page-layout.js to remember sidebar state
- [x] T048 [US2] Add ARIA state management in page-layout.js (aria-expanded on toggle button, aria-hidden on sidebar)

#### Sidebar Fixed Positioning

- [x] T049 [US2] Add sticky sidebar styles in _page-layout.scss (.page-layout.sidebar-fixed .page-sidebar with position: sticky, top: 0)
- [x] T050 [US2] Update main component mvp/templates/cotton/inner/index.html to apply CSS classes based on sidebar_fixed attribute
- [x] T051 [US2] Update main component mvp/templates/cotton/inner/index.html to apply CSS classes based on sidebar_toggleable attribute

#### Toolbar Widget Integration

- [x] T052 [US2] Implement toolbar widget expand/collapse icon in mvp/templates/cotton/inner/toolbar/widget.html
- [x] T053 [US2] Add toggle button click handler wiring in page-layout.js
- [x] T054 [US2] Update toolbar component mvp/templates/cotton/inner/toolbar.html to conditionally render widget when collapsible=True

### Responsive Behavior

- [x] T055 [US2] Implement responsive breakpoint logic in _page-layout.scss using sidebar_breakpoint attribute
- [x] T056 [US2] Add media query helpers in _page-layout.scss for sm, md, lg, xl, xxl breakpoints
- [x] T057 [US2] Implement sidebar auto-hide behavior below breakpoint in _page-layout.scss
- [x] T058 [US2] Update main component mvp/templates/cotton/inner/index.html to apply breakpoint class based on sidebar_breakpoint attribute

### Verification for User Story 2

- [x] T059 [US2] Verify sidebar displays on right side using chrome-devtools-mcp
- [x] T060 [US2] Verify sidebar toggle button appears when sidebar_toggleable=True using chrome-devtools-mcp
- [x] T061 [US2] Verify sidebar collapses/expands on toggle click using chrome-devtools-mcp
- [x] T062 [US2] Verify sidebar state persists on page reload using chrome-devtools-mcp
- [x] T063 [US2] Verify responsive behavior at different breakpoints using chrome-devtools-mcp
- [x] T064 [US2] Verify sticky sidebar behavior on scroll using chrome-devtools-mcp

### Tests for User Story 2 (AFTER design verification)

- [x] T065 [P] [US2] Create unit test file tests/components/test_page_layout_sidebar.py
- [x] T066 [P] [US2] Test sidebar slot rendering in test_page_layout_sidebar.py using cotton_render()
- [x] T067 [P] [US2] Test collapsed attribute applies correct CSS class in test_page_layout_sidebar.py
- [x] T068 [P] [US2] Test sidebar_fixed attribute applies correct CSS class in test_page_layout_sidebar.py
- [x] T069 [P] [US2] Test sidebar_toggleable renders toggle button in test_page_layout_sidebar.py
- [x] T070 [P] [US2] Test sidebar_breakpoint applies correct breakpoint class in test_page_layout_sidebar.py
- [x] T071 [US2] Create E2E test file tests/e2e/test_page_layout_sidebar_e2e.py with pytest-playwright
- [x] T072 [US2] Test sidebar toggle button click in test_page_layout_sidebar_e2e.py
- [x] T073 [US2] Test sidebar collapse/expand animation in test_page_layout_sidebar_e2e.py
- [x] T074 [US2] Test sidebar sessionStorage persistence in test_page_layout_sidebar_e2e.py
- [x] T075 [US2] Test responsive sidebar behavior in test_page_layout_sidebar_e2e.py
- [x] T076 [US2] Test sticky sidebar on scroll in test_page_layout_sidebar_e2e.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently ✅

---

## Phase 4: User Story 3 - Template-Driven Configuration (Priority: P2)

**Goal**: Developers can configure inner layout through template attributes, each page has independent configuration

**Independent Test**: Create multiple pages with different inner layout configurations, verify each displays independently

### Design & Implementation for User Story 3

> **NOTE: Implement FIRST, verify design meets expectations, THEN write tests**

#### Configuration Attributes

- [x] T077 [P] [US3] Verify all component attributes are declared in c-vars in mvp/templates/cotton/inner/index.html
- [x] T078 [P] [US3] Add default values for all attributes in index.html (toolbar_fixed=False, footer_fixed=False, sidebar_fixed=False, sidebar_toggleable=False, sidebar_breakpoint='lg')
- [x] T079 [P] [US3] Add class attribute support in index.html for custom CSS classes
- [x] T080 [US3] Ensure toolbar visibility is controlled by slot presence (not attribute) in index.html
- [x] T081 [US3] Ensure footer visibility is controlled by slot presence (not attribute) in index.html
- [x] T082 [US3] Ensure sidebar visibility is controlled by slot presence (not attribute) in index.html

#### Attribute Validation

- [x] T083 [US3] Add breakpoint validation logic in index.html (ensure sidebar_breakpoint is valid Bootstrap breakpoint)
- [x] T084 [US3] Add CSS class generation based on attributes in index.html (combine toolbar_fixed, footer_fixed, sidebar_fixed, sidebar_toggleable, breakpoint classes)
- [x] T085 [US3] Test attribute combinations in demo page demo/templates/demo/page_layout.html

### Verification for User Story 3

- [x] T086 [US3] Verify toolbar_fixed=False renders scrolling toolbar using chrome-devtools-mcp
- [x] T087 [US3] Verify footer_fixed=False renders scrolling footer using chrome-devtools-mcp
- [x] T088 [US3] Verify sidebar_fixed=False renders scrolling sidebar using chrome-devtools-mcp
- [x] T089 [US3] Verify sidebar_breakpoint='md' auto-hides at correct breakpoint using chrome-devtools-mcp
- [x] T090 [US3] Verify custom class attribute adds CSS classes to container using chrome-devtools-mcp
- [x] T091 [US3] Verify missing toolbar slot does not render toolbar using chrome-devtools-mcp

### Tests for User Story 3 (AFTER design verification)

- [x] T092 [P] [US3] Create unit test file tests/components/test_page_layout_config.py
- [x] T093 [P] [US3] Test default attribute values in test_page_layout_config.py
- [x] T094 [P] [US3] Test toolbar_fixed=False does not apply sticky class in test_page_layout_config.py
- [x] T095 [P] [US3] Test footer_fixed=False does not apply sticky class in test_page_layout_config.py
- [x] T096 [P] [US3] Test sidebar_breakpoint='md' applies correct breakpoint class in test_page_layout_config.py
- [x] T097 [P] [US3] Test custom class attribute is applied to container in test_page_layout_config.py
- [x] T098 [P] [US3] Test missing toolbar slot does not render toolbar element in test_page_layout_config.py
- [x] T099 [P] [US3] Test missing footer slot does not render footer element in test_page_layout_config.py
- [x] T100 [P] [US3] Test missing sidebar slot does not render sidebar element in test_page_layout_config.py
- [x] T101 [US3] Create integration test file tests/integration/test_page_layout_integration.py
- [x] T102 [US3] Test inner layout within outer layout in test_page_layout_integration.py
- [x] T103 [US3] Test multiple inner layouts on same page in test_page_layout_integration.py

**Checkpoint**: All user stories should now be independently functional ✅

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T104 Create documentation file docs/page-layout.md with component guide
- [x] T105 Add usage examples to docs/page-layout.md (basic layout, with sidebar, all options)
- [x] T106 Add troubleshooting section to docs/page-layout.md
- [x] T107 [P] Add inline code comments to mvp/templates/cotton/inner/index.html
- [x] T108 [P] Add inline code comments to mvp/static/mvp/scss/page-layout.scss
- [x] T109 [P] Add inline code comments to mvp/static/mvp/js/page-layout.js
- [x] T110 Update demo page demo/templates/demo/page_layout.html with additional examples
- [x] T111 Add performance metrics display to demo page
- [x] T112 Run linting with `poetry run ruff check .`
- [x] T113 Run formatting with `poetry run ruff format .`
- [x] T114 Verify all tests pass with `poetry run pytest`
- [x] T115 Check test coverage with `poetry run pytest --cov=mvp --cov-report=html`
- [ ] T116 Run accessibility audit on demo page using chrome-devtools-mcp
- [ ] T117 Test in Chrome browser
- [ ] T118 Test in Firefox browser (deferred)
- [ ] T119 Test in Safari browser (deferred)
- [ ] T120 Test in Edge browser (deferred)
- [ ] T121 Run quickstart.md validation (follow Tutorial 1-5 step by step)
- [x] T122 Update CHANGELOG.md with feature 006 entry

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0: Demo Setup** ✅ COMPLETE - No dependencies
- **Phase 1: Foundational** - Depends on Phase 0 completion - BLOCKS all user stories
- **Phase 2: User Story 1 (P1)** - Depends on Foundational (Phase 1) - MVP milestone
- **Phase 3: User Story 2 (P2)** - Depends on Foundational (Phase 1) - Can run parallel to US1 but better sequentially for clarity
- **Phase 4: User Story 3 (P2)** - Depends on Foundational (Phase 1) - Can run parallel to US1/US2
- **Phase 5: Polish** - Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 1) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 1) - Integrates with US1 but independently testable
- **User Story 3 (P2)**: Can start after Foundational (Phase 1) - Configuration layer over US1/US2 but independently testable

### Within Each User Story

1. Sub-components before main component integration
2. CSS Grid structure before sticky positioning
3. HTML/CSS before JavaScript
4. Core implementation before responsive behavior
5. Implementation before verification
6. Verification before tests
7. Unit tests before E2E tests

### Parallel Opportunities

**Phase 1 (Foundational)**:

- T005 (verify index.html), T006 (SCSS base), T007 (JS base) can run in parallel

**User Story 1**:

- T010 (toolbar.html), T011 (footer.html), T012 (toolbar/widget.html) can run in parallel
- T030-T034 (unit tests) can run in parallel after implementation complete

**User Story 2**:

- T065-T070 (unit tests) can run in parallel after implementation complete

**User Story 3**:

- T077-T079 (attribute verification), T092-T100 (unit tests) can run in parallel
- T107-T109 (code comments) can run in parallel

**Phase 5 (Polish)**:

- T107-T109 (code comments) can run in parallel
- T117-T120 (browser testing) can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch sub-components together:
Task T010: "Create toolbar component at mvp/templates/cotton/inner/toolbar.html"
Task T011: "Create footer component at mvp/templates/cotton/inner/footer.html"
Task T012: "Create toolbar widget at mvp/templates/cotton/inner/toolbar/widget.html"

# Launch unit tests together (after implementation):
Task T030: "Test toolbar slot rendering"
Task T031: "Test footer slot rendering"
Task T032: "Test toolbar_fixed attribute"
Task T033: "Test footer_fixed attribute"
Task T034: "Test main content area"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Demo Setup ✅ DONE
2. Complete Phase 1: Foundational → Foundation ready
3. Complete Phase 2: User Story 1 → Basic Layout Working
4. **STOP and VALIDATE**: Test User Story 1 independently via demo page
5. Deploy/demo if ready

### Incremental Delivery

1. Phase 0 + Phase 1 → Foundation ready ✅
2. Add User Story 1 → Test independently → Deploy/Demo (MVP! - Basic toolbar/footer/content layout)
3. Add User Story 2 → Test independently → Deploy/Demo (Sidebar with toggle)
4. Add User Story 3 → Test independently → Deploy/Demo (Full configuration)
5. Phase 5 → Polish and cross-cutting concerns
6. Each story adds value without breaking previous stories

### Recommended Order

1. ✅ Phase 0 (Demo Setup) - COMPLETE
2. Phase 1 (Foundational T005-T009) - 5 tasks
3. Phase 2 (User Story 1 T010-T038) - 29 tasks → **MVP MILESTONE**
4. Phase 3 (User Story 2 T039-T076) - 38 tasks
5. Phase 4 (User Story 3 T077-T103) - 27 tasks
6. Phase 5 (Polish T104-T122) - 19 tasks

**Total Tasks**: 122 (4 complete, 118 remaining)

---

## Notes

- [P] tasks = different files, no dependencies within phase
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Use chrome-devtools-mcp for all visual verification tasks
- Use context7 for django-cotton, Bootstrap 5, and Django documentation
- Commit after completing each user story phase
- Demo page enables continuous visual monitoring throughout implementation
- Stop at any checkpoint to validate story independently
