# Tasks: Mobile Footer Navigation

**Input**: Design documents from `specs/017-mobile-footer-nav/`
**Feature Branch**: `017-mobile-footer-nav`
**Prerequisites**: plan.md ✅ · spec.md ✅ · research.md ✅ · data-model.md ✅ · contracts/public-api.md ✅ · quickstart.md ✅

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other [P] tasks at the same phase (different files, no shared dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)
- File paths are relative to the `django-mvp/` workspace root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Register the new renderer in the test settings so all subsequent story phases can run against a fully configured environment.

- [ ] T001 Register `"mobile-footer-nav": "mvp.renderers.MobileFooterNavRenderer"` in `FLEX_MENUS["renderers"]` dict in `tests/settings.py`

**Checkpoint**: `python manage.py check` passes with the new key present before any implementation exists (renderer import error expected — confirms the hook is wired).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: SCSS infrastructure that all stories depend on for visible output. Must be complete before any UI story can be visually verified.

**⚠️ CRITICAL**: All user story UI work depends on the SCSS partial being importable from `mvp.scss`.

- [ ] T002 [P] Create `mvp/static/scss/_mobile-footer-nav.scss` with `position: fixed; bottom: 0; left: 0; right: 0; z-index: $zindex-fixed` sticky-footer rules, background (`--bs-body-bg`), and border-top (`--bs-border-color`) for dark-mode compatibility
- [ ] T003 Add `@use "mobile-footer-nav"` to the partials block in `mvp/static/scss/mvp.scss` (depends on T002)

**Checkpoint**: SCSS compiles without errors (run `python manage.py check` — static assets compile on first request in dev).

---

## Phase 3: User Story 1 — Developer Adds Items to Mobile Footer Menu (Priority: P1) 🎯 MVP

**Goal**: A developer can import `MobileFooterMenu`, append `MenuItem` instances, and see them rendered in the footer nav — independently of `AppMenu`.

**Independent Test**: Register a test `MenuItem` on `MobileFooterMenu`, render `c-app.mobile-footer-nav` with `cotton_render_soup`, assert the item appears as a `.nav-item > .nav-link` in the output.

### Tests for User Story 1 ⚠️ Write FIRST — must FAIL before implementation

- [ ] T004 [P] [US1] Add `TestCAppMobileFooterNav` class to `tests/test_components/test_c_app.py` with tests for:
  - component renders `<nav aria-label="Mobile navigation">`
  - component applies `show-on-mobile` CSS class
  - pre-populated sidebar toggle renders as `<button data-lte-toggle="sidebar">`
  - custom `MenuItem` added to `MobileFooterMenu` appears as `.nav-item > .nav-link`
  - empty `MobileFooterMenu` renders without broken markup
  - `class` attribute is forwarded to the `<nav>` element

- [ ] T005 [P] [US1] Create `tests/test_renderers.py` with `TestMobileFooterNavRenderer` class testing:
  - `MobileFooterNavRenderer` is importable and is a `BaseRenderer` subclass
  - `templates` dict maps depth-0 to `menus/mobile-footer-nav/wrapper.html`
  - `templates` dict maps depth-1+ leaf and parent to `menus/mobile-footer-nav/item.html`
  - renderer is registered under key `"mobile-footer-nav"` in test settings `FLEX_MENUS`

### Implementation for User Story 1

- [ ] T006 [P] [US1] Add `MobileFooterMenu` singleton to `mvp/menus.py` — `Menu("MobileFooterMenu", children=[MenuItem(name="sidebar_toggle", extra_context={...})])` pre-populated with the sidebar toggle item per data-model.md Entity 1
- [ ] T007 [P] [US1] Add `MobileFooterNavRenderer` class to `mvp/renderers.py` with `templates` dict mapping depth-0 to `menus/mobile-footer-nav/wrapper.html` and depth-1+ to `menus/mobile-footer-nav/item.html` per data-model.md Entity 2
- [ ] T008 [P] [US1] Create `mvp/templates/menus/mobile-footer-nav/wrapper.html` — renders `<ul class="nav w-100">` and iterates children via `{% render_item child renderer=renderer %}` per data-model.md Entity 3
- [ ] T009 [P] [US1] Create `mvp/templates/menus/mobile-footer-nav/item.html` — renders one BS5 `.nav-item.flex-grow-1.text-center`; sidebar-toggle items render `<button type="button" data-lte-toggle="sidebar">`; other items render `<a href="{{ url }}>`; both include `{% icon icon %}` and label `<span>`; `active` class applied when `selected` per data-model.md Entity 4
- [ ] T010 [US1] Create `mvp/templates/cotton/app/mobile-footer-nav.html` — Cotton component wrapping `{% render_menu "MobileFooterMenu" renderer="mobile-footer-nav" %}` inside `<nav class="show-on-mobile {{ class }}" aria-label="Mobile navigation">` per data-model.md Entity 5 and contracts/public-api.md Cotton Component API (depends on T007, T008, T009)
- [ ] T011 [US1] Add `{% block app.mobile_footer_nav %}<c-app.mobile-footer-nav />{% endblock app.mobile_footer_nav %}` to `mvp/templates/mvp/base.html` immediately after `{% endblock app.footer %}` (line 125) and before `{% endblock app %}` per contracts/public-api.md Template Block API (depends on T010)
- [ ] T012 [US1] Validate User Story 1: `python manage.py check` then `pytest tests/test_components/test_c_app.py::TestCAppMobileFooterNav tests/test_renderers.py -v` — all tests must pass GREEN

**Checkpoint**: User Story 1 fully functional — developer can add items to `MobileFooterMenu` and see them rendered. Cotton component and renderer complete and tested.

---

## Phase 4: User Story 2 — End User Sees Footer Nav on Mobile Only (Priority: P1)

**Goal**: The footer nav is visible on viewports below the `sidebar-expand` breakpoint and hidden at or above it. Sticky positioning keeps it fixed during scroll.

**Independent Test**: Use Playwright to load a page at 375px (mobile) and assert `nav.show-on-mobile` is visible; load at 1200px (desktop) and assert it is hidden.

### Tests for User Story 2 ⚠️ Write FIRST — must FAIL before implementation

- [ ] T013 [P] [US2] Create `tests/test_views/test_mobile_footer_nav_e2e.py` with `@pytest.mark.e2e` class `TestMobileFooterNavVisibility` containing:
  - `test_footer_nav_visible_on_mobile` — viewport 375×812, assert `nav[aria-label="Mobile navigation"]` is visible
  - `test_footer_nav_hidden_on_desktop` — viewport 1280×800, assert same nav is hidden
  - `test_footer_nav_fixed_during_scroll` — mobile viewport, scroll 500px, assert nav bounding box `y + height ≈ viewport height` (still pinned)
  - Follow pattern from `tests/test_views/test_base_e2e.py` for `pytest_playwright` importorskip guard and `pytestmark`

### Implementation for User Story 2

No new implementation files required — visibility is governed by the `show-on-mobile` CSS class (already active via T002/T003 SCSS and T010 component). Verify SCSS partial includes the `d-none` / display override rules within the `.sidebar-expand` loop interaction (research.md §2 confirms `.show-on-mobile` already exists in `_utils.scss`).

- [ ] T014 [US2] Validate User Story 2: `python manage.py check` then `pytest tests/test_views/test_mobile_footer_nav_e2e.py -m e2e -k "visibility or scroll" -v` — all visibility tests must pass GREEN

**Checkpoint**: Footer nav responsive visibility confirmed by Playwright at both mobile and desktop breakpoints.

---

## Phase 5: User Story 3 — End User Taps Sidebar Toggle in Footer Nav (Priority: P2)

**Goal**: The pre-populated sidebar toggle item in the footer nav opens and closes the AdminLTE 4 sidebar via `data-lte-toggle="sidebar"` — no custom JS required.

**Independent Test**: Use Playwright on mobile viewport to tap the `button[data-lte-toggle="sidebar"]` inside the footer nav, assert sidebar overlay becomes visible; tap again, assert it is hidden.

### Tests for User Story 3 ⚠️ Write FIRST — must FAIL before implementation

- [ ] T015 [P] [US3] Add `TestMobileFooterNavSidebarToggle` class to `tests/test_views/test_mobile_footer_nav_e2e.py` with:
  - `test_sidebar_opens_when_toggle_tapped` — mobile viewport, click `nav[aria-label="Mobile navigation"] button[data-lte-toggle="sidebar"]`, assert sidebar overlay or sidebar element becomes visible
  - `test_sidebar_closes_when_toggle_tapped_again` — mobile viewport, open sidebar via toggle, tap again, assert sidebar is closed/hidden
  - `test_default_menu_has_exactly_one_item` — render page, count items inside footer nav, assert exactly 1

### Implementation for User Story 3

No new implementation files required — the `data-lte-toggle="sidebar"` button was defined in T006 (`MobileFooterMenu` pre-populated item) and T009 (item template button rendering). Confirm `sidebar-toggle.js` script tag already loads in `base.html` (research.md §3 confirms it is on line 134).

- [ ] T016 [US3] Validate User Story 3: `python manage.py check` then `pytest tests/test_views/test_mobile_footer_nav_e2e.py -m e2e -k "sidebar_toggle or sidebar_opens or sidebar_closes or default_menu" -v` — all sidebar toggle tests must pass GREEN

**Checkpoint**: Sidebar toggle works end-to-end on mobile via the pre-populated footer nav item.

---

## Phase 6: User Story 4 — Developer Uses Custom Renderer for Consistent Link Styling (Priority: P2)

**Goal**: Every item rendered by `MobileFooterNavRenderer` produces valid BS5 `.nav-item > .nav-link` markup with correct active state, icon support, and button-vs-link branching — regardless of item position.

**Independent Test**: Use `cotton_render_soup` or direct template rendering to assert `.nav-item > .nav-link` structure, `active` class on matching URL, icon presence, and `<button>` vs `<a>` branching for sidebar toggle items.

### Tests for User Story 4 ⚠️ Write FIRST — must FAIL before implementation

- [ ] T017 [P] [US4] Extend `tests/test_renderers.py` with `TestMobileFooterNavRendererOutput` class testing:
  - `test_item_renders_nav_item_nav_link_structure` — rendered HTML contains `.nav-item > .nav-link`
  - `test_active_class_applied_when_url_matches_request_path` — item with matching URL gets `active` on `.nav-link`
  - `test_no_active_class_when_url_does_not_match` — non-matching URL has no `active` class
  - `test_icon_rendered_when_icon_in_extra_context` — icon element present in output
  - `test_sidebar_toggle_renders_as_button_not_anchor` — sidebar toggle item renders `<button>`, not `<a>`
  - `test_regular_item_renders_as_anchor_not_button` — non-toggle item renders `<a>`, not `<button>`
  - `test_sidebar_toggle_has_data_lte_toggle_attribute` — `data-lte-toggle="sidebar"` present on toggle button
  - `test_items_rendered_in_registration_order` — two items registered in order appear in DOM order

### Implementation for User Story 4

No new implementation files required — the renderer (`mvp/renderers.py`, T007) and templates (`mvp/templates/menus/mobile-footer-nav/`, T008/T009) were created in Phase 3. Verify all renderer contract assertions in the new tests pass against the existing implementation.

- [ ] T018 [US4] Validate User Story 4: `python manage.py check` then `pytest tests/test_renderers.py -v` — all renderer output tests must pass GREEN

**Checkpoint**: All user stories (US1–US4) are independently functional and fully tested.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, linting, and full-suite green — Constitution Principles II, V, X.

- [ ] T019 Update `skills/django-mvp/SKILL.md` to document: `MobileFooterMenu` import and `children.append()` usage, `"mobile-footer-nav"` renderer registration in `FLEX_MENUS`, `c-app.mobile-footer-nav` component with `class` attribute, `{% block app.mobile_footer_nav %}` override pattern, and removal of pre-populated sidebar toggle
- [ ] T020 [P] Run `ruff check mvp/menus.py mvp/renderers.py` and fix any style or import-order violations
- [ ] T021 [P] Run `djlint mvp/templates/cotton/app/mobile-footer-nav.html mvp/templates/menus/mobile-footer-nav/wrapper.html mvp/templates/menus/mobile-footer-nav/item.html --check` and fix any template formatting issues
- [ ] T022 Full suite validation: `python manage.py check` then `pytest -m "not e2e"` (unit + component tests) then `pytest -m e2e` (Playwright) — entire test suite must be GREEN with no regressions

**Checkpoint**: Feature complete. All linters pass, all tests green, SKILL.md updated.

---

## Dependency Graph

```
T001 (settings)
    └─→ T012 (US1 validate)

T002 (SCSS partial)
    └─→ T003 (SCSS import)
            └─→ T014 (US2 validate)

T004 (Cotton component tests - RED) ─┐
T005 (renderer unit tests - RED)     │
T006 (MobileFooterMenu)             ─┤
T007 (MobileFooterNavRenderer)      ─┤
T008 (wrapper.html)                 ─┤→ T010 (Cotton component) → T011 (base.html block) → T012 (US1 validate)
T009 (item.html)                    ─┘

T012 (US1 validate)
    └─→ T013 (E2E visibility tests - RED)
            └─→ T014 (US2 validate)
                    └─→ T015 (E2E sidebar toggle tests - RED)
                            └─→ T016 (US3 validate)
                                    └─→ T017 (renderer output tests - RED)
                                            └─→ T018 (US4 validate)
                                                    └─→ T019 (SKILL.md)
                                                    └─→ T020 (ruff)
                                                    └─→ T021 (djlint)
                                                    └─→ T022 (full suite)
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
