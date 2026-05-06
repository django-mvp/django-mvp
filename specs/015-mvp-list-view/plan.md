# Implementation Plan: MVPListView — Item Templates and Composed List Page

**Branch**: `015-mvp-list-view` | **Date**: 2026-05-06 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `specs/015-mvp-list-view/spec.md`

## Summary

`MVPListViewMixin` and `MVPListView` already have most of the required infrastructure
in place from earlier specs. This feature closes three open stubs and adds the
Constitution-XII-compliant docstrings that are currently missing:

1. **`get_page_title()` stub**: currently returns `None` (`pass`). Must return
   `page_title` attribute when set; fall back to `model._meta.verbose_name_plural.title()`.
2. **`directory` attribute not set**: `MVPListViewMixin` inherits `directory = []`
   from `CRUDDirectoryMixin`. Must be set to `["create"]` to limit CRUD URL injection
   to the create action only.
3. **`MVPListView` missing `paginate_by`**: Must declare `paginate_by = 24` (grid-friendly
   default, divisible by 1, 2, 3, and 4).
4. **Docstrings**: `MVPListViewMixin` and `MVPListView` need Constitution-XII compliant
   class docstrings with `Config:`, `Override hooks:`, and usage examples.
5. **Tests**: `tests/test_views/test_list_view.py` needs new test cases for all five
   items above (the existing file covers only `SearchMixin`/`OrderMixin`/`SearchOrderMixin`).
6. **Skill update**: `skills/django-mvp/SKILL.md` needs an `MVPListView` entry documenting
   the full developer-facing API.

No new models, migrations, templates, Cotton components, or URL patterns are required.

## Technical Context

**Language/Version**: Python 3.12, Django 5.x  
**Primary Dependencies**: django-mvp (internal), Django's `ListView`  
**Storage**: N/A — no new models or migrations  
**Testing**: pytest, pytest-django, factory-boy  
**Target Platform**: Django web application (server-rendered), reusable library  
**Project Type**: Reusable Django library  
**Performance Goals**: No queryset overhead from `directory = ["create"]` when
`has_create_permission` is falsy — `CRUDDirectoryMixin.get_directory()` already
short-circuits on permission checks.  
**Constraints**: `paginate_by = 24` default must not affect `MVPListViewMixin` itself
(only `MVPListView`), preserving full control for custom base class compositions.  
**Scale/Scope**: Three stub fixes + docstrings in one file; test additions to one
existing test file; one skill doc update.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Gate | Status | Notes |
|---|---|---|---|
| I. Design-First, Verify Implementation | Tests written for verified behaviour; `python manage.py check` after each story phase | ✅ PASS | Existing infrastructure verified; new test cases target the three stub fixes |
| I. Story-Level Validation | Tasks grouped by user story; manage.py check + pytest required per phase | ✅ PASS | Required in tasks.md generation |
| II. Documentation-First | Public API documented in quickstart and skill | ✅ PASS | [quickstart.md](quickstart.md), [contracts/view-api.md](contracts/view-api.md), `skills/django-mvp/SKILL.md` update required |
| III. Component Quality & Accessibility | No new templates or Cotton components | ✅ PASS | Python-only changes |
| IV. Config-Driven Design | All configuration via class attributes | ✅ PASS | `list_item_template`, `grid`, `empty_state_*`, `directory`, `paginate_by` |
| V. Tooling & Consistency | Ruff + djlint must pass | ✅ PASS | Python-only changes; no template files added |
| VI. UI Verification (playwright-mcp) | No new HTML/CSS/templates | ⚠️ REQUIRES TASK | Template files unchanged, but rendered output changes: page title was `None` (now model name), pagination controls activate at 24 records, "New" button eligibility changes. A Playwright verification task is required per Constitution VI. Added as T044 in tasks.md. |
| VIII. End-to-End Testing (pytest-playwright) | E2E required when user-visible behaviour changes | ⚠️ REQUIRES TASK | Stub fixes produce user-visible changes (title, pagination). Playwright MCP verification (T044) satisfies the in-PR interactive check. No persistent pytest-playwright spec added (changes are behavior-restoring fixes, not new feature screens); T044 covers the acceptance gate. |
| IX. Template Component Reuse | No new templates | ✅ PASS | No template changes |
| X. django-mvp Skill Currency | `skills/django-mvp/SKILL.md` must document `MVPListView` API | ✅ PASS | Listed as required file change |
| XI. Dual-Audience User Stories | Developer and end-user stories both present in spec | ✅ PASS | US1–US6 cover both audiences |
| XII. View Class Docstring Completeness | `MVPListViewMixin` and `MVPListView` need full Config/Override hooks/Example docstrings | ✅ PASS | Listed as required change; both currently have placeholder docstrings |

**Constitution Check result**: All gates PASS. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/015-mvp-list-view/
├── plan.md              ← this file
├── research.md          ← Phase 0 decisions
├── data-model.md        ← attribute/context variable schema
├── quickstart.md        ← developer quickstart
├── contracts/
│   └── view-api.md      ← public API contract for MVPListViewMixin and MVPListView
└── tasks.md             ← Phase 2 output (/speckit.tasks command)
```

### Source Code

```text
mvp/
└── views/
    └── list.py                         ← implement get_page_title(), set directory, add paginate_by, add docstrings (modify)

tests/
└── test_views/
    └── test_list_view.py               ← add MVPListViewMixin test cases (modify)

skills/
└── django-mvp/
    └── SKILL.md                        ← add MVPListView section (modify)
```

## Design Decisions

### D1: `get_page_title()` implementation

```python
def get_page_title(self):
    if self.page_title:
        return self.page_title
    return self.model._meta.verbose_name_plural.title()
```

`page_title` (inherited from `PageMixin`, default `""`) is checked for truthiness first.
When truthy, it is returned as-is. When falsy (empty string, `None`, or unset), the model's
`verbose_name_plural` is used. This mirrors the precedence pattern used by other views
in the library (e.g., `MVPCreateView`).

### D2: `directory = ["create"]` placement

`directory = ["create"]` is set **on `MVPListViewMixin`**, not on `MVPListView`. This ensures
that any custom view combining `MVPListViewMixin` with a non-`ListView` base class
(e.g., `MVPFilteredListView`) also inherits the correct scoping. The attribute is defined at
the mixin level to match where all other `MVPListViewMixin` class attributes live.

### D3: `paginate_by = 24` placement

`paginate_by = 24` is set **on `MVPListView`**, not on `MVPListViewMixin`. This keeps
`MVPListViewMixin` neutral — developers combining it with custom base classes retain full
control over pagination. 24 was chosen because it is the smallest even number divisible
by 1, 2, 3, and 4, making it ideal for grid layouts of any common column count.

### D4: Breadcrumb default

The existing `get_breadcrumbs()` on `MVPListViewMixin` already returns:

```python
[{"text": _("Home"), "href": "/"}, {"text": self.get_page_title()}]
```

This satisfies FR-011. No change needed; the stub fix to `get_page_title()` (D1) makes
the breadcrumb title correct automatically.

### D5: Test helper for `MVPListViewMixin`

A new `_make_list_view()` helper will be added to `test_list_view.py` alongside
the existing `_make_search_view()` / `_make_order_view()` helpers. It produces a
fully-wired `MVPListViewMixin + ListView` stub with `request`, `kwargs`, `args`,
and `object_list` set, avoiding template rendering.

## Constitution Check (post-design)

All gates re-checked after Phase 1 design. No new violations introduced.

- Principle XII: `MVPListViewMixin` docstring will include `Config:`, `Override hooks:`,
  and a minimal 5-line usage example as mandated.
- Principle II: `quickstart.md` and `contracts/view-api.md` are generated as part of this
  plan; `skills/django-mvp/SKILL.md` update is a required task.
- Principle I: All code changes are testable without running a server. `manage.py check`
  is a required step in each story phase task.

**Post-design Constitution Check result**: PASS.
