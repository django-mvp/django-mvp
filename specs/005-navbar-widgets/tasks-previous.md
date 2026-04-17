# Tasks: Main Navbar Widgets - Base & Generic Widgets

**Input**: Design documents from /specs/005-navbar-widgets/
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Scope**: This spec has been reduced to focus on foundational components only:

- **Base Widget Component** (foundation for all custom widgets)
- **Theme Switcher Widget** (generic widget with JavaScript)
- **Fullscreen Widget** (generic widget, simpler pattern)

**Deferred to Future Specs**:

- User Profile Widget
- Messages Widget
- Notifications Widget

**Tests**: Tests are REQUIRED for behavior changes. Use pytest + pytest-django for backend/integration. End-to-end tests with playwright are REQUIRED for all features. UI changes MUST be verified using chrome-devtools-mcp. Use context7 for up-to-date library documentation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `- [ ] [ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project structure, documentation setup, and dependency validation

- [ ] T001 Verify Bootstrap 5.3+ is available and django-easy-icons is configured in base.html
- [ ] T002 Verify AdminLTE 4 CSS/JS are loaded from CDN in base.html
- [ ] T003 [P] Create mvp/templates/cotton/navbar/widgets/ directory structure
- [ ] T004 [P] Create tests/test_navbar_base_widget.py for base widget tests

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Create documentation structure in docs/navbar-widgets.md with placeholders for all three widgets
- [ ] T006 [P] Setup test fixtures in tests/conftest.py for widget rendering tests
- [ ] T007 [P] Verify django-cotton 2.3+ component loading works correctly

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Base Widget Component (Priority: P1)  MVP

**Goal**: Create reusable base widget component that provides foundation for all navbar widgets

**Independent Test**: Create a custom widget using base component with icon, badge, and dropdown content. Verify AdminLTE styling and Bootstrap dropdown behavior.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T008 [P] [US1] Test base widget renders with icon in tests/test_navbar_base_widget.py
- [ ] T009 [P] [US1] Test base widget displays badge with count in tests/test_navbar_base_widget.py
- [ ] T010 [P] [US1] Test base widget hides badge when count is zero in tests/test_navbar_base_widget.py
- [ ] T011 [P] [US1] Test base widget renders dropdown content via slot in tests/test_navbar_base_widget.py
- [ ] T012 [P] [US1] Test badge supports Bootstrap color classes (danger, warning, info, success) in tests/test_navbar_base_widget.py
- [ ] T012a [P] [US1] Test each badge color renders with correct Bootstrap text-bg-{color} class (danger, warning, info, success) in tests/test_navbar_base_widget.py
- [ ] T013 [P] [US1] Test base widget handles negative badge counts (hide badge) in tests/test_navbar_base_widget.py
- [ ] T014 [P] [US1] Test base widget follows AdminLTE nav-item dropdown pattern in tests/test_navbar_base_widget.py

### Implementation for User Story 1

- [ ] T015 [US1] Create base widget component in mvp/templates/cotton/navbar/widgets/index.html
- [ ] T016 [US1] Add icon prop and use c-icon component for rendering (never direct <i> tags)
- [ ] T017 [US1] Add badge_count prop with conditional rendering logic to base widget
- [ ] T018 [US1] Add badge_color prop with Bootstrap color class support to base widget
- [ ] T019 [US1] Add default slot for dropdown content in base widget
- [ ] T020 [US1] Apply AdminLTE navbar styling (nav-item dropdown, navbar-badge classes) to base widget
- [ ] T021 [US1] Add data-bs-toggle="dropdown" for Bootstrap dropdown behavior in base widget
- [ ] T022 [US1] Add ARIA labels for accessibility (aria-label on icon button) in base widget
- [ ] T023 [US1] Run all US1 tests and verify they pass: poetry run pytest tests/test_navbar_base_widget.py -v

### UI Verification for User Story 1

- [ ] T024 [US1] Use chrome-devtools-mcp to verify base widget renders correctly in navbar
- [ ] T025 [US1] Use chrome-devtools-mcp to verify badge displays with different counts (0, 5, 99, 100, 1000 displays as "999+")
- [ ] T026 [US1] Use chrome-devtools-mcp to verify dropdown opens on click with custom content
- [ ] T027 [US1] Use chrome-devtools-mcp to verify badge colors (danger, warning, info, success)

### Documentation for User Story 1

- [ ] T028 [US1] Document base widget props (icon, badge_count, badge_color) in docs/navbar-widgets.md
- [ ] T029 [US1] Document base widget slots (default slot for dropdown) in docs/navbar-widgets.md
- [ ] T030 [US1] Add usage example for custom widget in docs/navbar-widgets.md
- [ ] T031 [US1] Add base widget example to demo/templates/demo/navbar_widgets.html

**Checkpoint**: At this point, User Story 1 should be fully functional - developers can create custom widgets using the base component

---

## Phase 4: User Story 2 - Theme Switcher Widget (Priority: P1)  MVP

**Goal**: Provide theme switcher widget with Light/Dark/Auto modes and localStorage persistence

**Independent Test**: Add theme switcher to navbar, toggle between themes, verify persistence across page reloads and system preference detection.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T032 [P] [US2] Create tests/test_theme_switcher_widget.py for theme switcher component tests
- [ ] T033 [P] [US2] Test theme switcher widget renders with dropdown menu in tests/test_theme_switcher_widget.py
- [ ] T034 [P] [US2] Test theme switcher shows Light, Dark, Auto options in tests/test_theme_switcher_widget.py
- [ ] T035 [P] [US2] Test theme switcher marks current selection as active in tests/test_theme_switcher_widget.py
- [ ] T036 [P] [US2] Create tests/test_theme_switcher_js.py for JavaScript behavior tests
- [ ] T037 [P] [US2] Test theme switcher JavaScript applies theme to html data-bs-theme attribute in tests/test_theme_switcher_js.py
- [ ] T038 [P] [US2] Test theme switcher JavaScript saves preference to localStorage in tests/test_theme_switcher_js.py
- [ ] T039 [P] [US2] Test theme switcher JavaScript loads saved preference on page load in tests/test_theme_switcher_js.py
- [ ] T040 [P] [US2] Test theme switcher JavaScript respects system preference in Auto mode in tests/test_theme_switcher_js.py
- [ ] T041 [P] [US2] Test theme switcher JavaScript functions without localStorage (session-only) in tests/test_theme_switcher_js.py

### Implementation for User Story 2

- [ ] T042 [P] [US2] Create theme_switcher.html component in mvp/templates/cotton/navbar/widgets/
- [ ] T043 [US2] Use base widget with palette-fill icon in theme_switcher.html
- [ ] T044 [US2] Add dropdown menu with Light, Dark, Auto options in theme_switcher.html
- [ ] T045 [US2] Add active state indicators (checkmarks) for current theme in theme_switcher.html
- [ ] T046 [US2] Add data-theme attributes for JavaScript targeting in theme_switcher.html
- [ ] T047 [P] [US2] Create theme-switcher.js in mvp/static/js/navbar/
- [ ] T048 [US2] Implement theme detection from localStorage in theme-switcher.js
- [ ] T049 [US2] Implement theme detection from system preference (prefers-color-scheme) in theme-switcher.js
- [ ] T050 [US2] Implement theme application to html data-bs-theme attribute in theme-switcher.js
- [ ] T051 [US2] Implement localStorage save on theme selection in theme-switcher.js
- [ ] T052 [US2] Implement localStorage availability check with session-only fallback in theme-switcher.js
- [ ] T053 [US2] Implement system preference change listener for Auto mode in theme-switcher.js
- [ ] T054 [US2] Implement active state updates in dropdown menu in theme-switcher.js
- [ ] T055 [US2] Add theme-switcher.js script tag to base.html or mvp/base.html
- [ ] T056 [US2] Run all US2 tests and verify they pass: poetry run pytest tests/test_theme_switcher_widget.py tests/test_theme_switcher_js.py -v

### UI Verification for User Story 2

- [ ] T057 [US2] Use chrome-devtools-mcp to verify theme switcher renders in navbar with palette icon
- [ ] T058 [US2] Use chrome-devtools-mcp to verify dropdown shows Light, Dark, Auto options
- [ ] T059 [US2] Use chrome-devtools-mcp to click Light theme and verify immediate theme change
- [ ] T060 [US2] Use chrome-devtools-mcp to click Dark theme and verify immediate theme change
- [ ] T061 [US2] Use chrome-devtools-mcp to verify theme persists after page reload
- [ ] T062 [US2] Use chrome-devtools-mcp to verify Auto mode respects system preference
- [ ] T063 [US2] Use chrome-devtools-mcp to verify active state checkmark updates on selection

### Documentation for User Story 2

- [ ] T064 [US2] Document theme switcher component in docs/navbar-widgets.md
- [ ] T065 [US2] Document theme switcher JavaScript API in docs/navbar-widgets.md
- [ ] T066 [US2] Document localStorage key and data structure in docs/navbar-widgets.md
- [ ] T067 [US2] Add theme switcher usage example to docs/navbar-widgets.md
- [ ] T068 [US2] Add theme switcher to demo/templates/demo/navbar_widgets.html
- [ ] T069 [US2] Document graceful degradation when localStorage unavailable in docs/navbar-widgets.md

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - base widget is reusable, theme switcher is fully functional

---

## Phase 5: User Story 3 - Fullscreen Toggle Widget (Priority: P2)

**Goal**: Provide fullscreen toggle widget using browser Fullscreen API with state management

**Independent Test**: Add fullscreen widget to navbar, click to toggle fullscreen mode, verify icon changes and ESC key handling.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T070 [P] [US3] Create tests/test_fullscreen_widget.py for fullscreen widget tests
- [ ] T071 [P] [US3] Test fullscreen widget renders with expand icon in tests/test_fullscreen_widget.py
- [ ] T072 [P] [US3] Test fullscreen widget uses data-lte-toggle="fullscreen" in tests/test_fullscreen_widget.py
- [ ] T073 [P] [US3] Test fullscreen widget has proper ARIA labels in tests/test_fullscreen_widget.py
- [ ] T074 [P] [US3] Test fullscreen widget integrates with AdminLTE fullscreen plugin in tests/test_fullscreen_widget.py

### Implementation for User Story 3

- [ ] T075 [P] [US3] Create fullscreen_widget.html component in mvp/templates/cotton/navbar/widgets/
- [ ] T076 [US3] Use base widget with arrows-fullscreen icon in fullscreen_widget.html
- [ ] T077 [US3] Add data-lte-toggle="fullscreen" for AdminLTE fullscreen integration in fullscreen_widget.html
- [ ] T078 [US3] Add ARIA label for accessibility in fullscreen_widget.html
- [ ] T079 [US3] Remove dropdown (no dropdown needed for fullscreen toggle) in fullscreen_widget.html
- [ ] T079a [US3] Verify AdminLTE fullscreen plugin handles feature detection (FR-019) or add conditional rendering if widget should hide when unsupported
- [ ] T080 [US3] Run all US3 tests and verify they pass: poetry run pytest tests/test_fullscreen_widget.py -v

### UI Verification for User Story 3

- [ ] T081 [US3] Use chrome-devtools-mcp to verify fullscreen widget renders in navbar
- [ ] T082 [US3] Use chrome-devtools-mcp to click widget and verify fullscreen mode activates
- [ ] T083 [US3] Use chrome-devtools-mcp to verify icon changes in fullscreen mode
- [ ] T084 [US3] Use chrome-devtools-mcp to click widget again and verify fullscreen exits
- [ ] T085 [US3] Use chrome-devtools-mcp to verify ESC key exits fullscreen and updates widget

### Documentation for User Story 3

- [ ] T086 [US3] Document fullscreen widget in docs/navbar-widgets.md
- [ ] T087 [US3] Document AdminLTE fullscreen plugin integration in docs/navbar-widgets.md
- [ ] T088 [US3] Add fullscreen widget usage example to docs/navbar-widgets.md
- [ ] T089 [US3] Add fullscreen widget to demo/templates/demo/navbar_widgets.html
- [ ] T090 [US3] Document Fullscreen API browser compatibility in docs/navbar-widgets.md

**Checkpoint**: All user stories should now be independently functional - base widget, theme switcher, and fullscreen widget all working

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final integration, documentation, and quality assurance

### Integration & Examples

- [ ] T091 Add all three widgets to Demo App navbar in demo/templates/base.html
- [ ] T092 Create comprehensive navbar widgets demo page at demo/templates/demo/navbar_widgets.html
- [ ] T093 Add navbar widgets menu item to Demo App navigation

### Documentation

- [ ] T094 [P] Complete docs/navbar-widgets.md with all three widgets documented
- [ ] T095 [P] Add troubleshooting section to docs/navbar-widgets.md (localStorage, Fullscreen API, etc.)
- [ ] T096 [P] Add quickstart guide to docs/navbar-widgets.md
- [ ] T097 [P] Update README.md with navbar widgets section and link to docs
- [ ] T098 [P] Add navbar widgets to docs/index.md navigation

### Code Quality

- [ ] T099 Run full test suite: poetry run pytest -v
- [ ] T100 Run ruff linting: poetry run ruff check .
- [ ] T101 Run ruff formatting: poetry run ruff format .
- [ ] T102 Run djlint on templates: poetry run djlint mvp/templates/cotton/navbar/widgets/ --check

### End-to-End Testing (Playwright)

- [ ] T103 Create tests/e2e/test_navbar_widgets.py for end-to-end tests
- [ ] T104 [P] Write E2E test for base widget custom implementation in tests/e2e/test_navbar_widgets.py
- [ ] T105 [P] Write E2E test for theme switcher workflow (Light  Dark  Auto  reload) in tests/e2e/test_navbar_widgets.py
- [ ] T106 [P] Write E2E test for fullscreen toggle workflow (enter  exit  ESC key) in tests/e2e/test_navbar_widgets.py
- [ ] T107 Run E2E tests: poetry run pytest tests/e2e/test_navbar_widgets.py -v

### Final Verification

- [ ] T108 Use chrome-devtools-mcp to verify all three widgets work together in navbar
- [ ] T109 Use chrome-devtools-mcp to verify mobile responsiveness (320px, 768px, 1200px)
- [ ] T110 Use chrome-devtools-mcp to verify accessibility (keyboard navigation, ARIA labels)
- [ ] T111 Verify all acceptance scenarios from spec.md are satisfied

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User Story 1 (Base Widget) MUST complete before User Stories 2 & 3
  - User Stories 2 (Theme Switcher) and 3 (Fullscreen) can proceed in parallel after US1
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (Base Widget - P1)**: Foundation for all widgets - MUST complete first
- **User Story 2 (Theme Switcher - P1)**: Depends on US1 (uses base widget) - High priority
- **User Story 3 (Fullscreen - P2)**: Depends on US1 (uses base widget) - Can run parallel with US2

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Component implementation before JavaScript (where applicable)
- JavaScript before UI verification
- UI verification before documentation
- All tests must pass before moving to next story

### Parallel Opportunities

#### Phase 1 (Setup)

- T003 (directory structure) + T004 (test file creation) can run in parallel

#### Phase 2 (Foundational)

- T006 (test fixtures) + T007 (Cotton verification) can run in parallel

#### Phase 3 (User Story 1 - Base Widget)

- T008-T014: All tests can be written in parallel
- T024-T027: All UI verification tasks can run in parallel after implementation
- T028-T031: All documentation tasks can run in parallel

#### Phase 4 (User Story 2 - Theme Switcher)

- T032-T041: All tests can be written in parallel (component tests + JS tests)
- T042 (component) + T047 (JS file creation) can start in parallel
- T057-T063: All UI verification tasks can run in parallel after implementation
- T064-T069: All documentation tasks can run in parallel

#### Phase 5 (User Story 3 - Fullscreen)

- T070-T074: All tests can be written in parallel
- T075 (component creation) can start immediately after US1 complete
- T081-T085: All UI verification tasks can run in parallel after implementation
- T086-T090: All documentation tasks can run in parallel

#### Phase 6 (Polish)

- T094-T098: All documentation tasks can run in parallel
- T104-T106: All E2E tests can be written in parallel

---

## Parallel Example: User Story 1 (Base Widget)

After foundational phase completes, here's how US1 tasks can be parallelized:

```bash
# Terminal 1: Write all tests in parallel (one developer can do these sequentially)
poetry run pytest tests/test_navbar_base_widget.py  # All should FAIL initially

# Terminal 2: Implement base widget component
# Edit: mvp/templates/cotton/navbar/widgets/index.html
# (T015-T022 done sequentially by one developer)

# Terminal 3: After implementation, verify tests pass
poetry run pytest tests/test_navbar_base_widget.py -v  # All should PASS now

# Terminal 4: UI verification (can be done in parallel after impl)
# Use chrome-devtools-mcp for T024-T027

# Terminal 5: Documentation (can be done in parallel with UI verification)
# T028-T031: Update docs and examples
```

---

## Implementation Strategy

### MVP Scope (Minimum Viable Product)

For initial release, implement:

- **User Story 1 (Base Widget)** - Required foundation
- **User Story 2 (Theme Switcher)** - High user value, demonstrates complete pattern
- **User Story 3 (Fullscreen)** - Optional but recommended (demonstrates simpler widget pattern)

### Incremental Delivery

1. **Sprint 1**: Phase 1-3 (Setup + Foundational + Base Widget) - Delivers foundation
2. **Sprint 2**: Phase 4 (Theme Switcher) - Delivers first complete widget with JS
3. **Sprint 3**: Phase 5 (Fullscreen) - Delivers simpler widget pattern example
4. **Sprint 4**: Phase 6 (Polish) - Documentation, E2E tests, integration

### Risk Mitigation

- Test theme switcher localStorage handling early (localStorage might be blocked)
- Verify Fullscreen API browser support (not available in all browsers)
- Test dropdown behavior on mobile devices (touch interactions)
- Validate AdminLTE fullscreen plugin integration (verify it exists in AdminLTE 4)

---

## Success Criteria Checklist

- [ ] **SC-001**: Developers can add any widget in under 5 lines of template code
- [ ] **SC-002**: All widgets render correctly on mobile (320px), tablet (768px), desktop (1200px+)
- [ ] **SC-003**: Theme switcher changes theme in under 100ms with no flicker
- [ ] **SC-004**: Widget dropdowns open/close with smooth AdminLTE animations
- [ ] **SC-005**: Badge counters display correctly for values 0 to 999+
- [ ] **SC-006**: Fullscreen toggle works with single click and reflects state
- [ ] **SC-007**: All widgets have ARIA labels, keyboard navigation, screen reader support
- [ ] **SC-008**: Theme preference persists across browser sessions and page reloads
- [ ] **SC-009**: Documentation provides complete examples for each widget type
- [ ] **SC-010**: Test coverage includes unit tests for components and integration tests for JS

---

## Summary

**Total tasks**: 111
**Phases**: 6 (Setup + Foundation + 3 User Stories + Polish)
**Test tasks**: 33 (30%)
**Implementation tasks**: 55 (50%)
**Documentation tasks**: 15 (13%)
**Quality/verification tasks**: 8 (7%)

**Scope Reduction**:

- **Removed**: User Profile, Messages, Notifications widgets
- **Retained**: Base Widget (foundation), Theme Switcher (full-featured), Fullscreen (simple pattern)
- **Benefit**: Focused scope, faster delivery, clearer foundation for future widgets

**MVP Scope**: Phases 1-4 (T001-T069) = Foundation + Base Widget + Theme Switcher
**Full Feature**: All phases = 100%
