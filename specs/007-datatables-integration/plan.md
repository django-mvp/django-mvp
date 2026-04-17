# Implementation Plan: Django Tables2 Integration

**Branch**: `007-datatables-integration` | **Date**: January 20, 2026 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/007-datatables-integration/spec.md`

## Summary

Integrate django-tables2 as an optional dependency for django-mvp, providing a demo page that showcases table rendering with sorting, filtering, and pagination. The integration must support two display modes: fill mode (table expands to viewport height with independent scrolling) and standard mode (content-based height with normal page scrolling). The demo is accessible via a new "Integrations" menu group in the sidebar.

**Technical Approach**: Use django-tables2's SingleTableView for the demo, configure optional dependency in pyproject.toml with semantic versioning (>=2.0.0,<3.0.0), use existing Product model for demonstration (already has 27+ products via generate_dummy_data command), implement responsive layout using Bootstrap 5 utility classes (w-100/h-100), and ensure ARIA compliance for accessibility.

## Technical Context

**Language/Version**: Python 3.10+ (project supports 3.10, 3.11, 3.12)
**Primary Dependencies**: Django 4.2-5.x, django-tables2 2.x, django-cotton 2.3.1+, django-cotton-bs5, Bootstrap 5, AdminLTE 4
**Storage**: SQLite (development), uses existing Product model with generate_dummy_data command
**Testing**: pytest, pytest-django (unit/integration), pytest-playwright (E2E UI testing)
**Target Platform**: Django web application, modern browsers (no IE11)
**Project Type**: Django application package with demo/demo app
**Performance Goals**: <1s table load time, <200ms interaction response, 60fps scrolling in fill mode
**Constraints**: <200ms p95 for table interactions, optional dependency (no base package bloat), Bootstrap 5 w-100/h-100 layout approach, ARIA-compliant markup
**Scale/Scope**: Demo page with sufficient data to overflow viewport in both dimensions (18 fields from Product model, 27+ existing products), single table view integration

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- ✅ Design-first approach is feasible and planned (implement UI first, verify visually, then write tests)
- ✅ Visual verification approach is planned (chrome-devtools-mcp for table rendering, responsive behavior, fill mode)
- ✅ Test types are identified:
  - pytest-django: View tests, model tests, menu registration, URL routing
  - pytest-playwright: E2E tests for sorting, filtering, pagination, fill mode behavior, responsive design
  - Post-implementation after visual verification confirms expected behavior
- ✅ Documentation updates are included (quickstart.md for using django-tables2 with MVP layout)
- ✅ Quality gates are understood (Ruff linting, Ruff formatting, pytest, djlint for templates)
- ✅ Documentation retrieval is planned (context7 for django-tables2 API patterns - already retrieved)
- ✅ End-to-end testing is planned (playwright for complete user journey: navigate to demo, sort, filter, paginate, resize window)

## Project Structure

### Documentation (this feature)

```text
specs/007-datatables-integration/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output - django-tables2 patterns, fill mode implementation
├── data-model.md        # Phase 1 output - Product model analysis and ProductTable definition
├── quickstart.md        # Phase 1 output - Using tables2 with MVP layouts
├── contracts/           # Phase 1 output - N/A (no API contracts for this feature)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
django-mvp/
├── pyproject.toml                        # Add optional dependency: django-tables2>=2.0.0,<3.0.0
├── demo/                              # Demo application
│   ├── models.py                         # Add SampleDataModel for table demo
│   ├── tables.py                         # NEW: django-tables2 Table class definition
│   ├── views.py                          # Add DataTablesView (SingleTableView)
│   ├── urls.py                           # Add datatables-demo URL
│   ├── menus.py                          # Add Integrations menu group + DataTables item
│   ├── management/commands/
│   │   └── generate_sample_data.py       # NEW: Management command for demo data
│   └── templates/demo/
│       └── datatables_demo.html          # NEW: Demo page template
├── mvp/
│   └── templates/
│       └── django_tables2/               # NEW: Template overrides directory
│           ├── table.html                # Bootstrap 5 + AdminLTE table styling
│           └── pagination.html           # Bootstrap 5 pagination styling (optional)
└── tests/
    ├── test_datatables_integration.py    # NEW: View/model tests (pytest-django)
    └── test_datatables_e2e.py            # NEW: E2E tests (pytest-playwright)
```

**Structure Decision**: This follows django-mvp's existing pattern:

- `demo/` app contains demo implementations for package users to reference
- `mvp/` package contains reusable template overrides
- Tests live in root `tests/` directory
- Optional dependencies declared in `pyproject.toml` extras
- Uses existing Product model and generate_dummy_data command (no new models needed)

## Complexity Tracking

> No constitution violations - feature follows all established principles

---

## Phase 0: Outline & Research ✅

**Status**: Complete
**Output**: [research.md](research.md)

### Research Questions Resolved

1. ✅ **django-tables2 Architecture & Patterns**
   - SingleTableView usage documented
   - Template customization patterns identified
   - Integration with Django ORM established

2. ✅ **Bootstrap 5 Responsive Tables & Fill Mode**
   - Fill mode implementation strategy using flexbox
   - Responsive table patterns with `.table-responsive`
   - AdminLTE 4 grid compatibility verified

3. ✅ **Template Override Structure**
   - Override location: `mvp/templates/django_tables2/`
   - ARIA compliance requirements mapped to template blocks
   - Empty state customization pattern documented

4. ✅ **Existing Product Model Analysis**
   - 18 fields available for horizontal overflow
   - 27+ existing products via generate_dummy_data
   - Already has realistic business data structure

5. ✅ **Menu Integration Pattern**
   - Registration order approach for menu placement
   - Integrations group structure defined
   - Icon selection guidance provided

6. ✅ **pyproject.toml Optional Dependencies**
   - Semantic versioning strategy: `>=2.0.0,<3.0.0`
   - Poetry extras configuration pattern documented
   - Dev dependency vs optional dependency clarified

### Key Decisions

- **View Base Class**: `SingleTableView` from django-tables2
- **Fill Mode Implementation**: Bootstrap 5 flexbox utilities (`d-flex`, `flex-column`, `h-100`, `flex-grow-1`)
- **Template Location**: `mvp/templates/django_tables2/` for reusable overrides
- **Data Source**: Existing Product model (18 fields, 27+ products)
- **Menu Placement**: Registration order (Integrations group registered early)
- **Version Constraint**: Major version lock (`>=2.0.0,<3.0.0`)

---

## Phase 1: Design & Contracts ✅

**Status**: Complete
**Outputs**:

- [data-model.md](data-model.md)
- [quickstart.md](quickstart.md)
- contracts/ (N/A - no API contracts for UI feature)

### Deliverables

#### 1. Data Model ([data-model.md](data-model.md))

**Entities Defined**:

- `Product` (Existing Django Model): 18-field model with categories, pricing, inventory
- `ProductTable` (django-tables2 Table): Table class with styling and configuration
- Data Source: Existing `generate_dummy_data` command (creates 27+ products)

**Key Specifications**:

- Field types and constraints documented
- Table CSS classes for AdminLTE 4 styling
- ARIA attributes for accessibility
- Empty state message configuration
- Database schema and migration structure

#### 2. Quickstart Guide ([quickstart.md](quickstart.md))

**Content Coverage**:

- Installation instructions (optional dependency)
- Quick start tutorial (5 minutes to working table)
- Fill mode vs standard mode comparison
- Configuration options (pagination, sorting, filtering)
- Styling and customization patterns
- Accessibility features
- Advanced patterns and performance tips
- Troubleshooting guide

**Code Examples**:

- Model creation
- Table definition
- View setup
- Template patterns (both modes)
- Filtering integration
- Custom styling

#### 3. Agent Context Update

**Updated File**: `.github/agents/copilot-instructions.md`

**Added Technologies**:

- django-tables2 2.x
- Python 3.10+ context
- Django 4.2-5.x compatibility
- SQLite development database

---

## Phase 1 Post-Design Constitution Re-Check ✅

### Design-First Verification

- ✅ **UI First**: Template structure designed before test implementation
- ✅ **Visual Verification Planned**: chrome-devtools-mcp will verify table rendering, fill mode behavior
- ✅ **Test Strategy Clear**: Tests written after UI verification confirms expected behavior

### Documentation Verification

- ✅ **Public Behavior Documented**: quickstart.md covers all user-facing functionality
- ✅ **Usage Examples Provided**: Quick start includes working code for common scenarios
- ✅ **Integration Patterns**: Fill mode vs standard mode documented with templates

### Quality Gates Verification

- ✅ **Test Coverage Planned**: pytest-django for unit/integration, pytest-playwright for E2E
- ✅ **Linting/Formatting**: Ruff configured, djlint for templates
- ✅ **Accessibility**: ARIA requirements mapped to implementation

### Constitution Compliance Summary

| Principle | Status | Evidence |
| --------- | ------ | -------- |
| I. Design-First, Verify Implementation | ✅ Pass | UI design complete (templates, layout), tests planned post-verification |
| II. Documentation-First | ✅ Pass | quickstart.md completed, usage patterns documented |
| III. Component Quality & Accessibility | ✅ Pass | ARIA attributes planned, keyboard navigation verified |
| IV. Compatibility & Config-Driven Design | ✅ Pass | Optional dependency, no breaking changes |
| V. Tooling & Consistency | ✅ Pass | Poetry managed, Ruff/djlint configured |
| VI. UI Verification | ✅ Pass | chrome-devtools-mcp verification planned |
| VII. Documentation Retrieval | ✅ Pass | Context7 used for django-tables2 docs |
| VIII. End-to-End Testing | ✅ Pass | Playwright tests planned for user workflows |

**Result**: ✅ **ALL PRINCIPLES SATISFIED**

---

## Next Steps

### Command to Run

```bash
/speckit.tasks
```

This will:

1. Generate `tasks.md` with implementation tasks
2. Provide task-by-task implementation guidance
3. Include test specifications for each task

### Expected Task Categories

**Package Configuration**:

- Update pyproject.toml with optional dependency
- Create/update CHANGELOG.md

**Data Layer**:

- No changes needed (uses existing Product model)
- Verify generate_dummy_data creates sufficient products

**View Layer**:

- Create ProductTable class
- Implement DataTablesView
- Add URL pattern

**Template Layer**:

- Create demo page template (fill mode)
- Create django-tables2 template overrides
- Add ARIA attributes and accessibility features

**Navigation**:

- Add Integrations menu group
- Add DataTables Demo menu item

**Testing**:

- Unit tests (model, table, view)
- Integration tests (URL routing, menu registration)
- E2E tests (sorting, pagination, fill mode, responsive)

**Documentation**:

- Add quickstart.md reference to main docs
- Update CHANGELOG.md
- Add demo page to README examples

---

## Planning Complete

**Phase 0**: ✅ Research finished ([research.md](research.md))
**Phase 1**: ✅ Design & Contracts finished ([data-model.md](data-model.md), [quickstart.md](quickstart.md))
**Constitution Check**: ✅ All principles satisfied
**Agent Context**: ✅ Updated with new technologies

**Ready for**: Phase 2 - Implementation Tasks (`/speckit.tasks`)
