# Tasks: Mobile Footer Navigation

**Input**: Design documents from `specs/017-dock/`
**Feature Branch**: `017-dock`
**Prerequisites**: plan.md ✅ · spec.md ✅ · research.md ✅ · data-model.md ✅ · contracts/public-api.md ✅ · quickstart.md ✅
**Propagated**: 2026-05-26 — Updated from spec.md refinement (NFR-001: BS5-utility-first styling). T002/T009/T010 descriptions corrected; corrective tasks T023–T026 added.
**Propagated**: 2026-05-26 — Reflected user template/style refactoring. T004/T008/T009/T010/T017 descriptions updated; Phase 9 (T027–T029) added for test corrections.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other [P] tasks at the same phase (different files, no shared dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)
- File paths are relative to the `django-mvp/` workspace root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Register the new renderer in the test settings so all subsequent story phases can run against a fully configured environment.

- [X] T001 Register `"dock": "mvp.renderers.MobileFooterNavRenderer"` in `FLEX_MENUS["renderers"]` dict in `tests/settings.py`

**Checkpoint**: `python manage.py check` passes with the new key present before any implementation exists (renderer import error expected — confirms the hook is wired).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: SCSS infrastructure that all stories depend on for visible output. Must be complete before any UI story can be visually verified.

**⚠️ CRITICAL**: All user story UI work depends on the SCSS partial being importable from `mvp.scss`.

- [X] T002 [P] Create `mvp/static/scss/_dock.scss` containing **only** `padding-bottom: env(safe-area-inset-bottom, 0)` within `.dock` for iOS safe-area support. All other properties (positioning, background, border, flex layout) are applied as BS5 utility classes in templates — NOT in this file (NFR-001).
- [X] T003 Add `@use "dock"` to the partials block in `mvp/static/scss/mvp.scss` (depends on T002)

**Checkpoint**: SCSS compiles without errors (run `python manage.py check` — static assets compile on first request in dev).

---

## Phase 3: User Story 1 — Developer Adds Items to Mobile Footer Menu (Priority: P1) 🎯 MVP

**Goal**: A developer can import `MobileFooterMenu`, append `MenuItem` instances, and see them rendered in the footer nav — independently of `AppMenu`.

**Independent Test**: Register a test `MenuItem` on `MobileFooterMenu`, render `c-app.dock` with `cotton_render_soup`, assert the item appears as a `.nav-item > .nav-link` in the output.

### Tests for User Story 1 ⚠️ Write FIRST — must FAIL before implementation

- [X] T003a [P] Consult context7 for up-to-date `django-flex-menus` `BaseRenderer` API before writing any implementation in T006–T009 — confirm `get_context_data` signature, `visible` field behaviour, and template rendering loop (Constitution Principle VII)

- [X] T004 [P] [US1] Add `TestCAppMobileFooterNav` class to `tests/test_components/test_c_app.py` with tests for:
  - outer container `<div>` carries `aria-label="Mobile navigation"` and `show-on-mobile`
  - component's inner `<nav>` (from `<c-nav>`) is present
  - pre-populated sidebar toggle renders as `<button data-lte-toggle="sidebar">`
  - custom `MenuItem` added to `MobileFooterMenu` appears as direct `<button>`/`<a class="nav-link">` child of `<nav>` (no `<li>` wrapper)
  - empty `MobileFooterMenu` renders without broken markup (checks for `<nav>`)
  - `class` attribute is forwarded to the outer `<div>` element
  - a `MenuItem` with a permission/visibility constraint the current user does not satisfy does NOT appear in rendered output (FR-011)

- [X] T005 [P] [US1] Create `tests/test_renderers.py` with `TestMobileFooterNavRenderer` class testing:
  - `MobileFooterNavRenderer` is importable and is a `BaseRenderer` subclass
  - `templates` dict maps depth-0 to `menus/dock/index.html`
  - `templates` dict maps depth-1+ leaf and parent to `menus/dock/item.html`
  - renderer is registered under key `"dock"` in test settings `FLEX_MENUS`
  - a mocked item with `visible=False` produces no output (confirms `super().get_context_data()` `BaseRenderer` visibility filtering is preserved — FR-011)

### Implementation for User Story 1

- [X] T006 [P] [US1] Add `MobileFooterMenu` singleton to `mvp/menus.py` — `Menu("MobileFooterMenu", children=[MenuItem(name="sidebar_toggle", extra_context={...})])` pre-populated with the sidebar toggle item per data-model.md Entity 1
- [X] T007 [P] [US1] Add `MobileFooterNavRenderer` class to `mvp/renderers.py` with `templates` dict mapping depth-0 to `menus/dock/index.html` and depth-1+ to `menus/dock/item.html` per data-model.md Entity 2
- [X] T008 [P] [US1] Create `mvp/templates/menus/dock/index.html` — renders `<c-nav :attrs="context">` passing `MobileFooterMenu.extra_context` (type, fill, gap) as component attributes, iterates children via `{% render_item child renderer=renderer %}` with `<div class="vr my-2">` separators between items per data-model.md Entity 3
- [X] T009 [P] [US1] Create `mvp/templates/menus/dock/item.html` — renders `<c-link text="{{ label }}" :href="url" :active="selected" :attrs="attrs">` with `btn-icon` class when `show_text` is falsy (icon-only default) and optional extra classes; delegates button-vs-anchor branching and `data-lte-toggle` attribute forwarding to `<c-link>` via `:attrs="attrs"`. **NFR-001**: all item layout handled by the cotton-bs5 component; no custom SCSS rules.
- [X] T010 [US1] Create `mvp/templates/cotton/app/dock.html` — Cotton component with a `<div>` outer positioning container carrying `fixed-bottom bg-body border-top show-on-mobile dock` and `aria-label="Mobile navigation"`; wraps `{% render_menu "MobileFooterMenu" renderer="dock" %}` whose wrapper template provides the inner `<c-nav>` semantic nav element; per contracts/public-api.md Cotton Component API. (depends on T007, T008, T009)
- [X] T011 [US1] Add `{% block app.mobile_footer_nav %}<c-app.dock />{% endblock app.mobile_footer_nav %}` to `mvp/templates/mvp/base.html` immediately after `{% endblock app.footer %}` and before `{% endblock app %}` per contracts/public-api.md Template Block API (depends on T010)
- [X] T011a [US1] **Playwright MCP inline verification** (Constitution Principle VI): use the Playwright MCP server to open the running dev app in a 375×812 mobile viewport; confirm `nav[aria-label="Mobile navigation"]` is present and visually pinned at the bottom of the viewport; confirm the pre-populated sidebar toggle `<button data-lte-toggle="sidebar">` is visible and tappable; screenshot for record (depends on T011)
- [X] T012 [US1] Validate User Story 1: `python manage.py check` then `pytest tests/test_components/test_c_app.py::TestCAppMobileFooterNav tests/test_renderers.py -v` — all tests must pass GREEN

**Checkpoint**: User Story 1 fully functional — developer can add items to `MobileFooterMenu` and see them rendered. Cotton component and renderer complete and tested.

---

## Phase 4: User Story 2 — End User Sees Footer Nav on Mobile Only (Priority: P1)

**Goal**: The footer nav is visible on viewports below the `sidebar-expand` breakpoint and hidden at or above it. Sticky positioning keeps it fixed during scroll.

**Independent Test**: Use Playwright to load a page at 375px (mobile) and assert `nav.show-on-mobile` is visible; load at 1200px (desktop) and assert it is hidden.

### Tests for User Story 2 ⚠️ Write FIRST — must FAIL before implementation

- [X] T013 [P] [US2] Create `tests/test_views/test_mobile_footer_nav_e2e.py` with `@pytest.mark.e2e` class `TestMobileFooterNavVisibility` containing:
  - `test_footer_nav_visible_on_mobile` — viewport 375×812, assert `nav[aria-label="Mobile navigation"]` is visible
  - `test_footer_nav_hidden_on_desktop` — viewport 1280×800, assert same nav is hidden
  - `test_footer_nav_fixed_during_scroll` — mobile viewport, scroll 500px, assert nav bounding box `y + height ≈ viewport height` (still pinned)
  - Use `pytest.importorskip("playwright")` guard and `pytestmark = pytest.mark.e2e` at module level

### Implementation for User Story 2

No new implementation files required — visibility is governed by the `show-on-mobile` CSS class (already active via T002/T003 SCSS and T010 component). Verify SCSS partial includes the `d-none` / display override rules within the `.sidebar-expand` loop interaction (research.md §2 confirms `.show-on-mobile` already exists in `_utils.scss`).

- [X] T014 [US2] Validate User Story 2: `python manage.py check` then `pytest tests/test_views/test_mobile_footer_nav_e2e.py -m e2e -k "visibility or scroll" -v` — all visibility tests must pass GREEN

**Checkpoint**: Footer nav responsive visibility confirmed by Playwright at both mobile and desktop breakpoints.

---

## Phase 5: User Story 3 — End User Taps Sidebar Toggle in Footer Nav (Priority: P2)

**Goal**: The pre-populated sidebar toggle item in the footer nav opens and closes the AdminLTE 4 sidebar via `data-lte-toggle="sidebar"` — no custom JS required.

**Independent Test**: Use Playwright on mobile viewport to tap the `button[data-lte-toggle="sidebar"]` inside the footer nav, assert sidebar overlay becomes visible; tap again, assert it is hidden.

### Tests for User Story 3 ⚠️ Write FIRST — must FAIL before implementation

- [X] T015 [P] [US3] Add `TestMobileFooterNavSidebarToggle` class to `tests/test_views/test_mobile_footer_nav_e2e.py` with:
  - `test_sidebar_opens_when_toggle_tapped` — mobile viewport, click `nav[aria-label="Mobile navigation"] button[data-lte-toggle="sidebar"]`, assert sidebar overlay or sidebar element becomes visible
  - `test_sidebar_closes_when_toggle_tapped_again` — mobile viewport, open sidebar via toggle, tap again, assert sidebar is closed/hidden
  - `test_default_menu_has_exactly_one_item` — render page, count items inside footer nav, assert exactly 1

### Implementation for User Story 3

No new implementation files required — the `data-lte-toggle="sidebar"` button was defined in T006 (`MobileFooterMenu` pre-populated item) and T009 (item template button rendering). Confirm `sidebar-toggle.js` script tag already loads in `base.html` (research.md §3 confirms it is on line 134).

- [X] T016 [US3] Validate User Story 3: `python manage.py check` then `pytest tests/test_views/test_mobile_footer_nav_e2e.py -m e2e -k "sidebar_toggle or sidebar_opens or sidebar_closes or default_menu" -v` — all sidebar toggle tests must pass GREEN
- [X] T016a [US3] **Playwright MCP inline verification** (Constitution Principle VI): use the Playwright MCP server on a 375×812 mobile viewport; tap `nav[aria-label="Mobile navigation"] button[data-lte-toggle="sidebar"]`; confirm the sidebar opens (sidebar overlay or `aside.app-sidebar` becomes visible); tap again and confirm it closes; screenshot both states for record

**Checkpoint**: Sidebar toggle works end-to-end on mobile via the pre-populated footer nav item.

---

## Phase 6: User Story 4 — Developer Uses Custom Renderer for Consistent Link Styling (Priority: P2)

**Goal**: Every item rendered by `MobileFooterNavRenderer` produces valid BS5 `.nav-item > .nav-link` markup with correct active state, icon support, and button-vs-link branching — regardless of item position.

**Independent Test**: Use `cotton_render_soup` or direct template rendering to assert `.nav-item > .nav-link` structure, `active` class on matching URL, icon presence, and `<button>` vs `<a>` branching for sidebar toggle items.

### Tests for User Story 4 ⚠️ Write FIRST — must FAIL before implementation

- [X] T017 [P] [US4] Extend `tests/test_renderers.py` with `TestMobileFooterNavRendererOutput` class testing:
  - `test_item_renders_nav_item_nav_link_structure` — rendered HTML contains a direct `<button>`/`<a class="nav-link">` child of `<nav>` (no `<li class="nav-item">` wrapper)
  - `test_active_class_applied_when_url_matches_request_path` — item with matching URL gets `active` on `.nav-link`
  - `test_no_active_class_when_url_does_not_match` — non-matching URL has no `active` class
  - `test_icon_rendered_when_icon_in_extra_context` — icon element present in output
  - `test_sidebar_toggle_renders_as_button_not_anchor` — sidebar toggle item renders `<button>`, not `<a>`
  - `test_regular_item_renders_as_anchor_not_button` — non-toggle item renders `<a>`, not `<button>`
  - `test_sidebar_toggle_has_data_lte_toggle_attribute` — `data-lte-toggle="sidebar"` present on toggle button
  - `test_items_rendered_in_registration_order` — two items registered in order appear in DOM order (find by `.nav-link` class)

### Implementation for User Story 4

No new implementation files required — the renderer (`mvp/renderers.py`, T007) and templates (`mvp/templates/menus/dock/`, T008/T009) were created in Phase 3. Verify all renderer contract assertions in the new tests pass against the existing implementation.

- [X] T018 [US4] Validate User Story 4: `python manage.py check` then `pytest tests/test_renderers.py -v` — all renderer output tests must pass GREEN

**Checkpoint**: All user stories (US1–US4) are independently functional and fully tested.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, linting, and full-suite green — Constitution Principles II, V, X.

- [X] T019 Update `skills/django-mvp/SKILL.md` to document: `MobileFooterMenu` import and `children.append()` usage, `"dock"` renderer registration in `FLEX_MENUS`, `c-app.dock` component with `class` attribute, `{% block app.mobile_footer_nav %}` override pattern, and removal of pre-populated sidebar toggle
- [X] T020 [P] Run `ruff check mvp/menus.py mvp/renderers.py` and fix any style or import-order violations
- [X] T021 [P] Run `djlint mvp/templates/cotton/app/dock.html mvp/templates/menus/dock/index.html mvp/templates/menus/dock/item.html --check` and fix any template formatting issues
- [X] T022 Full suite validation: `python manage.py check` then `pytest -m "not e2e"` (unit + component tests) then `pytest -m e2e` (Playwright) — entire test suite must be GREEN with no regressions

**Checkpoint**: Feature complete. All linters pass, all tests green, SKILL.md updated.

---

## Phase 8: NFR-001 Corrective Refactoring (BS5-Utility-First)

**Purpose**: The implementation of T002/T009/T010 predates NFR-001. These corrective tasks bring the existing implementation into compliance with the refined spec by removing custom SCSS rules that have direct BS5 utility class equivalents and moving them to templates.

- [X] T023 [P] Refactor `mvp/static/scss/_dock.scss` — remove `position: fixed`, `bottom`, `left`, `right`, `z-index`, `background-color`, `border-top`, and `.nav-link` flex/padding rules; retain **only** `padding-bottom: env(safe-area-inset-bottom, 0)` inside `.dock { }` (NFR-001)
- [X] T024 [P] Add BS5 utility classes `fixed-bottom bg-body border-top` to the `<nav>` element in `mvp/templates/cotton/app/mobile_footer_nav.html`; update `TestCAppMobileFooterNav` test assertions if class names on `<nav>` change (NFR-001, depends on T023)
- [X] T025 [P] Add BS5 utility classes `d-flex flex-column align-items-center py-2 px-1` to `.nav-link` elements in `mvp/templates/menus/dock/item.html`; update `TestMobileFooterNavRendererOutput` test assertions if `.nav-link` class list changes (NFR-001, depends on T023)
- [X] T026 Validate NFR-001 refactoring: `python manage.py check` then `pytest tests/test_components/test_c_app.py::TestCAppMobileFooterNav tests/test_renderers.py -v` — all tests must pass GREEN with no regressions (depends on T023, T024, T025)

**Checkpoint**: `_dock.scss` contains only `env(safe-area-inset-bottom)`. All positioning/background/border/flex layout is applied via BS5 utility classes in templates. Tests green.

---

## Phase 9: Test Corrections for `<c-nav>`/`<c-link>` Architecture

**Purpose**: The user's template refactoring (reflected in T008/T009/T010) uses `<c-nav>` and `<c-link>` cotton-bs5 components instead of custom HTML, changing the DOM structure. Seven tests written against the original `<nav>` outer + `<li class="nav-item">` structure are failing. These tasks update assertions to match the actual architecture.

- [X] T027 [P] Update `TestCAppMobileFooterNav` failing tests in `tests/test_components/test_c_app.py`:
  - `test_renders_nav_with_aria_label`: find outer `<div>` with `aria-label="Mobile navigation"` (not `<nav>`)
  - `test_applies_show_on_mobile_class`: assert `show-on-mobile` is on the outer `<div>`, not on the inner `<nav>`
  - `test_custom_menu_item_appears_as_nav_item_nav_link`: assert item is a direct `<button>`/`<a class="nav-link">` child of `<nav>` (no `<li>` wrapper)
  - `test_empty_menu_renders_without_broken_markup`: check for `<nav>` (not `<ul>`) in output
  - `test_class_attribute_forwarded_to_nav`: check custom class is on outer `<div>`, not inner `<nav>`

- [X] T028 [P] Update `TestMobileFooterNavRendererOutput` failing tests in `tests/test_renderers.py`:
  - `test_item_renders_nav_item_nav_link_structure`: assert direct child `<button>`/`<a class="nav-link">` of `<nav>` (no `<li class="nav-item">`)
  - `test_items_rendered_in_registration_order`: find items by `class_="nav-link"` as direct `<nav>` children (not `<li class="nav-item">`)

- [X] T029 Validate: `pytest tests/test_components/test_c_app.py::TestCAppMobileFooterNav tests/test_renderers.py -v` — all 22 tests must pass GREEN (depends on T027, T028)

**Checkpoint**: 7 previously-failing tests corrected and passing; all tests in both test files pass GREEN.

---

## Dependency Graph

```
T001 (settings)
    └─→ T012 (US1 validate)

T002 (SCSS partial)
    └─→ T003 (SCSS import)
            └─→ T014 (US2 validate)

T003a (context7 API research)
    └─→ T006, T007, T008, T009 (implementation)

T004 (Cotton component tests - RED) ─┐
T005 (renderer unit tests - RED)     │
T006 (MobileFooterMenu)             ─┤
T007 (MobileFooterNavRenderer)      ─┤
T008 (wrapper.html)                 ─┤→ T010 (Cotton component) → T011 (base.html block) → T011a (MCP verify) → T012 (US1 validate)
T009 (item.html)                    ─┘

T012 (US1 validate)
    └─→ T013 (E2E visibility tests - RED)
            └─→ T014 (US2 validate)
                    └─→ T015 (E2E sidebar toggle tests - RED)
                            └─→ T016 (US3 validate)
                                    └─→ T016a (MCP sidebar toggle verify)
                                            └─→ T017 (renderer output tests - RED)
                                                    └─→ T018 (US4 validate)
                                                            └─→ T019 (SKILL.md)
                                                            └─→ T020 (ruff)
                                                            └─→ T021 (djlint)
                                                            └─→ T022 (full suite)

T023 (refactor _dock.scss — NFR-001)
    ├─→ T024 (add fixed-bottom/bg-body/border-top to <nav> — NFR-001)
    ├─→ T025 (add d-flex/flex-column/align-items-center to .nav-link — NFR-001)
    └─→ (T024 + T025) → T026 (validate NFR-001 refactoring)

T027 [P] (update TestCAppMobileFooterNav assertions) ─┐
T028 [P] (update TestMobileFooterNavRendererOutput assertions) ─┘
    └─→ T029 (validate: all 22 tests GREEN)
```

**Story completion order**: US1 (P1) → US2 (P1) → US3 (P2) → US4 (P2)

---

## Parallel Execution Examples

**Phase 2**: T002 and T003 are sequential; T002 can run alongside T004/T005/T006/T007/T008/T009 as they touch different files.

**Phase 3 setup (after T001 + T002)**: T004, T005, T006, T007, T008, T009 can all run in parallel — each edits a different file.

**Phase 7**: T019, T020, T021 can all run in parallel.

---

## Implementation Strategy

**MVP scope**: Phases 1–3 (T001–T012) deliver User Story 1 — a fully functional `MobileFooterMenu` + renderer + Cotton component. This alone is independently releasable.

**Incremental delivery**:

1. US1 (T001–T012): Core menu object, renderer, component, base.html wiring — developer integration story complete
2. US2 (T013–T014): Playwright verification of responsive visibility — end user story confirmed
3. US3 (T015–T016): Sidebar toggle E2E — default item behavior confirmed
4. US4 (T017–T018): Renderer contract assertions — developer consistency story confirmed
5. Polish (T019–T022): Docs, lint, full suite green

**TDD order within each phase**: Write tests (RED) → implement (GREEN) → validate checkpoint.
