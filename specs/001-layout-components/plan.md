# Implementation Plan: AdminLTE Layout Component Separation

**Branch**: `001-layout-components` | **Date**: 2026-01-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-layout-components/spec.md`

## Summary

Split the AdminLTE layout into 5 separate Cotton components (app, header, sidebar, main, footer) to enable granular customization and composition flexibility. Technical approach: Create component subdirectories under templates/cotton/app/ with Cotton c-vars for configuration, update base.html to compose components with default layout in the `app` block, and provide slot-based content injection. This allows developers to override layouts by extending base.html and recomposing components in the `app` block.

## Technical Context

**Language/Version**: Python 3.10-3.12
**Primary Dependencies**: Django 4.2-5.x, django-cotton >=2.3.1, AdminLTE 4 (CSS via CDN)
**Storage**: N/A (no database changes - template/static files only)
**Testing**: pytest, pytest-django (component rendering tests)
**Target Platform**: Web browsers (Chrome, Firefox, Safari, Edge)
**Project Type**: Django reusable app package
**Performance Goals**: No performance impact - pure template refactoring
**Constraints**:

- Must maintain AdminLTE 4 CSS class naming conventions
- Must not break existing layouts/templates
- Must work with django-cotton's attribute/slot system
- Components must render exact AdminLTE grid structure
**Scale/Scope**: 5 layout components, 11 template files total

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

✅ **Test-first approach is feasible and planned**

- Tests can be written first for component rendering with various configurations
- Tests for CSS class generation based on c-vars
- Tests for slot content rendering
- Tests for component composition in templates

✅ **Test types are identified**

- pytest-django for Cotton component rendering tests using `cotton_render()`
- Integration tests for base.html template composition
- Unit tests for component structure validation
- No pytest-playwright needed (layout is pure CSS, not JS interactions)

✅ **Documentation updates are included**

- Document each component's c-vars and slots
- Update quickstart with component composition examples
- Document base.html override pattern for custom layouts
- Add examples for common layout variations

✅ **Quality gates are understood**

- All tests pass via `poetry run pytest`
- Ruff linting passes
- Ruff formatting applied
- djlint for template formatting

---

### Post-Design Re-Evaluation (Phase 1 Complete)

*To be completed after Phase 1 design is finalized*

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
mvp/                           # Django app package
├── templates/
│   ├── base.html           # Root template with app block containing default 5-component layout
│   └── cotton/
│       └── app/             # Layout component directory
│           ├── index.html   # App component (top-level .app-wrapper orchestrator)
│           ├── footer.html  # Footer component (flat file)
│           ├── header/
│           │   ├── index.html   # Header orchestrator with navbar
│           │   └── toggle.html  # Sidebar toggle button
│           ├── sidebar/
│           │   ├── index.html     # Sidebar orchestrator
│           │   ├── branding.html  # Logo/brand text
│           │   └── menu.html      # Navigation menu wrapper
│           └── main/
│               ├── index.html         # Main content orchestrator
│               ├── content_header.html # Page title/breadcrumbs
│               └── content.html        # Main content wrapper

tests/
├── test_app_components.py      # Component rendering tests
└── test_base_template.py        # Template composition integration tests

demo/                       # Demo app
├── templates/
│   └── demo/
│       └── dashboard.html      # Example using default layout
└── views.py
```

**Structure Decision**: Django reusable app structure with templates organized under cotton/app/ directory. Each layout component is either a subdirectory with sub-components (header/, sidebar/, main/, app/) or a flat file (footer.html). Base template (base.html) provides default layout composition in the `app` block. Developers extend base.html and override `app` block for custom layouts.

## Complexity Tracking

No complexity violations - this is a straightforward template refactoring with no additional architectural complexity beyond what Django Cotton already provides.
