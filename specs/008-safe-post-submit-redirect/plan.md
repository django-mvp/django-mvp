# Implementation Plan: Safe Post-Submit Redirect

**Branch**: `008-safe-post-submit-redirect` | **Date**: 2026-05-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/008-safe-post-submit-redirect/spec.md`
**Propagated**: 2026-05-04 — Updated from spec.md refinement (FR-001a: `get_next_candidate()` override point)

## Summary

`NextURLMixin` in `mvp/views/edit.py` already implements same-origin URL validation and basic context injection. This feature completes the implementation to meet all spec requirements: adding DEBUG-level logging for rejected `next` values (FR-005b), fixing `next_url` context retention for CRUD shorthands on failed POST re-render (FR-012), extending shorthand resolution to `MVPFormView` (FR-006 Q2 clarification), inserting `success_url` as a priority step before the built-in list-URL fallback (FR-009), and adding a comprehensive test file for all five user stories.

The approach is gap-filling: existing code is preserved where it already satisfies a requirement; only the four identified gaps receive targeted changes.

## Technical Context

**Language/Version**: Python 3.10–3.12 (target-version = py311 per pyproject.toml)
**Primary Dependencies**: Django ≥4.2,<6.0; `django.utils.http.url_has_allowed_host_and_scheme`; Python `logging` stdlib
**Storage**: N/A — no new models or migrations
**Testing**: pytest + pytest-django (via `fairdm-dev-tools[test]`); pytest-playwright for E2E
**Target Platform**: Any WSGI/ASGI Django deployment
**Project Type**: Reusable Django app (single package)
**Performance Goals**: No measurable performance impact; `url_has_allowed_host_and_scheme` is O(1)
**Constraints**: No new public API that breaks existing behaviour; logging must not emit in production unless `DEBUG=True`
**Scale/Scope**: Changes confined to `mvp/views/edit.py` (~10–20 LOC); new test file `tests/test_views/test_edit_view.py`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- ✅ Design-first approach is feasible and planned — gaps identified from spec vs. existing code; targeted changes designed before tests are written
- ✅ Visual verification approach is planned — no UI changes in this feature; Playwright E2E confirms redirect behaviour in a real browser
- ✅ Test types are identified — pytest + pytest-django for unit/integration; pytest-playwright for E2E redirect flows
- ✅ Documentation updates are included — `NextURLMixin` docstring, `get_success_url` docstrings, and quickstart.md
- ✅ Quality gates are understood — `python manage.py check` + `pytest tests/test_views/test_edit_view.py` after each phase
- ✅ Documentation retrieval is planned — `url_has_allowed_host_and_scheme` Django docs consulted in Phase 0 research
- ✅ End-to-end testing is planned — pytest-playwright covers "create with ?next=list → redirects to list" flow
- ✅ Tasks are grouped by user story — each of the 5 stories has a discrete implementation + test block
- ✅ Every phase touching Django code includes `python manage.py check` validation task
- ✅ Every phase touching UI includes a Playwright MCP server verification task — E2E phase covers redirect and re-render
- ✅ UI configuration uses Cotton components and template overrides only — no Python-level UI config
- ✅ Template work considered prebuilt django-cotton-bs5 components first — no template changes in this feature
- ✅ Custom Cotton components used instead of `{% include %}` partials — N/A, no new components
- ✅ django-cotton-bs5 skill and django-cotton skill consulted before authoring new templates — N/A
- ✅ cotton-test-components skill consulted for any custom Cotton component tests — N/A, no new Cotton components
- ✅ Cotton component tests are planned under `tests/test_components/` — N/A
- ✅ Single-file top-level cotton components in one shared top-level module — N/A
- ✅ If this feature touches the public API, skills/django-mvp/SKILL.md update is planned — `NextURLMixin` is part of the public surface; SKILL.md update included in Phase 1
- ✅ skills/django-mvp/SKILL.md is only referenced for example-app work, not core mvp/ development
- ✅ Spec includes at least one [Developer] story and one [End User] story — US1–US4 are Developer, US2 is End User

## Project Structure

### Documentation (this feature)

```text
specs/008-safe-post-submit-redirect/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── next-url-mixin.md  # Phase 1 output — public API contract
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created here)
```

### Source Code (repository root)

```text
mvp/
└── views/
    └── edit.py          # ALL changes — NextURLMixin + MVPFormBase + MVPModelFormBase

tests/
└── test_views/
    └── test_edit_view.py  # NEW — all unit + integration tests for this feature
```

**Structure Decision**: Single targeted file edit. The existing `mvp/views/edit.py` contains all affected classes (`NextURLMixin`, `MVPFormBase`, `MVPModelFormBase`). No new modules needed. Test file mirrors the source tree per Constitution Principle I.

## Complexity Tracking

> No Constitution violations.

---

## Phase 0: Research

**Status**: ✅ Complete — see [research.md](research.md)

### Findings summary

| Item | Decision |
|------|----------|
| URL validation function | `url_has_allowed_host_and_scheme` — already in use; handles empty string, protocol-relative, unsafe schemes |
| Debug logging | `logging.getLogger(__name__)` + `logger.warning(...)` guarded by `settings.DEBUG` |
| FormMixin.get_success_url() in MRO | Returns `self.success_url`; raises `ImproperlyConfigured` when absent — wrap in `try/except` |
| next_url context for CRUD shorthands | Preserve raw shorthand in context when `get_next_url()` returns None and raw value is in `crud_views` |
| Shorthand scope for MVPFormView | Add `get_success_url()` to `MVPFormBase` with `hasattr(self, 'crud_views')` guard |

### Gaps resolved

1. **FR-005b** — Add `logger.warning` when `next` candidate is rejected and `DEBUG=True`
2. **FR-006** — Add `get_success_url()` to `MVPFormBase`; shorthand resolution guarded by `hasattr(self, 'crud_views')`
3. **FR-009** — Insert `super().get_success_url()` (step 3) before `resoluve_crud_url("list")` fallback; wrapped in `try/except ImproperlyConfigured`
4. **FR-012** — Preserve CRUD shorthand in `get_context_data()` when `get_next_url()` returns None
5. **FR-001a** — Add `get_next_candidate()` to `NextURLMixin` as a single override point for request reading; refactor all inline `request.POST/GET.get("next")` calls across `get_next_url()`, `get_context_data()`, and `get_success_url()` to use it

---

## Phase 1: Design

**Status**: ✅ Complete

### Artifacts

- [data-model.md](data-model.md) — Class hierarchy, `next_url` state machine, priority chain, method change table
- [contracts/next-url-mixin.md](contracts/next-url-mixin.md) — Public API contract for `NextURLMixin`, `get_context_data`, `get_success_url`
- [quickstart.md](quickstart.md) — Developer guide: basic usage, CRUD shorthands, template hidden field, success URL priority, debug logging, non-model form views

### Post-design Constitution Check

All 20 constitution principles re-evaluated after Phase 1 design:

- ✅ No new complexity added beyond the 4 targeted gap-fixes
- ✅ No new models, migrations, Cotton components, or templates
- ✅ All changes confined to `mvp/views/edit.py` (~15 LOC net)
- ✅ `skills/django-mvp/SKILL.md` update planned in implementation phase (US3)
- ✅ E2E test plan documented in contracts — no changes required to post-design check

---

## Ready for Phase 2

Run `/speckit.tasks` to generate `tasks.md` with actionable, dependency-ordered tasks for implementation.
