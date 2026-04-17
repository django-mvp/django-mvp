# Implementation Plan: Inner Layout System

**Branch**: `006-page-layout` | **Date**: January 19, 2026 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-page-layout/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command.

## Summary

This feature introduces an inner layout system for the Django MVP package, providing a nested, configurable layout structure within the outer AdminLTE 4 layout. The inner layout uses CSS Grid (mirroring AdminLTE's app-wrapper pattern) and Django Cotton components to create four configurable areas: toolbar (top), footer (bottom), secondary sidebar (right), and main content (center). The main component `<c-page>` accepts attributes for fixed positioning (`fixed_header`, `fixed_footer`, `fixed_sidebar`), sidebar behavior (`sidebar_expand`), and custom classes. Sub-components use dot notation: `<c-page.toolbar>`, `<c-page.footer>`, `<c-page.sidebar>`. The toolbar can include a toggle widget (`<c-page.toolbar.widget>`) for collapsing the sidebar.

## Technical Context

**Language/Version**: Python 3.10+, Django 4.2-5.x
**Primary Dependencies**: Django (>=4.2,<6.0), django-cotton (>=2.3.1), django-cotton-bs5 (^0.5.1), Bootstrap 5.3
**Storage**: N/A (UI components only, no data persistence)
**Testing**: pytest, pytest-django (Cotton component tests with cotton_render), pytest-playwright (E2E UI tests)
**Target Platform**: Web browsers (responsive from 320px mobile to 4K displays)
**Project Type**: Web application (Django reusable app providing Cotton components)
**Performance Goals**: Initial render <100ms for typical layouts, CSS Grid layout updates <16ms (60fps), no layout shift (CLS < 0.1)
**Constraints**: Must work with existing outer layout without conflicts, sticky positioning within scroll areas (not viewport-fixed), default breakpoint 'lg' (1024px) for sidebar visibility
**Scale/Scope**: Single reusable Django app, ~3-5 new Cotton components, integrates with existing MVP configuration, affects all pages using inner layout

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Initial Check (Before Phase 0) ✅ PASSED

- ✅ Design-first approach is feasible and planned (implementation before test writing) - will implement Cotton components first, verify visually, then write tests
- ✅ Visual verification approach is planned (chrome-devtools-mcp for UI validation) - will verify CSS Grid layout, sticky positioning, and responsive behavior
- ✅ Test types are identified (pytest, pytest-django, pytest-playwright as needed) for post-implementation - Cotton component tests with cotton_render() + E2E tests for layout interactions
- ✅ Documentation updates are included for any public behavior change - will document all Cotton components and their attributes
- ✅ Quality gates are understood (tests + lint + format) - poetry run pytest, ruff check/format
- ✅ Documentation retrieval is planned (context7 for up-to-date library docs) - will fetch django-cotton, Bootstrap 5.3, and CSS Grid best practices
- ✅ End-to-end testing is planned (playwright for complete user workflows after implementation) - will test full page layouts with all inner layout combinations

**Initial Gate Status**: ✅ PASS - All gates satisfied, ready for Phase 0 research

### Post-Phase 1 Check (After Design) ✅ PASSED

- ✅ **Design-first workflow**: Design complete via research.md, data-model.md, contracts/, and quickstart.md. Ready for implementation → visual verification → testing
- ✅ **Visual verification planned**: Will use chrome-devtools-mcp to verify CSS Grid rendering, sticky positioning behavior, responsive breakpoints, and sidebar toggle functionality
- ✅ **Test strategy defined**:
  - Unit tests: `tests/components/test_page_layout.py` using `django_cotton.cotton_render()`
  - Integration tests: `tests/integration/test_page_layout_integration.py` for outer layout compatibility
  - E2E tests: `tests/e2e/test_page_layout_e2e.py` using pytest-playwright for browser interactions
- ✅ **Documentation complete**:
  - API contract: `contracts/page_layout.md` (component attributes, slots, HTML output)
  - Quick start guide: `quickstart.md` (5-minute tutorial, common patterns, troubleshooting)
  - Data model: `data-model.md` (component entities, CSS architecture, accessibility)
- ✅ **Quality gates ready**: Tests will verify all functionality before merge. Linting/formatting via Ruff
- ✅ **Documentation retrieval executed**: Context7 used for django-cotton, Bootstrap 5.3, and CSS Grid best practices (see research.md)
- ✅ **E2E testing planned**: Playwright tests will cover sticky positioning, responsive behavior, sidebar toggle, and session persistence

**Post-Design Gate Status**: ✅ PASS - Design phase complete, all constitution requirements satisfied. Ready for Phase 2 (task breakdown) and implementation.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
mvp/                          # Main Django app package
├── templates/
│   └── cotton/
│       └── inner/
│           ├── index.html             # EXISTING: Main <c-page> component
│           ├── toolbar.html           # EXISTING: Toolbar sub-component (<c-page.toolbar>)
│           ├── footer.html            # EXISTING: Footer sub-component (<c-page.footer>)
│           ├── sidebar.html           # EXISTING: Sidebar sub-component (<c-page.sidebar>)
│           ├── content.html           # EXISTING: Content wrapper component
│           └── toolbar/
│               └── widget.html        # EXISTING: Toolbar toggle widget (<c-page.toolbar.widget>)
├── static/
│   └── mvp/
│       ├── scss/
│       │   └── _page-layout.scss     # EXISTING: Inner layout styles (CSS Grid)
│       └── js/
│           └── page-layout.js        # EXISTING: Sidebar toggle functionality
└── context_processors.py             # Existing (no changes expected)

tests/
├── components/
│   └── test_page_layout.py          # NEW: Component unit tests
├── integration/
│   └── test_page_layout_integration.py  # NEW: Integration tests
└── e2e/
    └── test_page_layout_e2e.py      # NEW: Playwright E2E tests

docs/
└── page-layout.md                   # NEW: Component documentation
```

**Structure Decision**: This is a Django reusable app with Cotton component-based architecture. Components live in `mvp/templates/cotton/inner/` following Cotton naming conventions (folder-based components with dot notation). Styles use SCSS and will be compiled via django-compressor. Tests follow existing structure: unit tests for component rendering, integration tests for template inheritance, E2E tests for browser interactions.

## Implementation Phases

### Phase 0: Demo View & Navigation Setup (Visual Progress Monitoring)

**Purpose**: Create demo page infrastructure to enable visual monitoring of implementation progress throughout all subsequent phases.

**Tasks**:

1. **Create demo view**
   - Add `page_layout_demo` view to `demo/views.py`
   - Follow pattern of existing `layout_demo` view
   - Support query parameters for testing configurations (toolbar_fixed, footer_fixed, sidebar_fixed, sidebar_breakpoint, sidebar_toggleable)
   - Context variables: fixed_sidebar, fixed_header, fixed_footer, breakpoint options

2. **Create demo template**
   - Add `demo/templates/demo/page_layout.html` (already exists, update if needed)
   - Extend `base.html`
   - Use `<c-page>` component with configurable attributes
   - Include configuration form in sidebar (similar to layout_demo)
   - Show rich content in main area for scrolling/sticky testing

3. **Add URL routing**
   - Add route to `demo/urls.py`: `path("page-layout/", views.page_layout_demo, name="page_layout_demo")`

4. **Add menu item**
   - Update `demo/menus.py` to add "Inner Layout" menu item (already exists in file, verify it's active)
   - Position: After "Navbar Widgets" menu item
   - Icon: `layout-text-sidebar`
   - Badge: "New" with `text-bg-warning` classes

**Acceptance Criteria**:

- ✅ Demo view accessible at `/page-layout/`
- ✅ Menu item appears in AppMenu sidebar
- ✅ Demo page renders with current `<c-page>` component
- ✅ Configuration form allows toggling all attributes
- ✅ Query parameters update layout in real-time

**Visual Verification**: Use chrome-devtools-mcp to verify:

- Menu item renders correctly
- Demo page loads without errors
- Configuration form is functional

### Phase 1: Core Component Implementation

**Prerequisites**: Phase 0 complete

**Tasks**:

1. **Update/verify component templates**
   - Verify `mvp/templates/cotton/inner/index.html` (main wrapper)
   - Verify `mvp/templates/cotton/inner/toolbar.html`
   - Verify `mvp/templates/cotton/inner/footer.html`
   - Verify `mvp/templates/cotton/inner/sidebar.html`
   - Verify `mvp/templates/cotton/inner/toolbar/widget.html`

2. **Implement SCSS styles**
   - Create/update `mvp/static/mvp/scss/_page-layout.scss`
   - CSS Grid structure matching AdminLTE 4 pattern
   - Sticky positioning classes (toolbar-fixed, footer-fixed, sidebar-fixed)
   - Sidebar collapse behavior
   - Responsive breakpoints (sm, md, lg, xl, xxl)

3. **Implement JavaScript toggle**
   - Create/update `mvp/static/mvp/js/page-layout.js`
   - Sidebar toggle functionality
   - SessionStorage persistence
   - Mobile overlay support
   - ARIA state management

**Acceptance Criteria**:

- ✅ All component templates render correctly
- ✅ CSS Grid layout matches AdminLTE 4 pattern
- ✅ Sticky positioning works for toolbar/footer/sidebar
- ✅ Sidebar collapse animation smooth
- ✅ Responsive behavior correct at all breakpoints
- ✅ Toggle button works on desktop and mobile

**Visual Verification**: Use chrome-devtools-mcp to verify:

- Grid structure in DevTools
- Sticky positioning behavior
- Responsive breakpoints
- Toggle animations

### Phase 2: Testing & Validation

**Prerequisites**: Phase 1 complete

**Tasks**:

1. **Unit tests**
   - Create `tests/components/test_page_layout.py`
   - Test component rendering with django_cotton.cotton_render()
   - Test all attribute combinations
   - Test slot rendering

2. **Integration tests**
   - Create `tests/integration/test_page_layout_integration.py`
   - Test compatibility with outer layout
   - Test multiple inner layouts on same page

3. **E2E tests**
   - Create `tests/e2e/test_page_layout_e2e.py`
   - Use pytest-playwright
   - Test sticky positioning behavior
   - Test sidebar toggle functionality
   - Test responsive behavior
   - Test session persistence

**Acceptance Criteria**:

- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ All E2E tests pass
- ✅ Code coverage >90%
- ✅ No lint errors (ruff check)
- ✅ Code formatted (ruff format)

### Phase 3: Documentation & Polish

**Prerequisites**: Phase 2 complete

**Tasks**:

1. **Update documentation**
   - Create `docs/page-layout.md` with component guide
   - Update demo page with comprehensive examples
   - Add inline code comments

2. **Polish demo page**
   - Add more example configurations
   - Add code snippets showing usage
   - Add performance metrics display

3. **Final verification**
   - Cross-browser testing (Chrome, Firefox, Safari, Edge)
   - Accessibility audit
   - Performance profiling

**Acceptance Criteria**:

- ✅ Documentation complete and accurate
- ✅ Demo page shows all features
- ✅ Works in all major browsers
- ✅ Accessibility score >95%
- ✅ Performance metrics meet goals (<100ms render, 60fps)

---

**Next Steps**: Run Phase 0 tasks to create demo infrastructure, then proceed through phases sequentially with visual verification at each step.
