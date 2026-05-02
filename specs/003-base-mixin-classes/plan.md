# Implementation Plan: Document and Test Core View Mixins

**Branch**: `003-base-mixin-classes` | **Date**: 2026-05-02 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-base-mixin-classes/spec.md`

## Summary

Add Google-style docstrings, type annotations, and comprehensive pytest coverage to `BaseTemplateNameMixin` and `PageMixin` in `mvp/views/base.py`. Also applies two small behaviour improvements agreed during clarification: (1) `base_template_name` defaults to `None` and raises `ImproperlyConfigured` when unset (mirrors Django's `TemplateResponseMixin`); (2) `breadcrumbs = []` class attribute is added to `PageMixin` and `get_breadcrumbs()` returns `self.breadcrumbs`, consistent with the other page-attribute getter pattern.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: Django 4.2–5.x, pytest, pytest-django
**Storage**: N/A (no database models)
**Testing**: pytest + pytest-django; Google-style docstrings; 100% line + branch coverage target
**Target Platform**: Django reusable app (Python package)
**Project Type**: Single Django app library
**Performance Goals**: All new tests complete in < 2 seconds total
**Constraints**: No breaking changes to existing subclass behaviour (all concrete subclasses already set `base_template_name`); Python 3.10+ compatibility
**Scale/Scope**: 2 mixin classes, ~10 methods total; 1 new test file

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Design-first approach is feasible and planned (behaviour changes implemented, then verified, then tests written)
- [~] Visual verification approach is planned — **EXEMPTED**: no UI changes; all changes are pure Python
- [x] Test types are identified: pytest + pytest-django for new `tests/test_views/test_base.py`
- [x] Documentation updates included: Google-style docstrings on all public methods; `skills/django-mvp/SKILL.md` update planned (breadcrumbs API addition)
- [x] Quality gates understood: tests + ruff lint/format + `python manage.py check`
- [~] Documentation retrieval planned (context7) — **N/A**: only standard Django CBV patterns used; no third-party library API lookups needed
- [~] End-to-end testing planned (pytest-playwright) — **EXEMPTED**: feature is pure Python library code with no browser UI
- [x] Tasks are grouped by user story
- [x] Every phase touching Django code includes `python manage.py check` validation task
- [~] Every phase touching UI includes Playwright MCP server verification — **N/A**: no UI changes
- [~] UI configuration uses Cotton components and template overrides only — **N/A**: no UI changes
- [~] Template work considered prebuilt django-cotton-bs5 components first — **N/A**: no template work
- [~] Custom Cotton components used instead of `{% include %}` partials — **N/A**: no template work
- [~] django-cotton-bs5 skill and django-cotton skill consulted — **N/A**: no template work
- [~] cotton-test-components skill consulted — **N/A**: no Cotton component tests
- [~] Cotton component tests planned under `tests/test_components/` — **N/A**: no Cotton components
- [~] Single-file top-level cotton components grouped — **N/A**: no Cotton components
- [x] Feature touches public API (`breadcrumbs` attr addition + `base_template_name` default change) → `skills/django-mvp/SKILL.md` update is planned
- [x] `skills/django-mvp/SKILL.md` referenced only for API change notification, not for core mvp/ development
- [!] **Principle XI VIOLATION — Justified**: spec has no [End User] story. This feature documents and tests internal framework mixins; end users never interact with `BaseTemplateNameMixin` or `PageMixin` directly. The only audience is developers. Exemption is justified.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Principle XI: no End User story | Feature is purely internal framework architecture; end users have no direct interaction with view mixins | Any fabricated end-user story would be fictional and misleading |

## Project Structure

### Documentation (this feature)

```text
specs/003-base-mixin-classes/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
mvp/
└── views/
    └── base.py          # MODIFY: docstrings, base_template_name=None, breadcrumbs attr

tests/
└── test_views/
    └── test_base.py     # CREATE: comprehensive tests for both mixins

skills/
└── django-mvp/
    └── SKILL.md         # UPDATE: document breadcrumbs attribute addition
```

**Structure Decision**: Single-project layout. All changes are confined to `mvp/views/base.py` (source) and `tests/test_views/test_base.py` (tests), mirroring the established project source tree convention.
