# Implementation Plan: MVPCreateView — Zero-Config Model Create View

**Branch**: `011-mvp-create-view` | **Date**: 2026-05-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/011-mvp-create-view/spec.md`

## Summary

`MVPCreateView` is the package's concrete model create view — intended to be
immediately usable with only `model` and `fields` set. The existing stub already has
the correct icon, CSS class, and success message template, but ships a static
`page_title = _("Create Entry")` that is model-agnostic. Two targeted additions are
required:

1. **FR-001** — `MVPCreateView.get_page_title()`: interpolate the class-level
   `page_title` template (`_("Create %(verbose_name)s")`) with
   `self.model_meta.verbose_name.title()`, producing "Create Product",
   "Create Order Line", etc. Falsy `page_title` overrides (None/False/"") are
   returned as-is.

2. **FR-004** — `MVPCreateView.get_success_message()`: inject a title-cased
   `verbose_name` so the default flash reads "Product successfully created." (not
   "product successfully created.").

Research confirmed that breadcrumb degradation (FR-006) is already handled by the
base class (`PageObjectMixin`) through the `django-cotton-bs5` breadcrumbs component's
`href|yesno:"a,span"` filter — no `get_breadcrumbs()` override is needed. Three
existing tests in `TestGetSuccessMessage` must be relocated to a `MVPUpdateView`-based
test vehicle to decouple `MVPModelFormBase` behaviour from the new
`MVPCreateView`-specific override.

## Technical Context

**Language/Version**: Python 3.10–3.13, Django 4.2–5.x
**Primary Dependencies**: Django (`SuccessMessageMixin`, `generic.CreateView`), `collections.defaultdict`
**Storage**: N/A
**Testing**: pytest, pytest-django, pytest-playwright (E2E)
**Target Platform**: Reusable Django app
**Project Type**: Library
**Performance Goals**: N/A
**Constraints**: Backward-compatible; must not alter `MVPUpdateView`, `MVPDeleteView`, `MVPFormView`, or any base mixin class
**Scale/Scope**: One class, two new methods, one file (`mvp/views/edit.py`); relocate 3 tests, add ~11 new tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status | Notes |
|-----------|------|--------|-------|
| I. Design-First | Tests written before implementation | ✅ PASS | Test-first mandated in tasks; failing tests observed before code change |
| I. Story-Level Validation | `manage.py check` + `pytest tests/test_views/` after each phase | ✅ PASS | Included in task plan |
| II. Documentation-First | Docstrings on both new methods; `quickstart.md` updated | ✅ PASS | Both methods get full docstrings; quickstart in this plan |
| III. Component Quality | N/A — no template or Cotton component changes | ✅ PASS | Pure Python change |
| IV. Compatibility | No breaking changes to `MVPModelFormBase`, `MVPUpdateView`, `MVPDeleteView`, `MVPFormView`, or any base mixin | ✅ PASS | Changes isolated to `MVPCreateView` only |
| IV. Cotton-Only UI | N/A — no UI configuration in this feature | ✅ PASS | |
| V. Tooling | Poetry, Ruff, pytest | ✅ PASS | |
| VI. UI Verification | E2E Playwright tasks for full create round-trip | ✅ PASS | Playwright E2E tasks included in plan |
| VII. Documentation Retrieval | Django `CreateView`, `verbose_name`, and `defaultdict` APIs confirmed from existing codebase | ✅ PASS | No external library changes |
| VIII. E2E Testing | Playwright E2E tests for title, message, and redirect | ✅ PASS | Tests added to `test_edit_view_e2e.py` |
| IX. Template Component Reuse | N/A — no template modifications | ✅ PASS | |
| X. django-mvp Skill Currency | `skills/django-mvp/SKILL.md` must be updated if `MVPCreateView` is public API | ✅ PASS | Skill update task included |
| XI. Dual-Audience Stories | Developer story (zero-config view) + end-user story (sees correct title/message) | ✅ PASS | Both audiences present in spec |

**Constitution Check Result: ALL GATES PASS**

**Post-Phase 1 re-check**: Research confirmed no template changes needed. Constitution check unchanged.

## Project Structure

### Documentation (this feature)

```text
specs/011-mvp-create-view/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks — not created by /speckit.plan)
```

### Source Code (repository root)

```text
mvp/
└── views/
    └── edit.py          # MVPCreateView — replace static page_title with translatable interpolation template; add get_page_title() and get_success_message()

tests/
└── test_views/
    ├── test_edit_view.py    # Relocate 3 TestGetSuccessMessage tests; add TestMVPCreateViewPageTitle,
    │                        # TestMVPCreateViewSuccessMessage, TestMVPCreateViewDefaults
    └── test_edit_view_e2e.py  # Add TestMVPCreateViewE2E (2–3 Playwright tests)

skills/
└── django-mvp/
    └── SKILL.md         # Update MVPCreateView entry to document auto-derived title and success message
```

**Structure Decision**: Single-file change to `mvp/views/edit.py` only. Tests appended
to existing files. No new files required in the source tree.

## Complexity Tracking

> **No constitution violations.** No complexity justification required.
