# Implementation Plan: HTMX Form Mixin

**Propagated**: 2026-05-28 — Updated from spec.md refinement
**Propagated**: 2026-05-29 — Added US5 (`htmx_success_components` allowlist + `X-Success-Component` client-driven component selection)
**Propagated**: 2026-05-29 — Added `HtmxMixin` base class; `get_context_data()` / `htmx_enabled` moves from `HtmxFormMixin` to `HtmxMixin`; `HtmxFormMixin` now inherits from `HtmxMixin` (FR-025–FR-026, Phase 9)
**Propagated**: 2026-05-29 — Expanded `HtmxMixin`: trigger subsystem (`htmx_trigger`, `htmx_trigger_after`, `_apply_htmx_triggers()`) and `_resolve_component()` helper move from `HtmxFormMixin` to `HtmxMixin`; `get_htmx_success_component()` delegates to `_resolve_component()` (FR-027–FR-028, Phase 10)

**Branch**: `020-htmx-form-mixin` | **Date**: 2026-05-28 | **Spec**: [specs/020-htmx-form-mixin/spec.md](spec.md)
**Input**: Feature specification from `specs/020-htmx-form-mixin/spec.md`

## Summary

A new `HtmxMixin` base class and `HtmxFormMixin` subclass that augment any of the package's existing form views (`MVPFormView`, `MVPCreateView`, `MVPUpdateView`, `MVPDeleteView`) with htmx progressive enhancement. On a valid htmx POST it returns a Cotton component partial (or an `HX-Redirect` header); on an invalid htmx POST it returns the form Cotton component at HTTP 200. Non-htmx requests are completely unmodified.

`HtmxMixin` is a lightweight base class for all htmx-enhanced views. It provides: `get_context_data()` (injects `htmx_enabled = True`), the trigger subsystem (`htmx_trigger`, `htmx_trigger_after`, `_apply_htmx_triggers()`), and `_resolve_component(attr, allowlist_attr, header_name)` — a shared helper for client-driven component selection via request headers. Any future htmx view type (e.g., `HtmxListViewMixin`) inherits all three capabilities without form-specific code. `HtmxFormMixin` inherits from `HtmxMixin` and adds all form-specific behaviour; its public API is unchanged. `get_htmx_success_component()` now delegates the allowlist/header lookup to `_resolve_component()`.

Success component resolution follows a two-stage lookup: (1) if `htmx_success_components` (a tuple of `(alias, component)` pairs) is non-empty and the `X-Success-Component` request header is present with a known alias, that component is returned immediately; (2) otherwise the server default `htmx_success_component` is used. Unknown aliases fall through silently. The feature is opt-in — an empty `htmx_success_components` means the header is always ignored.

## Technical Context

**Language/Version**: Python 3.12 / 3.13
**Primary Dependencies**: Django 5.2+, `django-htmx>=1.0,<2.0` (dev/optional dep — not declared as a package dependency; developers must install it themselves), `django-cotton==2.6.1` (existing dep)
**Storage**: N/A — no model changes, no migrations
**Testing**: pytest + pytest-django (unit); pytest-playwright (browser htmx interactions)
**Target Platform**: Django web application (server-side)
**Project Type**: Reusable Django app — view mixin
**Performance Goals**: No additional database queries beyond the existing form view chain
**Constraints**: Zero regression on non-htmx paths; 100% branch coverage on mixin logic
**Scale/Scope**: One new Python file (~150 LOC), one test module, one demo view, two demo Cotton components

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
    ├── htmx.py                      # NEW — HtmxMixin + HtmxFormMixin (import directly from mvp.views.htmx)
    │                                #   HtmxMixin: get_context_data(), htmx_trigger, htmx_trigger_after,
    │                                #     _apply_htmx_triggers(), _resolve_component()
    │                                #   HtmxFormMixin(HtmxMixin): htmx_success_component,
    │                                #     htmx_success_components, htmx_form_component,
    │                                #     htmx_redirect_on_success (trigger attrs inherited from HtmxMixin)
    └── __init__.py                  # unchanged — neither HtmxMixin nor HtmxFormMixin exported here

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

pyproject.toml                       # updated — add django-htmx as dev dependency only (not in [project] dependencies)
```

**Structure Decision**: Single Django app layout. New source file `mvp/views/htmx.py` isolates the `django-htmx` dependency and keeps `edit.py` clean. `HtmxFormMixin` is NOT exported from `mvp/views/__init__.py` to avoid `ImportError` in projects that do not install `django-htmx`. No new Django app or package is required.

## Complexity Tracking

No constitution violations — table omitted.
