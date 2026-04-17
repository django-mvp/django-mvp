# Implementation Plan: Main Navbar Widgets - Base & Generic Widgets

**Feature**: Main Navbar Widgets (Reduced Scope)
**Spec**: [spec.md](spec.md)
**Branch**: `005-navbar-widgets`
**Created**: January 14, 2026
**Updated**: January 15, 2026 - Regenerated with icon and Cotton slot clarifications

**Scope**: This plan covers the foundational base widget component and two generic widgets:

- Base Widget Component (foundation for all custom widgets)
- Theme Switcher Widget (generic widget with JavaScript)
- Fullscreen Widget (generic widget, simpler pattern)

**Deferred to Future Specs**: User Profile Widget, Messages Widget, Notifications Widget

---

## Technical Context

### Feature Summary

Implement AdminLTE 4 navbar widgets as reusable Cotton components. This implementation focuses on establishing patterns through a base widget and two reference implementations (theme switcher and fullscreen toggle).

### Tech Stack

- **Django 5.2+** - Backend framework
- **django-cotton 2.3+** - Component composition system
- **django-easy-icons** - Icon rendering via `<c-icon />` component (never direct `<i>` tags)
- **Bootstrap 5.3+** - UI framework (AdminLTE 4 dependency)
- **AdminLTE 4 RC3** - Navbar styling conventions and fullscreen plugin
- **localStorage API** - Theme persistence (with graceful degradation)
- **Fullscreen API** - Browser fullscreen support (with feature detection)

### Architecture Overview

All widgets follow a consistent composition pattern:

```
Navbar Widget Structure:
├── Widget trigger (icon + optional badge)
├── Dropdown menu (optional)
│   └── Customizable content via {{ slot }}
└── JavaScript behavior (theme switcher only)
```

**Component Naming Convention**:

- Base widget: `<c-navbar.widgets />` (index.html)
- Specific widgets: `<c-navbar.widgets.theme-switcher />`, `<c-navbar.widgets.fullscreen />`

**Icon Implementation**:

- Use `<c-icon name="alias" />` component from django-easy-icons
- Icon aliases defined in EASY_ICONS settings (tests/settings.py)
- Required aliases: theme_light, maximize, minimize
- Never use direct `<i class="bi-*">` tags

**Cotton Slot Syntax**:

- In component: `{{ slot }}` (default), `{{ footer }}` (named)
- When calling: Content between tags → `{{ slot }}`, `<c-slot name="footer">` → `{{ footer }}`
- Named slots only work from within other components

### Design Decisions

1. **Cotton Component Pattern**: All widgets are Cotton components with consistent props API
2. **Server-Side Rendering**: Dropdown content is server-rendered (no AJAX)
3. **Badge Display Logic**: Hide when zero, show "99+" when > 99
4. **Theme Persistence**: localStorage with session-only fallback
5. **Fullscreen Integration**: Uses AdminLTE 4's built-in fullscreen plugin (data-lte-toggle="fullscreen")
6. **Icon Component Usage**: All icons via `<c-icon name="alias" />` (django-easy-icons)
7. **Slot-Based Composition**: Use {{ slot }} Django variables for content injection

### Research Required

- **DONE**: AdminLTE 4 navbar widget HTML structure
- **DONE**: Theme switcher JavaScript implementation pattern
- **DONE**: Bootstrap 5 dropdown behavior and accessibility
- **DONE**: AdminLTE 4 fullscreen plugin integration
- **DONE**: EASY_ICONS available icon aliases (tests/settings.py)
- **DONE**: Cotton slot syntax ({{ slot }} for default, <c-slot name="..."> for named)

---

## Constitution Check

### I. Test-First ✅

**Plan**: All tests written FIRST before implementation.

- Base widget tests (T009-T017) before component creation
- Theme switcher tests (T035-T047) before JS implementation
- Fullscreen tests (T071-T075) before widget creation
- Tests must fail initially, then pass after implementation

### II. Documentation-First ✅

**Plan**: Documentation created alongside implementation.

- Base widget usage examples (T091-T093)
- Theme switcher configuration guide (T094-T095)
- Fullscreen widget integration docs (T096)
- All components documented with minimal examples

### III. Accessibility ✅

**Plan**: ARIA compliance built-in.

- Keyboard navigation for all widgets (Tab, Enter, Space)
- ARIA labels for icons (T020, T079)
- Screen reader announcements for theme changes
- Dropdown accessibility via Bootstrap 5

### IV. Config-Driven ✅

**Plan**: Widgets use consistent prop-based configuration.

- Base widget: icon, badge_count, badge_color props
- Theme switcher: initial_theme prop
- All widgets extensible via Cotton slots
- No template overrides required

### V. Tooling ✅

**Plan**: Standard project tooling.

- All commands via Poetry (`poetry run pytest`)
- Ruff linting and formatting
- djlint for template files
- Test coverage reporting

### VI. UI Verification (chrome-devtools-mcp) ✅

**Plan**: Visual verification at each phase.

- Base widget rendering (T026-T029)
- Badge display with various counts (T028)
- Theme switcher visual transitions (T060-T064)
- Fullscreen widget icon states (T082-T085)

### VII. Documentation Retrieval (context7) ✅

**Plan**: Use current documentation.

- django-cotton component patterns
- Bootstrap 5 dropdown accessibility
- AdminLTE 4 widget conventions
- django-easy-icons usage patterns

### VIII. End-to-End Testing (playwright) ✅

**Plan**: Complete workflow coverage.

- Base widget: Custom widget creation with icon, badge, dropdown (T030-T034)
- Theme switcher: Change theme, verify persistence, test auto mode (T065-T070)
- Fullscreen: Toggle on/off, ESC key handling (T086-T089)

---

## Phase 1: Setup & Documentation Research

**Purpose**: Gather documentation, validate assumptions, set up component structure

**Constitutional Requirements**: VII (Documentation Retrieval)

### Context7 Documentation Retrieval

- [ ] T001 [P] Retrieve django-cotton documentation for component slots and props patterns
- [ ] T002 [P] Retrieve Bootstrap 5 dropdown documentation for accessibility patterns
- [ ] T003 [P] Verify required icon aliases exist in EASY_ICONS settings (theme_light, maximize, minimize)
- [ ] T004 [P] Review django-easy-icons documentation for c-icon component usage

### Project Setup

- [ ] T005 Create component directory structure: `mvp/templates/cotton/navbar/widgets/`
- [ ] T006 Create JavaScript directory: `mvp/static/js/navbar/`
- [ ] T007 [P] Create test directory structure for widget tests
- [ ] T008 [P] Verify django-easy-icons is configured and c-icon component available

**Checkpoint**: Foundation setup complete, documentation retrieved

---

## Phase 2: Base Widget Component (US1 - Priority P1)

**Goal**: Create reusable base widget that all other widgets extend

**Independent Test**: Custom widget with icon, badge, dropdown renders correctly

**Constitutional Requirements**: I (Test-First), VI (UI Verification)

### Tests for Base Widget (Write FIRST)

- [ ] T009 [P] Test base widget renders with icon alias in tests/test_navbar_base_widget.py
- [ ] T010 [P] Test base widget uses c-icon component (not direct <i> tags)
- [ ] T011 [P] Test base widget displays badge with count
- [ ] T012 [P] Test base widget hides badge when count is zero
- [ ] T013 [P] Test base widget renders {{ slot }} content
- [ ] T014 [P] Test badge supports Bootstrap color classes (danger, warning, info, success)
- [ ] T015 [P] Test badge displays "99+" when count > 99
- [ ] T016 [P] Test base widget follows AdminLTE nav-item dropdown pattern
- [ ] T017 [P] Test base widget handles negative badge counts (hide badge)

### Implementation for Base Widget

- [ ] T018 Create base widget component: `cotton/navbar/widgets/index.html`
- [ ] T019 Add icon prop and use `<c-icon name="{{ icon }}" />` for rendering
- [ ] T020 Add ARIA label to widget link
- [ ] T021 Add badge_count prop with conditional rendering ({% if badge_count %})
- [ ] T022 Add badge_color prop with Bootstrap color class support
- [ ] T023 Add {{ slot }} for dropdown content injection
- [ ] T024 Implement badge "99+" logic for counts > 99
- [ ] T025 Add AdminLTE nav-item dropdown classes

### UI Verification (Constitutional VI)

- [ ] T026 Use chrome-devtools-mcp to verify base widget renders correctly
- [ ] T027 Verify icon renders via c-icon component (not direct <i> tag)
- [ ] T028 Verify badge displays with different counts (0, 5, 99, 100, 1000 displays as "999+")
- [ ] T029 Verify dropdown opens on click with custom content

### E2E Testing (Constitutional VIII)

- [ ] T030 [P] Playwright test: Create custom widget with base component
- [ ] T031 [P] Playwright test: Verify icon renders correctly
- [ ] T032 [P] Playwright test: Verify badge count displays
- [ ] T033 [P] Playwright test: Click widget, verify dropdown opens
- [ ] T034 [P] Playwright test: Verify dropdown content from {{ slot }}

**Checkpoint**: Base widget component complete and tested - ready for extension

---

## Phase 3: Theme Switcher Widget (US2 - Priority P1)

**Goal**: Provide theme switcher with localStorage persistence and auto-mode support

**Independent Test**: Toggle themes, verify persistence across page reloads

**Constitutional Requirements**: I (Test-First), VI (UI Verification), VIII (E2E)

### Tests for Theme Switcher (Write FIRST)

- [ ] T035 [P] Test theme switcher renders with Light/Dark/Auto options
- [ ] T036 [P] Test theme switcher uses theme_light icon alias
- [ ] T037 [P] Test theme switcher applies theme immediately
- [ ] T038 [P] Test localStorage persistence (mock localStorage)
- [ ] T039 [P] Test session-only mode when localStorage unavailable
- [ ] T040 [P] Test auto mode respects system preference
- [ ] T041 [P] Test active theme icon updates

### Tests for Theme Switcher JavaScript

- [ ] T042 [P] Test JavaScript detects initial theme preference
- [ ] T043 [P] Test JavaScript applies theme to <html data-bs-theme>
- [ ] T044 [P] Test JavaScript persists to localStorage
- [ ] T045 [P] Test JavaScript handles localStorage unavailable
- [ ] T046 [P] Test JavaScript detects system dark mode (matchMedia)
- [ ] T047 [P] Test JavaScript updates on system preference change

### Implementation for Theme Switcher

- [ ] T048 [P] Create theme switcher component: `cotton/navbar/widgets/theme-switcher.html`
- [ ] T049 Use base widget with theme_light icon alias
- [ ] T050 Add dropdown with Light/Dark/Auto options
- [ ] T051 Add active state indicators for current theme
- [ ] T052 Create theme-switcher.js: `mvp/static/js/navbar/theme-switcher.js`
- [ ] T053 Implement theme detection (localStorage → system → default)
- [ ] T054 Implement theme application (data-bs-theme attribute on <html>)
- [ ] T055 Add localStorage persistence with try/catch
- [ ] T056 Implement system preference detection (window.matchMedia)
- [ ] T057 Add event listeners for theme option clicks
- [ ] T058 Update active state on theme change
- [ ] T059 Add listener for system preference changes

### UI Verification (Constitutional VI)

- [ ] T060 Use chrome-devtools-mcp to verify theme switcher renders
- [ ] T061 Verify theme_light icon displays via c-icon
- [ ] T062 Verify theme changes immediately (< 100ms)
- [ ] T063 Verify no visual flicker during theme transition
- [ ] T064 Verify active theme indicator updates

### E2E Testing (Constitutional VIII)

- [ ] T065 [P] Playwright test: Load page, verify theme switcher visible
- [ ] T066 [P] Playwright test: Click widget, verify dropdown opens
- [ ] T067 [P] Playwright test: Select Dark theme, verify applied to <html>
- [ ] T068 [P] Playwright test: Reload page, verify theme persists
- [ ] T069 [P] Playwright test: Select Auto, verify system preference respected
- [ ] T070 [P] Playwright test: Clear localStorage, verify session-only mode

**Checkpoint**: Theme switcher functional with persistence and graceful degradation

---

## Phase 4: Fullscreen Widget (US3 - Priority P2)

**Goal**: Provide fullscreen toggle using AdminLTE 4's built-in fullscreen plugin

**Independent Test**: Toggle fullscreen on/off, verify ESC key handling

**Constitutional Requirements**: I (Test-First), VI (UI Verification), VIII (E2E)

### Tests for Fullscreen Widget (Write FIRST)

- [ ] T071 [P] Test fullscreen widget renders with maximize icon alias
- [ ] T072 [P] Test widget uses AdminLTE data-lte-toggle="fullscreen"
- [ ] T073 [P] Test widget hidden when fullscreen API unavailable
- [ ] T074 [P] Test icon updates based on fullscreen state
- [ ] T075 [P] Test ARIA label for accessibility

### Implementation for Fullscreen Widget

- [ ] T076 [P] Create fullscreen widget: `cotton/navbar/widgets/fullscreen.html`
- [ ] T077 Use base widget with maximize icon alias
- [ ] T078 Add data-lte-toggle="fullscreen" for AdminLTE integration
- [ ] T079 Add ARIA label for accessibility
- [ ] T080 Remove dropdown (no dropdown needed for fullscreen toggle)
- [ ] T081 Add conditional rendering based on Fullscreen API support

### UI Verification (Constitutional VI)

- [ ] T082 Use chrome-devtools-mcp to verify fullscreen widget renders
- [ ] T083 Verify maximize icon displays via c-icon
- [ ] T084 Verify data-lte-toggle attribute present
- [ ] T085 Verify widget toggles fullscreen on click

### E2E Testing (Constitutional VIII)

- [ ] T086 [P] Playwright test: Load page, verify fullscreen widget visible
- [ ] T087 [P] Playwright test: Click widget, verify fullscreen entered
- [ ] T088 [P] Playwright test: Click again, verify fullscreen exited
- [ ] T089 [P] Playwright test: Press ESC in fullscreen, verify exit

**Checkpoint**: Fullscreen widget functional with graceful API detection

---

## Phase 5: Documentation & Polish

**Purpose**: Finalize documentation and ensure production readiness

**Constitutional Requirements**: II (Documentation-First), V (Tooling)

### Documentation (Constitutional II)

- [ ] T090 [P] Update README.md with navbar widgets section
- [ ] T091 [P] Create docs/navbar-widgets.md with base widget examples
- [ ] T092 [P] Document icon usage with c-icon component and EASY_ICONS aliases
- [ ] T093 [P] Document Cotton slot syntax ({{ slot }} and named slots)
- [ ] T094 [P] Add theme switcher configuration guide
- [ ] T095 [P] Add fullscreen widget integration guide
- [ ] T096 [P] Document all component props and slots
- [ ] T097 [P] Add troubleshooting section (localStorage, fullscreen API, icon aliases)
- [ ] T098 [P] Create quickstart guide for each widget type

### Code Quality (Constitutional V)

- [ ] T099 Run pytest to verify all tests pass
- [ ] T100 Run ruff check and format on all Python files
- [ ] T101 Run djlint on all templates
- [ ] T102 Verify playwright tests pass in CI environment
- [ ] T103 Check test coverage (aim for >90%)

### Integration & Examples

- [ ] T104 [P] Update demo/ app with all widget types
- [ ] T105 [P] Verify required icon aliases exist in EASY_ICONS
- [ ] T106 [P] Test widgets in development server
- [ ] T107 [P] Verify mobile responsiveness in browser

**Checkpoint**: Feature complete, documented, and production-ready

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - start immediately
- **Base Widget (Phase 2)**: Depends on Phase 1 - BLOCKS all other widgets
- **Theme Switcher (Phase 3)**: Depends on Phase 2 - MVP priority
- **Fullscreen (Phase 4)**: Depends on Phase 2 - Can run parallel with Phase 3
- **Documentation (Phase 5)**: Depends on all implementation phases

### User Story Completion Order

1. **MVP (Phases 1-3)**: Setup + Base Widget + Theme Switcher
2. **Phase 4**: Fullscreen (enhancement)
3. **Phase 5**: Documentation & Polish

### Parallel Opportunities

#### Phase 1 (Setup) - Sequential (critical path)

```bash
# Must complete in order
1. Documentation retrieval (T001-T004)
2. Directory setup (T005-T008)
```

#### Phase 2 (Base Widget) - BLOCKS all widgets

Must complete base widget before widget implementations can begin.

#### Phase 3-4 (Widgets) - Can run parallel after Phase 2

```bash
# Terminal 1: Theme Switcher (T035-T070)
poetry run pytest tests/test_theme_switcher.py

# Terminal 2: Fullscreen Widget (T071-T089)
poetry run pytest tests/test_fullscreen.py
```

---

## Implementation Strategy

### MVP-First Approach

**Minimum Viable Product** = Phase 1 + Phase 2 + Phase 3

This delivers:

- Foundation (base widget component with c-icon and {{ slot }})
- Theme switcher widget (demonstrates full pattern with JS)
- Complete test coverage
- Basic documentation

**Time estimate**: ~10-14 hours

### Incremental Delivery

1. **MVP (Phases 1-3)**: Base + Theme Switcher - Core pattern established
2. **Phase 4**: Fullscreen - Additional generic widget
3. **Phase 5**: Documentation & Polish - Production-ready release

### Validation Checkpoints

After each phase, validate:

- [ ] All tests for that phase pass
- [ ] Ruff linting passes
- [ ] djlint passes on templates
- [ ] chrome-devtools-mcp verification complete
- [ ] Manual smoke test of feature works
- [ ] Documentation updated for new behavior

---

## Risk Assessment

### Technical Risks

1. **Icon alias dependencies** - Required aliases may not exist in EASY_ICONS
   - *Mitigation*: T003 verifies aliases early, add missing ones before implementation
2. **localStorage unavailable** - Theme switcher must gracefully degrade
   - *Mitigation*: T039, T045 test session-only mode explicitly
3. **Fullscreen API support** - Not available in all browsers
   - *Mitigation*: T073, T081 implement feature detection and graceful hiding
4. **Cotton slot syntax** - Misunderstanding slot implementation
   - *Mitigation*: Spec now clearly documents {{ slot }} and <c-slot name="..."> usage

### Integration Risks

1. **AdminLTE 4 compatibility** - Navbar structure changes
   - *Mitigation*: T016 tests AdminLTE pattern compliance
2. **Bootstrap 5 dropdown** - Accessibility requirements
   - *Mitigation*: T002 retrieves current Bootstrap docs, Phase 2 tests accessibility

---

## Test Organization

### Required Test Coverage

- Base widget component rendering with c-icon
- Badge display logic (0, 5, 99+)
- Cotton slot injection ({{ slot }})
- Theme switcher JavaScript (localStorage, system preference)
- Fullscreen API integration
- Icon alias resolution
- Accessibility (ARIA, keyboard navigation)
- Mobile responsiveness

### Test File Structure

```
tests/
├── test_navbar_base_widget.py        # T009-T017: Base widget component
├── test_theme_switcher.py            # T035-T047: Theme switcher
├── test_fullscreen_widget.py         # T071-T075: Fullscreen toggle
└── e2e/
    ├── test_base_widget_e2e.py       # T030-T034: Base widget workflows
    ├── test_theme_switcher_e2e.py    # T065-T070: Theme switching flows
    └── test_fullscreen_e2e.py        # T086-T089: Fullscreen workflows
```

### Test Commands

```bash
# Run all navbar widget tests
poetry run pytest tests/test_navbar_*.py

# Run with coverage
poetry run pytest --cov=mvp --cov-report=html

# Run E2E tests
poetry run pytest tests/e2e/test_*_e2e.py

# Run specific widget tests
poetry run pytest tests/test_theme_switcher.py -v
```

---

## Success Metrics

### Functional Completeness

- ✅ Base widget component created and tested
- ✅ Theme switcher with persistence implemented
- ✅ Fullscreen widget integrated
- ✅ All icon aliases via c-icon component
- ✅ All slots use {{ slot }} syntax

### Quality Metrics

- Test coverage: >90%
- All linting checks pass (Ruff, djlint)
- No accessibility violations
- All E2E tests passing
- Documentation complete with examples

### Performance Targets

- Theme switch: <100ms (SC-003)
- Widget dropdown: <50ms open time
- Page load impact: <10ms additional load time

---

## Future Enhancements (Deferred)

These features are explicitly out of scope for this implementation:

- User Profile Widget (requires authentication context)
- Messages Widget (requires messaging system)
- Notifications Widget (requires notification backend)
- Custom theme color definitions
- AJAX-based dropdown content
- Widget reordering/customization UI
- Real-time updates via WebSocket

These will be addressed in future specifications once the foundational pattern is established.
