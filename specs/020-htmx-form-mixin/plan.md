# Implementation Plan: HTMX Form Mixin

**Branch**: `020-htmx-form-mixin` | **Date**: 2026-05-28 | **Spec**: [specs/020-htmx-form-mixin/spec.md](spec.md)
**Input**: Feature specification from `specs/020-htmx-form-mixin/spec.md`

## Summary

A new `HtmxFormMixin` class that augments any of the package's existing form views (`MVPFormView`, `MVPCreateView`, `MVPUpdateView`, `MVPDeleteView`) with htmx progressive enhancement. On a valid htmx POST it returns a Cotton component partial (or an `HX-Redirect` header); on an invalid htmx POST it returns the form Cotton component at HTTP 200. Non-htmx requests are completely unmodified.

Detection uses `request.htmx` from `django-htmx`. Rendering uses `render_component()` from `django-cotton`. Client-side redirects use `HttpResponseClientRedirect`; triggers use `trigger_client_event()`. Django messages are drained via `get_messages()` on htmx success paths.

## Technical Context

**Language/Version**: Python 3.12 / 3.13
**Primary Dependencies**: Django 5.2+, `django-htmx>=1.0,<2.0` (new required dep), `django-cotton==2.6.1` (existing dep)
**Storage**: N/A — no model changes, no migrations
**Testing**: pytest + pytest-django (unit); pytest-playwright (browser htmx interactions)
**Target Platform**: Django web application (server-side)
**Project Type**: Reusable Django app — view mixin
**Performance Goals**: No additional database queries beyond the existing form view chain
**Constraints**: Zero regression on non-htmx paths; 100% branch coverage on mixin logic
**Scale/Scope**: One new Python file (~80–100 LOC), one test module, one demo view, two demo Cotton components

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Design-First, Verify Implementation | ✅ PASS | Spec + plan complete; playwright verification required for htmx browser interactions |
| II. Documentation-First | ✅ PASS | `quickstart.md` generated; docstrings + demo examples required in implementation |
| III. Component Quality & Accessibility | ✅ N/A | No new shared HTML components in the mixin; demo components follow Cotton conventions |
| IV. Compatibility & Config-Driven | ✅ PASS | Additive mixin; zero breaking changes to existing views |
| V. Tooling & Consistency | ✅ PASS | Poetry, Ruff, djlint; `django-htmx` added via `pyproject.toml` |
| VI. UI Verification (playwright-cli) | ✅ REQUIRED | htmx form submission, partial swap, inline errors, HX-Trigger, HX-Redirect MUST be verified in a real browser using the playwright-cli skill with behavior-level assertions tied to each user story's acceptance criteria |
| VII. Documentation Retrieval | ✅ PASS | django-htmx and django-cotton APIs fully researched; see `research.md` |
| VIII. E2E Testing — Simplicity Mandate | ✅ PASS | Unit tests cover all Python branching logic; playwright only for genuine browser-required behavior (htmx request lifecycle) |
| IX. Template Component Reuse | ✅ PASS | Demo components use Cotton conventions; no raw-HTML duplication |

**Post-design re-check**: Passes. No violations introduced by the Phase 1 design.

**Playwright mandate**: Tasks MUST include playwright verification for **each of the four user stories**. Assertions must be behavior-level — e.g. "partial replaces form container without page reload", "HX-Redirect navigates to the list page", "validation errors appear inline within the form partial", "no stale toast appears on subsequent navigation".

## Project Structure

### Documentation (this feature)

```text
specs/020-htmx-form-mixin/
├── plan.md              # This file
├── research.md          # Phase 0 — library API decisions (generated)
├── data-model.md        # Phase 1 — class interface contract (generated)
├── quickstart.md        # Phase 1 — developer usage guide (generated)
└── tasks.md             # Phase 2 — NOT created by /speckit.plan
```

No `contracts/` directory: the mixin is a Python class, not an external service interface.

### Source Code (repository root)

```text
mvp/
└── views/
    ├── edit.py                      # unchanged — existing form view base classes
    ├── htmx.py                      # NEW — HtmxFormMixin class
    └── __init__.py                  # updated — export HtmxFormMixin

tests/
└── test_views/
    ├── test_edit_view.py            # unchanged — existing edit view tests
    └── test_htmx_form_mixin.py     # NEW — unit tests for HtmxFormMixin

demo/
├── views.py                         # updated — add htmx demo view
├── urls.py                          # updated — register demo URL
├── menus.py                         # updated — add sidebar entry
└── templates/
    └── cotton/
        └── demo/
            ├── htmx-product-form.html     # NEW — form-error partial demo component
            └── htmx-product-created.html  # NEW — success partial demo component

pyproject.toml                       # updated — add django-htmx dependency
```

**Structure Decision**: Single Django app layout. New source file `mvp/views/htmx.py` isolates the `django-htmx` dependency and keeps `edit.py` clean. No new Django app or package is required.

## Complexity Tracking

No constitution violations — table omitted.
