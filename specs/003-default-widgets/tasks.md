# Tasks: AdminLTE 4 Widget Components

**Input**: Design documents from `/specs/003-default-widgets/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Status**: All 85 tasks complete (100%). Card component enhanced with v2.1 features (2026-01-05).

**Tests**: Tests are REQUIRED for behavior changes. Use pytest + pytest-django for component rendering tests and djlint for template linting.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

All paths relative to repository root `c:\Users\jennings\Documents\repos\django-mvp\`:

- **Components**: `mvp/templates/cotton/`
- **Tests**: `tests/`
- **Docs**: `docs/components/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create feature branch `003-default-widgets` and verify Poetry environment active
- [X] T002 [P] Review contracts in specs/003-default-widgets/contracts/ to understand component requirements
- [X] T003 [P] Review quickstart.md in specs/003-default-widgets/ for usage patterns

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Verify Bootstrap 5.3, AdminLTE 4, and Bootstrap Icons are loaded in base template
- [X] T005 [P] Verify django-cotton is properly configured in INSTALLED_APPS
- [X] T006 [P] Create test fixtures for component rendering in tests/conftest.py if needed
- [X] T007 Verify AdminLTE 4 JavaScript is loaded for card widget interactivity

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Display Statistical Data with Info Boxes (Priority: P1) 🎯 MVP

**Goal**: Create info-box component for displaying metrics with icons, progress bars, and various styling options

**Independent Test**: Render info box with icon="gear-fill", text="CPU Traffic", number="10%" and verify HTML structure matches contract

### Tests for User Story 1 (REQUIRED)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T008 [P] [US1] Create test file tests/test_info_box.py with basic rendering test
- [X] T009 [P] [US1] Add test for info box with variant attribute in tests/test_info_box.py
- [X] T010 [P] [US1] Add test for info box with progress bar in tests/test_info_box.py
- [X] T011 [P] [US1] Add test for info box with custom background and gradient in tests/test_info_box.py
- [X] T012 [P] [US1] Add test for info box with custom classes in tests/test_info_box.py
- [X] T013 [P] [US1] Add test for ARIA attributes on progress bar in tests/test_info_box.py

### Implementation for User Story 1

- [X] T014 [US1] Create mvp/templates/cotton/info-box.html with c-vars declaration
- [X] T015 [US1] Implement basic HTML structure with icon, text, and number sections in mvp/templates/cotton/info-box.html
- [X] T016 [US1] Add variant class logic for colored backgrounds in mvp/templates/cotton/info-box.html
- [X] T017 [US1] Add bg and gradient class logic in mvp/templates/cotton/info-box.html
- [X] T018 [US1] Add progress bar conditional section with ARIA attributes in mvp/templates/cotton/info-box.html
- [X] T019 [US1] Add custom class passthrough logic in mvp/templates/cotton/info-box.html
- [X] T020 [US1] Run all tests to verify info-box component passes
- [X] T021 [US1] Run djlint on mvp/templates/cotton/info-box.html to verify template quality
- [X] T022 [P] [US1] Create documentation file docs/components/info-box.md with usage examples

**Checkpoint**: At this point, User Story 1 (info-box) should be fully functional and testable independently

---

## Phase 4: User Story 2 - Create Summary Cards with Small Boxes (Priority: P1) 🎯 MVP

**Goal**: Create small-box component for displaying prominent metrics with icons, colored backgrounds, and footer links

**Independent Test**: Render small box with heading="150", text="New Orders", icon="cart-fill", variant="primary" and verify HTML structure matches contract

### Tests for User Story 2 (REQUIRED)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T023 [P] [US2] Create test file tests/test_small_box.py with basic rendering test
- [X] T024 [P] [US2] Add test for small box with bg attribute in tests/test_small_box.py
- [X] T025 [P] [US2] Add test for small box with footer link (default text) in tests/test_small_box.py
- [X] T026 [P] [US2] Add test for small box with custom link_text in tests/test_small_box.py
- [X] T027 [P] [US2] Add test for small box without footer link in tests/test_small_box.py
- [X] T028 [P] [US2] Add test for small box with custom classes in tests/test_small_box.py
- [X] T029 [P] [US2] Add test for ARIA hidden attribute on icon in tests/test_small_box.py

### Implementation for User Story 2

- [X] T030 [US2] Create mvp/templates/cotton/small-box.html with c-vars declaration
- [X] T031 [US2] Implement basic HTML structure with inner content (h3, p) in mvp/templates/cotton/small-box.html
- [X] T032 [US2] Add SVG icon with xlink:href reference in mvp/templates/cotton/small-box.html
- [X] T033 [US2] Add bg color class logic using text-bg-{variant} pattern in mvp/templates/cotton/small-box.html
- [X] T034 [US2] Add conditional footer link section with default link_text="More info" in mvp/templates/cotton/small-box.html
- [X] T035 [US2] Add custom class passthrough logic in mvp/templates/cotton/small-box.html
- [X] T036 [US2] Run all tests to verify small-box component passes
- [X] T037 [US2] Run djlint on mvp/templates/cotton/small-box.html to verify template quality
- [X] T038 [P] [US2] Create documentation file docs/components/small-box.md with usage examples

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Build Flexible Content Cards (Priority: P2)

**Goal**: Create card component with header, body, footer slots, and interactive tools (collapse, remove, maximize)

**Independent Test**: Render card with title="Card Title" and body content, verify header and body render correctly with collapse button

**Note**: Card component underwent v2.0 refactoring (2026-01-05) reducing template from 82 to 11 lines, then v2.1 enhancements (2026-01-05) added `compact`, `footer_class`, tool flags (`collapsible`, `removable`, `maximizable`), and flexbox header layout. See contracts/card.md for version history.

### Tests for User Story 3 (REQUIRED)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T039 [P] [US3] Create test file tests/test_card.py with basic card rendering test
- [X] T040 [P] [US3] Add test for card with icon in header in tests/test_card.py
- [X] T041 [P] [US3] Add test for card with variant="primary" fill="outline" in tests/test_card.py
- [X] T042 [P] [US3] ~~Add test for card with variant="primary" fill="header"~~ (removed in v2.0 - fill="header" deprecated) in tests/test_card.py
- [X] T043 [P] [US3] Add test for card with variant="primary" fill="card" in tests/test_card.py
- [X] T044 [P] [US3] Add test for card with footer slot in tests/test_card.py
- [X] T045 [P] [US3] Add test for card without footer slot in tests/test_card.py
- [X] T046 [P] [US3] Add test for card with collapsed attribute in tests/test_card.py
- [X] T047 [P] [US3] Add test for card with tools slot in tests/test_card.py
- [X] T048 [P] [US3] Add test for card without title (simple card) in tests/test_card.py
- [X] T049 [P] [US3] Add test for ARIA attributes on collapse button in tests/test_card.py
- [X] T050 [P] [US3] Add test for custom classes in tests/test_card.py

### Implementation for User Story 3

- [X] T051 [US3] Create mvp/templates/cotton/card.html with c-vars declaration
- [X] T052 [US3] Implement conditional card header with title and icon in mvp/templates/cotton/card.html
- [X] T053 [US3] Add variant-fill class logic for outline/header/card modes in mvp/templates/cotton/card.html
- [X] T054 [US3] Implement card-tools section with collapse button in mvp/templates/cotton/card.html
- [X] T055 [US3] Add tools named slot before collapse button in mvp/templates/cotton/card.html
- [X] T056 [US3] Implement card-body section with default slot in mvp/templates/cotton/card.html
- [X] T057 [US3] Add conditional footer section with footer named slot in mvp/templates/cotton/card.html
- [X] T058 [US3] Add collapsed state logic (display:none and aria-expanded) in mvp/templates/cotton/card.html
- [X] T059 [US3] Add AdminLTE data attributes (data-lte-toggle, data-lte-icon) in mvp/templates/cotton/card.html
- [X] T060 [US3] Add custom class passthrough logic in mvp/templates/cotton/card.html
- [X] T061 [US3] Run all tests to verify card component passes
- [X] T062 [US3] Run djlint on mvp/templates/cotton/card.html to verify template quality
- [X] T063 [P] [US3] Create documentation file docs/components/card.md with usage examples

### Card Component v2.1 Enhancements (Post-Implementation)

**Date**: 2026-01-05
**Rationale**: Practical improvements discovered during real-world usage

- [X] Added `compact` attribute for zero-padding body (tables, maps, full-width content)
- [X] Added `footer_class` attribute for footer styling customization
- [X] Restored footer slot (accidentally removed in v2.0 refactoring)
- [X] Added tool flags: `collapsible`, `removable`, `maximizable` with sub-components
- [X] Enhanced header with flexbox layout (`d-flex align-items-center`)
- [X] Enhanced icon styling with default classes (`me-2 fs-5 text-muted`)
- [X] Added `{{ attrs }}` passthrough for HTML attributes (id, data-*, aria-*)
- [X] Updated data-model.md to reflect v2.1 changes
- [X] Updated quickstart.md with v2.1 examples
- [X] Updated contracts/card.md with v2.1 documentation
- [X] Updated spec.md clarifications with v2.1 design decisions

**Checkpoint**: All primary user stories (US1, US2, US3) should now be independently functional

---

## Phase 6: User Story 4 - Apply Consistent Styling Across Widgets (Priority: P3)

**Goal**: Verify consistent Bootstrap 5 color schemes and utility class support across all widget components

**Independent Test**: Apply same Bootstrap utility classes to each widget and verify consistent rendering

### Tests for User Story 4 (REQUIRED)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T064 [P] [US4] Add test for Bootstrap shadow utilities on info-box in tests/test_info_box.py
- [X] T065 [P] [US4] Add test for Bootstrap shadow utilities on small-box in tests/test_small_box.py
- [X] T066 [P] [US4] Add test for Bootstrap shadow utilities on card in tests/test_card.py
- [X] T067 [P] [US4] Add test for all variant colors (primary, success, warning, danger, info, secondary) on info-box in tests/test_info_box.py
- [X] T068 [P] [US4] Add test for all bg colors on small-box in tests/test_small_box.py
- [X] T069 [P] [US4] Add test for all variant-fill combinations on card in tests/test_card.py

### Implementation for User Story 4

- [X] T070 [US4] Review all three components for consistent class attribute passthrough
- [X] T071 [US4] Review all three components for consistent default value handling ("default")
- [X] T072 [US4] Verify gradient logic works consistently with bg attribute across components
- [X] T073 [US4] Run full test suite to verify all styling tests pass
- [X] T074 [P] [US4] Add color variant examples to each documentation file

**Checkpoint**: All user stories should now be independently functional with consistent styling

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T075 [P] Update main README.md with links to new component documentation
- [X] T076 [P] Add widget components section to package documentation in docs/
- [X] T077 [P] Review and update CHANGELOG.md with new widget features
- [X] T078 Run full test suite with coverage: `poetry run pytest --cov=mvp --cov-report=html`
- [X] T079 Verify test coverage is >90% for all three component templates
- [X] T080 Run djlint on all templates: `poetry run djlint mvp/templates/cotton/ --check`
- [X] T081 [P] Create example dashboard page in demo/templates/ demonstrating all widgets
- [X] T082 Run quickstart.md validation by executing all example code snippets
- [X] T083 [P] Review contracts against implementation to ensure 100% compliance
- [X] T084 [P] Add widget components to example project menus if applicable
- [X] T085 Final visual comparison against AdminLTE 4 reference implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 (info-box) can proceed after Phase 2 ✅
  - US2 (small-box) can proceed after Phase 2 ✅
  - US3 (card) can proceed after Phase 2 ✅
  - US4 (styling) depends on US1, US2, US3 completion
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 4 (P3)**: Depends on US1, US2, US3 being complete (cross-cutting validation)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Component template before running tests
- All tests pass before documentation
- Documentation before moving to next story

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes:
  - **US1, US2, US3 can be worked on in parallel** by different developers
  - All tests for a user story marked [P] can run in parallel
- Polish tasks marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task T008: "Create test file tests/test_info_box.py with basic rendering test"
Task T009: "Add test for info box with variant attribute in tests/test_info_box.py"
Task T010: "Add test for info box with progress bar in tests/test_info_box.py"
Task T011: "Add test for info box with custom background and gradient in tests/test_info_box.py"
Task T012: "Add test for info box with custom classes in tests/test_info_box.py"
Task T013: "Add test for ARIA attributes on progress bar in tests/test_info_box.py"

# Then implement component sequentially (single file):
Task T014-T019: Implement info-box.html features
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (info-box)
4. Complete Phase 4: User Story 2 (small-box)
5. **STOP and VALIDATE**: Test both components independently in example dashboard
6. Deploy/demo if ready

**MVP Scope**: info-box + small-box = Complete dashboard metrics capability

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (info-box) → Test independently → Deploy/Demo (MVP Part 1!)
3. Add User Story 2 (small-box) → Test independently → Deploy/Demo (MVP Part 2!)
4. Add User Story 3 (card) → Test independently → Deploy/Demo
5. Add User Story 4 (styling) → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T007)
2. Once Foundational is done:
   - **Developer A**: User Story 1 (info-box) - T008-T022
   - **Developer B**: User Story 2 (small-box) - T023-T038
   - **Developer C**: User Story 3 (card) - T039-T063
3. **Developer A**: User Story 4 (styling validation) - T064-T074 (after US1, US2, US3 complete)
4. **Team**: Polish phase together - T075-T085

---

## Task Summary

- **Total Tasks**: 85
- **Setup Phase**: 3 tasks
- **Foundational Phase**: 4 tasks (BLOCKING)
- **User Story 1 (info-box)**: 15 tasks (6 tests + 9 implementation)
- **User Story 2 (small-box)**: 16 tasks (7 tests + 9 implementation)
- **User Story 3 (card)**: 25 tasks (12 tests + 13 implementation)
- **User Story 4 (styling)**: 11 tasks (6 tests + 5 implementation)
- **Polish Phase**: 11 tasks

**Parallel Opportunities**: 31 tasks marked [P] can run in parallel within their phase

**Suggested MVP Scope**: Phase 1 + Phase 2 + Phase 3 + Phase 4 = **38 tasks** (info-box + small-box only)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD approach)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Run `poetry run pytest` frequently during implementation
- Run `poetry run djlint mvp/templates/cotton/ --check` after template changes
- Components must match AdminLTE 4 reference implementation exactly
- All components must pass WCAG 2.1 AA accessibility standards
