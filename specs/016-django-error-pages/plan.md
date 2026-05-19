# Implementation Plan: Django Error Pages

**Branch**: `feature/016-django-error-pages` | **Date**: 2026-05-19 | **Spec**: [spec.md](spec.md)
**Propagated**: 2026-05-19 — Updated from spec.md refinement (logo added, error code display removed, block names simplified)

## Summary

Provide four production-ready, consistently styled Django error pages (400, 403, 404,
500) for the `django-mvp` package. Each page extends a shared `mvp/error_base.html`
scaffold that renders a full-viewport centered layout with the application logo,
without sidebar or DB queries. Numeric HTTP status codes are not displayed on-page;
they are communicated via response headers and page `<title>` only. Custom view
functions in `mvp/views/error.py` are registered as Django error handlers in
`demo/urls.py`. The 500 page optionally surfaces a support contact link sourced from
`settings.DEFAULT_FROM_EMAIL`. Four demo preview routes allow developers to inspect
the pages without triggering real errors.

## Technical Context

**Language/Version**: Python >=3.11, Django >=4.2,<6.0
**Primary Dependencies**: Django (error view mechanism), Bootstrap 5 + AdminLTE 4
  (CSS), django-cotton + django-cotton-bs5 (`<c-button>` component), django-flex-menu
  (sidebar, not rendered on error pages)
**Storage**: N/A — no database queries in any error view (FR-015)
**Testing**: pytest, pytest-django, pytest-playwright (E2E); djlint (template lint);
  Ruff (Python lint/format)
**Target Platform**: Django WSGI web application, served from any WSGI-compatible host
**Project Type**: Django reusable app (`mvp/`) + demo integration app (`demo/`)
**Performance Goals**: <1 second render per error page (SC-002); no DB queries
**Constraints**: No DB access in error views; WCAG 2.1 AA; `DEBUG=False` compatible;
  static asset delivery only
**Scale/Scope**: 4 templates + 1 base template update + 1 new view module + demo
  integration (views, URLs, sidebar menu)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Design-First, Verify Implementation | ✅ PASS | Playwright MCP verification required in all UI phases; pytest + pytest-playwright for all behaviour changes |
| II | Documentation-First | ✅ PASS | Template block API documented in `contracts/template-block-api.md`; quickstart in `quickstart.md`; skill update required |
| III | Component Quality & Accessibility | ✅ PASS | WCAG 2.1 AA (SC-005); semantic `<h1>` required; `<c-button>` from django-cotton-bs5 |
| IV | Cotton-Only UI Config | ✅ PASS | No Python-level layout config; all styling via template blocks and Cotton components |
| V | Tooling & Consistency | ✅ PASS | Poetry, Ruff, djlint must pass; enforced at CI |
| VI | UI Verification (playwright-mcp) | ✅ PASS | Each template phase includes a Playwright MCP verification task |
| VII | Documentation Retrieval (context7) | ✅ PASS | Implementer must consult context7 for Django error view API and django-cotton-bs5 before implementing |
| VIII | E2E Testing (pytest-playwright) | ✅ PASS | E2E tests for all four error pages required |
| IX | Template Component Reuse | ✅ PASS | `<c-button>` (django-cotton-bs5) used in all action blocks; prebuilt component mandate satisfied |
| X | django-mvp Skill Currency | ⚠ REQUIRED ACTION | `skills/django-mvp/SKILL.md` must be updated with error template block API and handler registration pattern when implementation is complete |
| XI | Dual-Audience User Stories | ✅ PASS (fixed) | Spec updated: US1-4 labeled `[End User]`, US5 labeled `[Developer]` |
| XII | View Class Docstring Completeness | ✅ N/A | Error handlers are simple functions, not classes; no docstring gate applies |

**Post-Design Re-check**: Constitution Check re-evaluated after Phase 1 design. All
gates pass. No violations remain.

## Project Structure

### Documentation (this feature)

```text
specs/016-django-error-pages/
├── plan.md                        # This file
├── research.md                    # Phase 0: Django error handler API, context safety
├── data-model.md                  # Phase 1: No DB models; template context shapes
├── quickstart.md                  # Phase 1: Developer integration guide
├── contracts/
│   └── template-block-api.md      # Phase 1: Block API + view function contract
└── tasks.md                       # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code

```text
mvp/
├── templates/
│   ├── 400.html                   # NEW: Bad Request page
│   ├── 403.html                   # NEW: Forbidden page
│   ├── 404.html                   # UPDATE: complete existing stub
│   ├── 500.html                   # UPDATE: fix copy + conditional support email
│   └── mvp/
│       └── error_base.html        # UPDATE: minor hardening (verify blocks are complete)
├── views/
│   ├── __init__.py                # UPDATE: export error handler functions
│   └── error.py                   # NEW: bad_request, permission_denied, not_found, server_error

demo/
├── menus.py                       # UPDATE: add "Error Pages" MenuGroup
├── urls.py                        # UPDATE: register handler400/403/404/500
└── views.py                       # UPDATE: add ErrorPagePreviewView for each code

tests/
├── test_views/
│   ├── test_error_views.py        # NEW: unit tests for error view functions
│   └── test_error_views_e2e.py    # NEW: pytest-playwright E2E tests

skills/
└── django-mvp/
    └── SKILL.md                   # UPDATE: add error page block API + handler registration
```

**Structure Decision**: Django web application (single repo, `mvp/` package + `demo/`
integration app). No frontend/backend split. Tests mirror source tree per Principle I.

## Complexity Tracking

No constitution violations requiring justification.
