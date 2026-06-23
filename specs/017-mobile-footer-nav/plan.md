# Implementation Plan: Mobile Footer Navigation

**Branch**: `017-dock` | **Date**: 2026-05-26 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/017-dock/spec.md`
**Propagated**: 2026-05-26 — Updated from spec.md refinement (NFR-001: BS5-utility-first styling)
**Propagated**: 2026-05-26 — Reflected user template/style refactoring: `<div>` outer container, `<c-nav>`/`<c-link>` components, `attrs` dict sidebar toggle, `show_text` flag, SCSS underline indicator

## Summary

Add a mobile-only sticky footer navigation bar to django-mvp's layout system.
The nav bar is rendered by a new `c-app.dock` Cotton component inserted
inside `c-app` in `base.html`. Its **outer element is a `<div>` positioning container**
applying `fixed-bottom bg-body border-top show-on-mobile dock` and
`aria-label`; the semantic `<nav>` is provided by the inner `<c-nav>` cotton-bs5
component, configured via `MobileFooterMenu.extra_context` (`type="underline"`,
`fill=True`, `gap=0`). Items are populated via a new `MobileFooterMenu` singleton
(independent of `AppMenu`), rendered by a new `MobileFooterNavRenderer` registered as
`"dock"` in `FLEX_MENUS`. The wrapper template uses `<c-nav :attrs="context">`;
item templates use `<c-link>` as direct children of `<nav>` (no `<li>` wrapper).
Items default to icon-only mode (`btn-icon`) — `show_text=True` in `extra_context`
enables label display. The pre-populated sidebar toggle uses `attrs: {"data-lte-toggle":
"sidebar"}` in `extra_context`, forwarded to the rendered element by `<c-link>`.
**NFR-001**: Bootstrap 5 utility classes and prebuilt cotton-bs5 components are preferred
over custom SCSS and custom HTML. The `_dock.scss` partial is restricted to
`env(safe-area-inset-bottom)` padding and nav-underline active indicator (both lack
BS5 utility equivalents).

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: Django 5.2+, django-flex-menus 0.4.2+, django-cotton 2.3.1+,
django-cotton-bs5 0.9.0+, Bootstrap 5 / AdminLTE 4, django-easy-icons 0.5+, Alpine.js 3.x
**Storage**: N/A — no database models
**Testing**: pytest + pytest-django + pytest-playwright; Cotton component tests grouped
under `tests/test_components/test_c_app.py` (Constitution Principle IX); E2E via
pytest-playwright
**Target Platform**: Django web application — mobile and desktop browsers
**Project Type**: Reusable Django library
**Performance Goals**: N/A (static server-rendered nav; no JS added)
**Constraints**: Cotton-only UI configuration (no Python-level CSS/layout config);
`show-on-mobile` already defined in `_utils.scss` via `.sidebar-expand` loop;
renderer registration via Django `FLEX_MENUS["renderers"]` setting; Cotton component
tests MUST go in `tests/test_components/test_c_app.py` (not a new file per Principle IX);
**NFR-001**: custom SCSS restricted to `env(safe-area-inset-bottom)` padding and
nav-underline active indicator (`var(--bs-nav-underline-border-width)`,
`var(--bs-emphasis-color)`) — both lack BS5 utility equivalents. All other styling
via BS5 utility classes in templates or prebuilt cotton-bs5 components
**Scale/Scope**: Small addition — 2 Python class additions, 1 Cotton component,
2 menu templates, 1 SCSS partial, 1 base.html block, 1 settings entry

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design — all
gates continue to pass.*

| Principle | Gate | Status |
|---|---|---|
| I. Design-First | Playwright MCP verification tasks required; pytest coverage required; Cotton tests in `tests/test_components/test_c_app.py` | ✅ PASS — all verification tasks planned |
| II. Documentation-First | `skills/django-mvp/SKILL.md` must be updated; quickstart.md produced | ✅ PASS — quickstart.md created; SKILL.md update in scope |
| III. Component Quality & Accessibility | Semantic `<nav>` with `aria-label` on outer container (FR-012); valid HTML | ✅ PASS — `<div aria-label="Mobile navigation">` outer; `<nav>` from inner `<c-nav>` |
| IV. Compatibility & Config-Driven | Cotton-only UI; renderer via settings; no breaking changes on existing API | ✅ PASS — new block/component; does not alter existing API |
| V. Tooling & Consistency | Ruff + djlint must pass; SCSS in existing pipeline | ✅ PASS — no new tooling needed |
| VI. UI Verification (playwright-mcp) | Playwright MCP tasks required for all UI changes | ✅ PASS — planned in tasks |
| VII. Documentation Retrieval | context7 for django-flex-menus | ✅ PASS — to be used during implementation |
| VIII. E2E Testing | pytest-playwright E2E tests required | ✅ PASS — planned |
| IX. Template Component Reuse | Prebuilt-first check; tests in `test_c_app.py` | ✅ PASS — wrapper uses `<c-nav>`; items use `<c-link>` from cotton-bs5; `test_c_app.py` grouping confirmed |
| X. SKILL.md Currency | `skills/django-mvp/SKILL.md` must be updated | ✅ PASS — in scope |
| XI. Dual-Audience | Developer + End User stories both present in spec | ✅ PASS — User Story 1 (Developer), Stories 2–3 (End User) |
| XII. View Docstring Completeness | No new view classes introduced | ✅ PASS — N/A |

## Project Structure

### Documentation (this feature)

```text
specs/017-dock/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── public-api.md    # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code

```text
mvp/
├── menus.py                              # + MobileFooterMenu singleton + pre-populated sidebar toggle
├── renderers.py                          # + MobileFooterNavRenderer
├── static/
│   └── scss/
│       ├── _dock.scss       # NEW — iOS safe-area only: env(safe-area-inset-bottom); positioning/bg/border/flex via BS5 utilities in templates (NFR-001)
│       └── mvp.scss                      # + @use "_dock"
└── templates/
    ├── cotton/
    │   └── app/
    │       └── dock.html    # NEW — c-app.dock Cotton component (<div> outer + <c-nav> inner)
    ├── menus/
    │   └── dock/
    │       ├── wrapper.html              # NEW — depth-0: <c-nav :attrs="context"> wrapping children with vr separators
    │       └── item.html                # NEW — depth-1+: <c-link> (direct child of <nav>, no <li>)

mvp/templates/mvp/
└── base.html                             # + {% block app.mobile_footer_nav %} inside <c-app>

tests/
├── settings.py                           # + "dock" in FLEX_MENUS["renderers"]
└── test_components/
    └── test_c_app.py                     # + dock component tests (grouped per Principle IX)

skills/
└── django-mvp/
    └── SKILL.md                          # + MobileFooterMenu, renderer registration, c-app.dock usage
```

**Structure Decision**: Single Django library layout. All new source files are
confined to the `mvp/` package tree with tests mirrored under `tests/`. The new
Cotton component follows the `cotton/app/` convention established by
`header.html`, `sidebar/`, `main.html`, and `footer.html`. Menu templates follow
the `menus/nav/` convention established by `NavRenderer`. The SCSS partial follows
the `_utils.scss` / `mvp.scss` partial-import pattern.

## Complexity Tracking

> No Constitution violations. This section is left blank per instructions.
