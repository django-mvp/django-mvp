# Implementation Plan: CRUD Directory Mixin

**Branch**: `006-crud-directory-mixin` | **Date**: 2026-05-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-crud-directory-mixin/spec.md`

## Summary

`CRUDDirectoryMixin` provides declarative, permission-gated CRUD URL resolution for model-driven Django views. Developers list the actions they want available (`directory = ["list", "detail", "update", "delete"]`), set per-action permission flags (`has_{action}_permission`), and the mixin resolves the correct URLs from the current model and request kwargs — injecting them into the template context as a `directory` dict. Templates rely on the presence or absence of `{action}_url` keys to render action buttons and navigation links without any URL wiring code in the view or template.

An experimental implementation already exists in `mvp/views/detail.py`. Research (see `research.md`) identified three functional gaps and three structural issues that must be addressed before the mixin can be considered production-ready:

1. **Permission naming mismatch**: `has_read_permission` is declared but never checked; the `"detail"` action checks `has_detail_permission`. Rename to align with action names.
2. **URL kwargs leak**: `get_lookup_kwargs()` (the single override point) is used for ALL actions. On detail/edit views this passes `pk` when reversing collection URLs (`list`, `create`), causing latent `NoReverseMatch` errors. Fix by splitting into `get_object_url_kwargs()` + `get_collection_url_kwargs()`.
3. **`MVPUpdateView.get_delete_url()` ignores permissions**: generates the delete URL without checking `has_delete_permission`. Fix by routing through `_resolve_directory_url`.

The implementation also has structural issues: `_OBJECT_ACTIONS` exposed as a class attribute, redundant `ModelInfoMixin` in `PageObjectMixin`'s explicit bases, and zero test coverage.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Django 4.2+
**Storage**: N/A — pure mixin, no database interaction
**Testing**: pytest, pytest-django (unit tests); pytest-playwright for E2E (UI renders action buttons correctly)
**Target Platform**: Any Django 4.2+ project using the `mvp` package
**Project Type**: Reusable Django app (single source tree under `mvp/`)
**Performance Goals**: N/A — resolution runs once per request; dominated by `dict.get()` + `reverse()` calls
**Constraints**: No backwards compatibility requirements (user explicitly confirmed)
**Scale/Scope**: ~5 methods changed across 2 files; 1 new test module (~200–250 lines); 1 demo page addition

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Design-first approach — review current implementation and design the corrected API (data-model.md), then implement, then write tests
- [x] Visual verification — Playwright MCP server planned for verifying demo page action buttons render correctly with permission gating
- [x] Test types identified — pytest + pytest-django (unit, integration); pytest-playwright for E2E on demo product detail page
- [x] Documentation updates — quickstart.md created; `skills/django-mvp/SKILL.md` update planned (public API change: method renames, new permission attribute names)
- [x] Quality gates understood — `python manage.py check` + pytest + ruff after each phase
- [x] Documentation retrieval — context7 for Django `reverse()` and CBV MRO patterns if needed
- [x] E2E testing — pytest-playwright for US5 (end-user sees correct action buttons for their permission level)
- [x] Tasks grouped by user story — US1 (declarative resolution), US2 (permission gating), US3 (nested URL kwargs), US4 (custom crud_views), US5 (rendered action buttons)
- [x] Every phase touching Django code includes `python manage.py check` validation task
- [x] Every phase touching UI — Playwright MCP server verification task planned for demo page
- [x] UI configuration — no Python-level UI config; demo page uses Cotton template patterns
- [x] Template work — prebuilt django-cotton-bs5 components used first for demo action button rendering
- [x] Custom Cotton components — not anticipated; action buttons are standard Bootstrap/cotton markup
- [x] django-cotton-bs5 / django-cotton skills — consulted before any template work on demo page
- [x] cotton-test-components skill — N/A (no custom Cotton components introduced by this feature)
- [x] Cotton test module topology — N/A (no Cotton components to test)
- [x] `skills/django-mvp/SKILL.md` update planned — method renames and new permission attribute names constitute a public API change
- [x] `skills/django-mvp/SKILL.md` only consulted for demo-app work, not core `mvp/` development
- [x] Spec has at least one [Developer] story (US1–US4) and one [End User] story (US5) ✅

**Post-Phase-1 re-check**: PASS — design (data-model.md) resolves all three functional gaps from research.md with no new violations introduced.

**Constitution gate: PASS — no violations.**

## Project Structure

### Documentation (this feature)

```text
specs/006-crud-directory-mixin/
├── plan.md              # This file
├── research.md          # Phase 0 output (gap analysis + naming + kwargs decisions)
├── data-model.md        # Phase 1 output (entity definitions + public API)
├── quickstart.md        # Phase 1 output (developer usage guide)
├── contracts/
│   └── mixin-api.md     # Phase 1 output — public method and attribute contract
└── tasks.md             # Phase 2 output (generated by /speckit.tasks)
```

### Source Code (repository root)

```text
mvp/
├── views/
│   ├── detail.py        # MODIFY: CRUDDirectoryMixin — rename attrs/methods, add method, fix dispatch
│   │                    # MODIFY: PageObjectMixin — remove redundant ModelInfoMixin from bases
│   └── edit.py          # MODIFY: MVPModelFormBase.get_lookup_kwargs() → get_object_url_kwargs()
│                        # MODIFY: MVPUpdateView.get_delete_url() — apply permission gate

tests/
└── test_views/
    ├── test_base.py                     # UNCHANGED (ModelInfoMixin tests already planned in spec 005)
    ├── test_crud_directory_mixin.py     # NEW: ~200–250 lines; full unit test coverage
    └── test_base_e2e.py                 # ADD: E2E tests for directory-driven action buttons on demo pages

demo/
├── views.py             # ADD: ProductDetailView with directory + permissions configured
├── urls.py              # ADD: product-detail URL pattern
└── templates/demo/      # ADD: product_detail.html template using directory context

skills/
└── django-mvp/
    └── SKILL.md         # MODIFY: update CRUDDirectoryMixin public API reference
                         #         (method renames, new permission attributes)
```

## Complexity Tracking

No constitution violations. No complexity justification required.
