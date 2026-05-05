# Implementation Plan: MVPUpdateView — Zero-Config Model Update View

**Branch**: `012-mvp-update-view` | **Date**: 2026-05-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/012-mvp-update-view/spec.md`

## Summary

`MVPUpdateView` is the package's concrete model update view. The existing stub
already carries `get_breadcrumbs()`, `get_delete_url()`, and `get_context_data()`
but has two implementation gaps and a Principle XII docstring deficiency:

1. **FR-001** — `page_title` is the static string `_("Update Entry")`. Replace
   with the interpolation template `_("Update %(verbose_name)s")`.
   `MVPModelFormBase.get_page_title()` already handles runtime interpolation;
   no new method override is required.

2. **FR-005** — `get_breadcrumbs()` builds the middle breadcrumb link via
   `self.object.get_absolute_url()` directly. Replace with
   `self.resolve_crud_url("detail")` so the permissions system
   (`CRUDDirectoryMixin`) gates the link, and graceful degradation to plain
   text is handled automatically by the `href|yesno:"a,span"` filter.

3. **FR-009** — `form_view.html` gates the Delete button on `{% if object %}`.
   For an update view, `object` is always set, so the button always renders —
   even when `delete_url` is an empty string (no delete view registered).
   Replace the guard with `{% if delete_url %}` to correctly hide the button
   when `get_delete_url()` returns `""`.

4. **FR-014** — The class docstring is a single line. Replace with a
   Principle XII-compliant docstring: intended-use summary, `Config:` block,
   `Override hooks:` subsection, and minimal usage example.

Research also confirmed `"detail"` is a valid key in `MVP_DEFAULT_VIEW_NAMES`,
so `resolve_crud_url("detail")` is safe to call without a `ValueError`.

Research Finding 7 (post-analysis addition) confirms that `get_delete_url()` already
correctly integrates with `CRUDDirectoryMixin` by calling `resolve_crud_url("delete")`
first. Replacing it with `get_directory()` is not viable: `get_directory()` returns
plain URLs and cannot append the `?back`/`?next` query parameters that are a core
UX requirement (US3). The raw `reverse()` call for `back_url` inside `get_delete_url()`
is intentional — using `resolve_crud_url("update")` would silently gate on
`has_update_permission` (which defaults to `False`), producing a `None` back URL
for developers who have not explicitly set that attribute. Only improvement: wrap
the `reverse()` call in `try/except` (T023).

## Technical Context

**Language/Version**: Python 3.10–3.13, Django 4.2–5.x
**Primary Dependencies**: Django (`generic.UpdateView`), `django-cotton-bs5` (breadcrumbs component)
**Storage**: N/A
**Testing**: pytest, pytest-django, pytest-playwright (E2E)
**Target Platform**: Reusable Django app
**Project Type**: Library
**Performance Goals**: N/A
**Constraints**: Backward-compatible; must not alter `MVPCreateView`, `MVPDeleteView`, `MVPFormView`, or any base mixin class
**Scale/Scope**: Two attribute/one-liner changes + one-line template fix in two files; class docstring rewrite; ~12–15 new tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status | Notes |
|-----------|------|--------|-------|
| I. Design-First | Tests written before implementation | ✅ PASS | Test-first mandated in tasks; failing tests observed before code change |
| I. Story-Level Validation | `manage.py check` + `pytest tests/test_views/` after each phase | ✅ PASS | Explicit validation tasks in plan |
| II. Documentation-First | Principle XII docstring on `MVPUpdateView`; `quickstart.md`; skill update | ✅ PASS | FR-014 mandates docstring; quickstart in Phase 1 |
| III. Component Quality | Template guard change: `{% if object %}` → `{% if delete_url %}` | ✅ PASS | One-line template change; no markup structure change |
| IV. Compatibility | No breaking changes to any other class | ✅ PASS | Changes isolated to `MVPUpdateView` + `form_view.html` guard |
| IV. Cotton-Only UI | Template guard is a Django template conditional, not Python config | ✅ PASS | |
| V. Tooling | Poetry, Ruff, pytest | ✅ PASS | |
| VI. UI Verification | Playwright MCP verification of delete-link show/hide and breadcrumb depth | ✅ PASS | Playwright MCP tasks included in plan |
| VII. Documentation Retrieval | All APIs (`resolve_crud_url`, `get_page_title`, `MVP_DEFAULT_VIEW_NAMES`) confirmed from source | ✅ PASS | No external library changes |
| VIII. E2E Testing | pytest-playwright E2E for title, breadcrumb, success message, delete link | ✅ PASS | Tests in `test_edit_view_e2e.py` |
| IX. Template Component Reuse | `form_view.html` uses existing Cotton components; no new markup | ✅ PASS | Guard change only — no new components needed |
| X. django-mvp Skill Currency | `skills/django-mvp/SKILL.md` must reflect updated `MVPUpdateView` API | ✅ PASS | Skill update task included |
| XI. Dual-Audience Stories | Developer stories (US1–US5) + end-user story (US6) | ✅ PASS | Both audiences present in spec |
| XII. View Class Docstring Completeness | `MVPUpdateView` docstring must have Config/Override hooks/example | ✅ PASS | FR-014 mandates replacement; task included |

**Constitution Check Result: ALL GATES PASS**

**Post-Phase 1 re-check**: Research confirmed no new classes, no new Cotton
components, and no migration needed. Constitution check unchanged.

## Phase 0: Research

### Findings

| Question | Finding | Decision |
|----------|---------|----------|
| Is `"detail"` a valid key for `resolve_crud_url()`? | `MVP_DEFAULT_VIEW_NAMES` in `config.py` includes `"detail"` | Safe — no `ValueError` risk |
| Does the template already gate the Delete button on `delete_url`? | `form_view.html` line 51 gates on `{% if object %}`, not `{% if delete_url %}` | Template fix required (FR-009) |
| Does breadcrumb degradation need Python changes? | `href|yesno:"a,span"` in Cotton breadcrumbs component handles `None`/empty`href` automatically | No Python guard needed in `get_breadcrumbs()` |
| Does `MVPModelFormBase.get_page_title()` handle `%(verbose_name)s` interpolation? | Yes — confirmed at `mvp/views/edit.py`; interpolates with `model_meta.verbose_name.title()` | No override needed on `MVPUpdateView` |
| Do `TestMVPUpdateViewDeleteUrl` tests already exist? | Yes — 3 tests in `test_delete_view.py` cover US3's `?back`/`?next` params | Do not duplicate; add breadcrumb and title tests only |
| Does `make_update_view()` fixture helper already exist? | Yes — in `test_edit_view.py` | Reuse directly |
| Should `get_delete_url()` be replaced by `CRUDDirectoryMixin.get_directory()`? | `get_delete_url()` already calls `resolve_crud_url("delete")` — permission integration is correct. `get_directory()` produces plain URLs and cannot append `?back`/`?next` params. Raw `reverse()` for `back_url` is intentional (must not gate on `has_update_permission`). | No change to `get_delete_url()` structure. Only improvement: add `try/except` around `reverse()` for `back_url` (T023) |

## Project Structure

### Documentation (this feature)

```text
specs/012-mvp-update-view/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output (findings above)
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks — not created by /speckit.plan)
```

### Source Code (repository root)

```text
mvp/
├── views/
│   └── edit.py                # MVPUpdateView — 3 targeted changes (see Summary)
└── templates/
    └── form_view.html         # 1-line guard change: {% if object %} → {% if delete_url %}

tests/
└── test_views/
    ├── test_edit_view.py      # Add TestMVPUpdateViewPageTitle, TestMVPUpdateViewBreadcrumb,
    │                          # TestMVPUpdateViewDefaults (no delete-URL tests — already in test_delete_view.py)
    └── test_edit_view_e2e.py  # Add TestMVPUpdateViewE2E (3–4 Playwright tests)

skills/
└── django-mvp/
    └── SKILL.md               # Update MVPUpdateView entry: model-aware title, breadcrumb depth,
                               # delete link visibility
```

**Structure Decision**: Two file changes in the `mvp/` package, tests appended to
existing files. No new source files. No new Cotton components.

## Phase 1: Design

### Data Model

No new models, fields, or migrations. `MVPUpdateView` operates on the developer's
model instance; the only Django model interaction is the existing `generic.UpdateView`
save path.

Key entities (unchanged from spec):

- **MVPUpdateView** — concrete view class; changes confined to three lines of Python
  - one line of HTML
- **Object** — the model instance being edited; surfaced in breadcrumb via `str(object)`
  and linked via `resolve_crud_url("detail")`
- **Delete URL** — empty string when no delete view is accessible; non-empty string
  otherwise; controls Delete button visibility via the updated template guard

### Interface Contracts

No public API changes. `MVPUpdateView` gains a richer docstring but its public
interface (attributes, methods, template variables) is unchanged. The template
guard change (`{% if object %}` → `{% if delete_url %}`) is a behaviour fix, not
an interface change — any consumer that has no delete view configured now correctly
sees no button, which is the documented contract.

The `delete_url` context variable was always the intended gate; the `{% if object %}`
guard was a pre-existing bug.

### Quickstart

See [quickstart.md](quickstart.md).

## Complexity Tracking

> **No constitution violations.** No complexity justification required.

[Gates determined based on constitution file]

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
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
