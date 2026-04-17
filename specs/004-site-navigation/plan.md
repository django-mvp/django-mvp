# Implementation Plan: Configurable Site Navigation Menu System

**Branch**: `004-site-navigation` | **Date**: January 7, 2026 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-site-navigation/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command.

## Summary

Django-mvp will provide a configurable menu system using django-flex-menus for defining navigation hierarchies programmatically in Python. The menu will be automatically rendered in the AdminLTE 4 sidebar using custom Cotton components that implement AdminLTE's nested nav structure (`.sidebar-menu`, `.nav-item`, `.nav-treeview`). A custom renderer will bridge django-flex-menus with Cotton templates, supporting single menu items (rendered first) and hierarchical menu groups (rendered after, with `.nav-header` separators). The default `AppMenu` in `mvp.menus` will be empty, allowing users to populate it via imports in their own app modules. App ordering determines menu item sequence.

## Technical Context

**Language/Version**: Python 3.10-3.12 (Django MVP supports 3.10, 3.11, 3.12)
**Primary Dependencies**: Django 4.2-5.x, django-flex-menus ^0.4.1, django-cotton ^2.3.1, django-easy-icons ^0.4.0, django-cotton-bs5 ^0.5.1
**Storage**: N/A (menu configuration is code-based, not database-backed)
**Testing**: pytest ^8.0.0, pytest-django ^4.9.0 (pytest-playwright if testing UI interactions)
**Target Platform**: Web application (Django server-rendered templates with AdminLTE 4 frontend)
**Project Type**: Django reusable app (single-project structure)
**Performance Goals**: Menu rendering <50ms for 50+ items, minimal template overhead
**Constraints**: Must integrate with existing AdminLTE 4 sidebar CSS classes, must work with django-cotton's component system, must not break existing MVP layout structure
**Scale/Scope**: Support 50+ menu items across multiple nested levels, handle 10+ Django apps contributing menu items

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- ✅ Test-first approach is feasible and planned (tests can be written before implementation).
  - pytest tests for menu definition API
  - pytest-django tests for menu rendering with Cotton components
  - pytest tests for custom renderer behavior
  - Integration tests for multi-app menu assembly
- ✅ Test types are identified (pytest, pytest-django, pytest-playwright as needed).
  - Unit tests: Menu/MenuItem instantiation, renderer template selection logic
  - Integration tests: Menu rendering in sidebar component, icon integration, URL resolution
  - (Optional) Browser tests: Visual verification of nested menu structure, collapsible behavior
- ✅ Documentation updates are included for any public behavior change.
  - Document `AppMenu` in mvp.menus
  - Document custom renderer API
  - Document Cotton menu component c-vars
  - Provide quickstart guide for defining menus
  - Update main README with navigation example
- ✅ Quality gates are understood (tests + lint + format).
  - Poetry run pytest for all tests
  - Ruff for linting and formatting
  - djlint for template linting

## Project Structure

### Documentation (this feature)

```text
specs/004-site-navigation/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── menu-api.md      # Menu and MenuItem class signatures
│   ├── renderer-api.md  # Custom renderer interface
│   └── template-api.md  # Cotton component c-vars
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
mvp/
├── menus.py                           # Contains AppMenu instance (empty by default)
├── renderers.py                       # Custom renderer for AdminLTE sidebar
└── templates/
    ├── cotton/
    │   └── app/
    │       └── sidebar/
    │           ├── menu.html          # [OPTIONAL] Container component for custom implementations
    │           ├── menu.item.html     # [OPTIONAL] Single/parent item component
    │           └── menu-header.html   # [OPTIONAL] Section header component
    └── menus/
        ├── container.html             # Root menu template (for renderer depth 0)
        ├── single-item.html           # Leaf item template (no children)
        ├── parent-item.html           # Parent item template (has children)
        ├── group-header.html          # Group header template
        └── nested-item.html           # Nested child item template

tests/
├── test_menu_definition.py            # Tests for AppMenu instantiation, item addition
├── test_menu_rendering.py             # Tests for Cotton component rendering
├── test_custom_renderer.py            # Tests for renderer template selection
└── test_menu_integration.py           # Tests for multi-app menu assembly, URL resolution

demo/
└── menus.py                           # Example showing how to populate AppMenu
```

**Structure Decision**: Django reusable app structure (Option 1 equivalent). Menu system is an extension of the existing MVP app, not a separate project. Cotton components live in `mvp/templates/cotton/app/sidebar/` to maintain MVP's component organization. Renderer templates live in `mvp/templates/menus/` following django-flex-menus conventions. Tests follow pytest-django structure with test files matching implementation modules.

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
