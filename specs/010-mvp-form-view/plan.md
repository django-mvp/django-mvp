# Implementation Plan: MVPFormView — Non-Model Form View

**Branch**: `010-mvp-form-view` | **Date**: 2026-05-04 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/010-mvp-form-view/spec.md`

## Summary

`MVPFormView` is the package's concrete non-model form view — a complete, immediately
usable view for contact forms, settings pages, search forms, and wizard steps that have
no backing database model.

Research confirms that 8 of 10 functional requirements are **already satisfied** by the
existing minimal stub (`class MVPFormView(MVPFormBase, generic.FormView): page_class = "mvp-form-page"`),
through inheritance from `MVPFormBase`, `generic.FormView`, `SuccessMessageMixin`,
`NextURLMixin`, and `PageMixin`. Two targeted additions to the stub class are required:

1. **FR-005** — `MVPFormView.get_success_message()`: override with
   `defaultdict(str, cleaned_data)` so that unknown placeholders (e.g.
   `%(verbose_name)s`) silently substitute `""` instead of raising `KeyError`.
   Unlike `MVPModelFormBase`, `verbose_name` must NOT be injected.

2. **FR-008** — `MVPFormView.get_page_title()`: override to return
   `camel_case_to_spaces(self.__class__.__name__).title()` when `page_title`
   is not set, giving a readable zero-config default (e.g. `ContactFormView`
   → `"Contact Form View"`).

Seven existing tests cover the inherited redirect chain, layout template, and
`ImproperlyConfigured` behaviour. Five new unit tests are required for the two
new methods: 3 in task T004 (`get_success_message()`) and 2 in task T008 (`get_page_title()`).

## Technical Context

**Language/Version**: Python 3.10–3.12, Django 4.2–5.x
**Primary Dependencies**: Django (`SuccessMessageMixin`, `FormMixin`, `generic.FormView`), `collections.defaultdict`, `django.utils.text.camel_case_to_spaces`
**Storage**: N/A
**Testing**: pytest, pytest-django
**Target Platform**: Reusable Django app
**Project Type**: Library
**Performance Goals**: N/A
**Constraints**: Backward-compatible; must not alter existing `MVPFormBase` or `MVPModelFormBase` behaviour
**Scale/Scope**: One class, two new methods, one file (`mvp/views/edit.py`), five new tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status | Notes |
|-----------|------|--------|-------|
| I. Design-First | Tests written before implementation | ✅ PASS | Test-first mandated in tasks; no UI to verify visually |
| I. Story-Level Validation | `manage.py check` + `pytest tests/test_views/` after each phase | ✅ PASS | Included in task plan |
| II. Documentation-First | Docstrings on both new methods | ✅ PASS | Both methods get full docstrings |
| III. Component Quality | N/A — no templates or Cotton components modified | ✅ PASS | Pure Python change |
| IV. Compatibility | No breaking changes; `MVPFormBase` and `MVPModelFormBase` untouched | ✅ PASS | `defaultdict(str)` is backward-compatible |
| IV. Cotton-Only UI | N/A — no UI configuration in this feature | ✅ PASS | |
| V. Tooling | Poetry, Ruff, pytest | ✅ PASS | |
| VI. UI Verification | N/A — no HTML/template changes | ✅ PASS | |
| VII. Documentation Retrieval | Standard Django patterns; APIs confirmed from existing codebase | ✅ PASS | |
| VIII. E2E Testing | No new user workflows; existing E2E tests cover the happy path | ✅ PASS | |
| IX. Template Component Reuse | N/A — no templates modified | ✅ PASS | |

**Constitution Check Result: ALL GATES PASS**

## Project Structure

### Documentation (this feature)

```text
specs/010-mvp-form-view/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks — not created by /speckit.plan)
```

### Source Code (repository root)

```text
mvp/
└── views/
    └── edit.py          # MVPFormView — add get_success_message() and get_page_title()

tests/
└── test_views/
    └── test_edit_view.py  # 5 new unit tests appended to TestMVPFormBase or new class
```

**Structure Decision**: Single-file change — `mvp/views/edit.py` only. Tests appended
to the existing `tests/test_views/test_edit_view.py` in a new class `TestMVPFormView`.
No new files needed.
