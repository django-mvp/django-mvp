# Implementation Plan: Cotton App Layout Configuration

**Branch**: `010-cotton-layout-config` | **Date**: 2026-04-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/010-cotton-layout-config/spec.md`

## Summary

Implement a complete Cotton-based application layout system where all AdminLTE 4 layout
behaviour is configured exclusively through component attributes. The system provides
five core components (`<c-app>`, `<c-app.header>`, `<c-app.sidebar>`, `<c-app.main>`,
`<c-app.footer>`) that compose a production-ready application shell. Layout modes
(fixed sidebar/header/footer, collapsible sidebar, fill mode) are controlled by boolean
and string attributes on `<c-app>` which map directly to AdminLTE 4 body CSS classes.
Attributes are declared in kebab-case in templates (for example, `<c-app fixed-sidebar sidebar-expand="lg">`);
django-cotton normalizes kebab-case names to snake_case for component consumption.
No settings.py, view context, or `:attrs` dict configuration is supported — Cotton
attributes are the sole configuration pathway.

## Technical Context

**Language/Version**: Python 3.11+ / Django 4.2–5.x
**Primary Dependencies**: django-cotton (>=2.3.1), django-cotton-bs5 (>=0.9.0), django-flex-menus (>=0.4.1), django-easy-icons (>=0.5), AdminLTE 4 (rc3, bundled locally), Bootstrap 5
**Storage**: N/A (no database models — all state is declarative via template attributes)
**Testing**: pytest + pytest-django (unit/integration), pytest-playwright (E2E), cotton-test-components fixtures
**Target Platform**: Server-rendered Django web applications (modern browsers)
**Project Type**: Reusable Django app (django-mvp package)
**Performance Goals**: Standard SSR page render (<200ms); no runtime config overhead
**Constraints**: Cotton attributes are the SOLE configuration pathway; declare template attributes in kebab-case (django-cotton converts to snake_case internally); no Python-level UI config; no `:attrs` dict passing
**Scale/Scope**: 5 core layout components, ~10 attributes, 1 menu integration point

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Design-first approach is feasible and planned — implement components first, verify visually, then write tests
- [x] Visual verification approach is planned — Playwright MCP server for verifying layout modes render correctly
- [x] Test types are identified — pytest-django for component rendering (cotton_render fixtures), pytest-playwright for E2E layout verification
- [x] Documentation updates are included — quickstart.md, data-model.md, attribute reference, skills/django-mvp/SKILL.md update
- [x] Quality gates are understood — `python manage.py check` + `pytest` + `ruff` + `djlint`
- [x] Documentation retrieval is planned — context7 for django-cotton, Bootstrap 5, AdminLTE 4 docs
- [x] End-to-end testing is planned — pytest-playwright tests for all layout mode combinations and navigation flows
- [x] Tasks are grouped by user story — Story 1 (base shell), Story 2 (navigation), Story 3 (advanced modes)
- [x] Every phase touching Django code includes `python manage.py check` validation task
- [x] Every phase touching UI includes Playwright MCP verification with acceptance criteria assertions
- [x] UI configuration uses Cotton components and template overrides only — enforced by design (attributes → body classes)
- [x] Template work considered prebuilt django-cotton-bs5 components first — checked, layout shell components are custom (no django-cotton-bs5 equivalent exists)
- [x] Custom Cotton components used instead of `{% include %}` — all layout regions are Cotton components under `cotton/app/`
- [x] django-cotton-bs5 skill and django-cotton skill consulted before authoring new templates
- [x] cotton-test-components skill consulted for custom Cotton component tests
- [x] This feature touches the public API → skills/django-mvp/SKILL.md update is planned
- [x] skills/django-mvp/SKILL.md is only referenced for demo app work, not core mvp/ development
- [x] Spec includes [Developer] stories (Story 1 P1, Story 3 P2) and [End User] story (Story 2 P1)

### Post-Design Re-check

- [x] All items above still hold after Phase 1 design artifacts are complete
- [x] data-model.md confirms no Django models needed (attribute-only data model)
- [x] contracts/ define clear attribute → rendered output mappings for all 5 components
- [x] No constitution violations identified

## Project Structure

### Documentation (this feature)

```text
specs/010-cotton-layout-config/
├── plan.md              # This file
├── research.md          # Phase 0: 8 research sections covering all unknowns
├── data-model.md        # Phase 1: Component attribute model (no Django models)
├── quickstart.md        # Phase 1: Developer integration guide
├── contracts/           # Phase 1: Per-component rendering contracts
│   ├── c-app.md
│   ├── c-app-header.md
│   ├── c-app-sidebar.md
│   ├── c-app-main.md
│   └── c-app-footer.md
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
mvp/
├── templates/
│   ├── mvp/
│   │   └── base.html                 # HTML document skeleton (extends by integrators)
│   └── cotton/
│       └── app/
│           ├── index.html            # <c-app> — body wrapper, layout classes
│           ├── header.html           # <c-app.header> — top navbar
│           ├── main.html             # <c-app.main> — content area
│           ├── menu.html             # <c-app.menu> — standalone app menu (Site Navigation)
│           ├── footer.html           # <c-app.footer> — site footer
│           └── sidebar/
│               ├── index.html        # <c-app.sidebar> — navigation sidebar
│               ├── header.html       # <c-app.sidebar.header> — branding/logo block
│               ├── toggle.html       # <c-app.sidebar.toggle> — hamburger button
│               └── menu/             # Sidebar menu sub-components (via flex_menu)
│                   ├── index.html
│                   ├── item.html
│                   ├── group.html
│                   └── collapse.html
├── static/
│   ├── js/
│   │   ├── sidebar-toggle.js        # Sidebar collapse persistence
│   │   └── theme-switcher.js        # Dark/light mode toggle
│   └── scss/
│       └── _*.scss                   # Custom SCSS overrides
├── context_processors.py             # mvp_config (brand defaults, convenience)
├── menus.py                          # AppMenu, MenuGroup, MenuCollapse classes
└── views.py                          # Base views (no layout config logic)

demo/
├── templates/
│   └── base.html                     # Demo app base (extends mvp/base.html)
├── views.py                          # LayoutConfigMixin (demo-only dynamic config)
└── menus.py                          # Demo sidebar menu items

tests/
├── conftest.py                       # Shared fixtures
├── test_smoke.py                     # Existing smoke tests
└── (new test files per component)    # Cotton component tests, E2E tests

skills/
└── django-mvp/
    └── SKILL.md                      # Public API skill (update planned)

docs/
├── layout-configuration.md           # Attribute reference docs (update planned)
└── layout-data-models-api-contracts.md
```

**Structure Decision**: This is a reusable Django app with templates under `mvp/templates/cotton/app/`. No new directories are created — all components already exist in the correct locations. Implementation focuses on refining existing components, ensuring attribute contracts are complete, and adding comprehensive tests and documentation.

## Complexity Tracking

No constitution violations. No complexity justifications needed.
