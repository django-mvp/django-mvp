# Implementation Plan: Mobile Footer Navigation

**Branch**: `017-mobile-footer-nav` | **Date**: 2026-05-26 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/017-mobile-footer-nav/spec.md`

## Summary

Add a mobile-only sticky footer navigation bar to django-mvp's layout system.
The nav bar is rendered by a new `c-app.mobile-footer-nav` Cotton component inserted
inside `c-app` in `base.html`. Items are populated via a new `MobileFooterMenu`
singleton (independent of `AppMenu`), rendered by a new `MobileFooterNavRenderer`
registered as `"mobile-footer-nav"` in `FLEX_MENUS`. The component is hidden on
desktop using the existing `.show-on-mobile` CSS utility (no new media queries needed).
It ships pre-populated with a sidebar toggle item using `data-lte-toggle="sidebar"`.

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
tests MUST go in `tests/test_components/test_c_app.py` (not a new file per Principle IX)
**Scale/Scope**: Small addition — 2 Python class additions, 1 Cotton component,
2 menu templates, 1 SCSS partial, 1 base.html block, 1 settings entry

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design — all
gates continue to pass.*

| Principle | Gate | Status |
|---|---|---|
| I. Design-First | Playwright MCP verification tasks required; pytest coverage required; Cotton tests in `tests/test_components/test_c_app.py` | ✅ PASS — all verification tasks planned |
| II. Documentation-First | `skills/django-mvp/SKILL.md` must be updated; quickstart.md produced | ✅ PASS — quickstart.md created; SKILL.md update in scope |
| III. Component Quality & Accessibility | Semantic `<nav>` with `aria-label` (FR-012); valid HTML | ✅ PASS — `<nav aria-label="Mobile navigation">` in design |
| IV. Compatibility & Config-Driven | Cotton-only UI; renderer via settings; no breaking changes on existing API | ✅ PASS — new block/component; does not alter existing API |
| V. Tooling & Consistency | Ruff + djlint must pass; SCSS in existing pipeline | ✅ PASS — no new tooling needed |
| VI. UI Verification (playwright-mcp) | Playwright MCP tasks required for all UI changes | ✅ PASS — planned in tasks |
| VII. Documentation Retrieval | context7 for django-flex-menus | ✅ PASS — to be used during implementation |
| VIII. E2E Testing | pytest-playwright E2E tests required | ✅ PASS — planned |
| IX. Template Component Reuse | Prebuilt-first check; custom Cotton component; tests in `test_c_app.py` | ✅ PASS — no suitable prebuilt component; `test_c_app.py` grouping confirmed |
| X. SKILL.md Currency | `skills/django-mvp/SKILL.md` must be updated | ✅ PASS — in scope |
| XI. Dual-Audience | Developer + End User stories both present in spec | ✅ PASS — User Story 1 (Developer), Stories 2–3 (End User) |
| XII. View Docstring Completeness | No new view classes introduced | ✅ PASS — N/A |

## Project Structure

### Documentation (this feature)

```text
specs/017-mobile-footer-nav/
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
│       ├── _mobile-footer-nav.scss       # NEW — sticky positioning + z-index + nav-link layout
│       └── mvp.scss                      # + @use "_mobile-footer-nav"
└── templates/
    ├── cotton/
    │   └── app/
    │       └── mobile-footer-nav.html    # NEW — c-app.mobile-footer-nav Cotton component
    ├── menus/
    │   └── mobile-footer-nav/
    │       ├── wrapper.html              # NEW — depth-0: <ul class="nav"> + children loop
    │       └── item.html                # NEW — depth-1+: BS5 .nav-item leaf

mvp/templates/mvp/
└── base.html                             # + {% block app.mobile_footer_nav %} inside <c-app>

tests/
├── settings.py                           # + "mobile-footer-nav" in FLEX_MENUS["renderers"]
└── test_components/
    └── test_c_app.py                     # + mobile-footer-nav component tests (grouped per Principle IX)

skills/
└── django-mvp/
    └── SKILL.md                          # + MobileFooterMenu, renderer registration, c-app.mobile-footer-nav usage
```

**Structure Decision**: Single Django library layout. All new source files are
confined to the `mvp/` package tree with tests mirrored under `tests/`. The new
Cotton component follows the `cotton/app/` convention established by
`header.html`, `sidebar/`, `main.html`, and `footer.html`. Menu templates follow
the `menus/nav/` convention established by `NavRenderer`. The SCSS partial follows
the `_utils.scss` / `mvp.scss` partial-import pattern.

## Complexity Tracking

> No Constitution violations. This section is left blank per instructions.
