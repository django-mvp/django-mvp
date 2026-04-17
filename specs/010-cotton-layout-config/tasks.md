# Tasks: Cotton App Layout Configuration

**Input**: Design documents from `/specs/010-cotton-layout-config/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Workflow**: Design-First — implement and verify components BEFORE writing tests.
Use Playwright MCP server during implementation to verify layout behaviour against acceptance criteria.
Use `cotton_render_soup` fixture (django-cotton-bs5) for component unit tests.
Every phase touching Django code MUST include `python manage.py check`. Every phase touching UI MUST include a Playwright MCP verification task with specific DOM assertions.

**Organization**: Tasks are grouped by user story. US1 and US2 are both P1; US3 is P2 and can be deferred.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story: US1, US2, or US3
- Exact file paths are included in every task description

---

## Phase 1: Setup (Baseline Audit)

**Purpose**: Understand the current state of existing component templates before refinement begins.

- [ ] T001 Audit `mvp/templates/cotton/app/` — read all existing component templates (index.html, header.html, main.html, menu.html, sidebar/index.html, sidebar/header.html, sidebar/toggle.html, sidebar/menu/*.html, footer.html), consult `.github/skills/cotton-test-components/SKILL.md` and `.github/skills/django-cotton/SKILL.md` before implementation begins, and note gaps against each contract in `specs/010-cotton-layout-config/contracts/`
- [ ] T002 Run `python manage.py check` — confirm zero errors before any changes are made

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Confirm shared infrastructure used by all three stories is present and correct before story work begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T003 Verify AdminLTERenderer is registered as `"adminlte"` in `FLEX_MENUS` settings and is importable — check `mvp/apps.py`, `tests/settings.py`, and any repository-level settings module or `pyproject.toml` configuration that contributes to `FLEX_MENUS`
- [ ] T004 [P] Verify `mvp/menus.py` exports `AppMenu`, `MenuGroup`, `MenuCollapse` with the correct public API per data-model.md Entity 6
- [ ] T005 [P] Verify `mvp/context_processors.py` `mvp_config` context processor supplies brand defaults (`brand_text`, etc.) accessible in sidebar component templates
- [ ] T006 [P] Verify `mvp/templates/mvp/base.html` exposes `{% block app %}` for integrator shell declarations and loads AdminLTE 4 + Bootstrap 5 assets

**Checkpoint**: Foundation confirmed — user story implementation can now begin

---

## Phase 3: User Story 1 — Configure Base Application Shell (Priority: P1) 🎯 MVP

**Goal**: Integrators can declare a full application shell using documented Cotton attributes on the five core components (`<c-app>`, `<c-app.header>`, `<c-app.sidebar>`, `<c-app.main>`, `<c-app.footer>`) and receive a correctly structured, production-ready layout.

**Independent Test**: A developer follows quickstart.md steps 1–7, configures the shell with `fixed-sidebar fixed-header sidebar-collapsible sidebar-expand="lg"`, and confirms the rendered `<body>` carries the expected CSS classes while all four regions appear in the DOM.

### Design & Implementation for User Story 1

> **Implement FIRST. Verify with Playwright MCP. Then write tests.**

- [ ] T007 [P] [US1] Implement `<c-app>` body/wrapper class contract in `mvp/templates/cotton/app/index.html` — `<body>` must carry `.bg-body-tertiary`, `.sidebar-expand-{bp}`, and conditional classes (`layout-fixed`, `fixed-header`, `fixed-footer`, `sidebar-mini`, `sidebar-collapse`) from boolean attributes; `.app-wrapper` carries `.fill` when attribute set
- [ ] T008 [P] [US1] Implement `<c-app.header>` navbar rendering contract in `mvp/templates/cotton/app/header.html` — `<nav>` with `.app-header .navbar .navbar-expand {class}`, `<c-app.sidebar.toggle>` as first left item, left/right/tray slots, optional `border-0` when `border=False`; verify references to `<c-app.header.toggle>` have been migrated to `<c-app.sidebar.toggle>`
- [ ] T009 [P] [US1] Implement `<c-app.sidebar.toggle>` hamburger button in `mvp/templates/cotton/app/sidebar/toggle.html` — `<li class="nav-item">` with `data-lte-toggle="sidebar"` link and accessible ARIA label
- [ ] T010 [US1] Implement `<c-app.sidebar>` aside rendering contract in `mvp/templates/cotton/app/sidebar/index.html` — `<aside class="app-sidebar shadow [class]" data-bs-theme="dark">` with `<c-app.sidebar.header>` branding block (replacing old `<c-app.sidebar.branding>` call), sidebar-wrapper/nav wrapper, default slot falling back to `{% render_menu "AppMenu" renderer="adminlte" %}`, and sidebar overlay div
- [ ] T011 [P] [US1] Implement `<c-app.sidebar.header>` branding/logo block in `mvp/templates/cotton/app/sidebar/header.html` — renders `logo` (full-size), `icon` (collapsed state), `text` (brand label), `link` (brand href); verify `sidebar/index.html` calls `<c-app.sidebar.header>` (not the old `<c-app.sidebar.branding>`)
- [ ] T011a [P] [US1] Implement `<c-app.menu>` standalone app menu component in `mvp/templates/cotton/app/menu.html` — renders `{% render_menu "Site Navigation" renderer="sidebar" %}`; document when to use `<c-app.menu>` vs the sidebar's auto-rendered `AppMenu`
- [ ] T012 [P] [US1] Implement `<c-app.main>` content wrapper in `mvp/templates/cotton/app/main.html` — `<main class="app-main pb-0">` with default slot
- [ ] T013 [P] [US1] Implement `<c-app.footer>` footer rendering contract in `mvp/templates/cotton/app/footer.html` — `<footer class="app-footer [class]">` with default slot (falls back to `text` attribute), right slot wrapped in `.float-end`
- [ ] T014 [US1] Update `demo/templates/base.html` to declare the full c-app shell using all four child components — `<c-app>` wrapping `<c-app.header>`, `<c-app.sidebar>`, `<c-app.main>`, `<c-app.footer>` to enable visual testing
- [ ] T015 [US1] Read `skills/django-mvp/SKILL.md` for current demo-app guidance, then add or update a full-shell demo view in `demo/views.py` (and URL in `demo/urls.py`) with `fixed-sidebar fixed-header sidebar-collapsible sidebar-expand="lg"` attributes configured for visual inspection

### Verification for User Story 1

- [ ] T016 [US1] Verify shell renders using Playwright MCP server — navigate to demo shell page and assert: `<body>` has classes `.bg-body-tertiary` and `.sidebar-expand-lg`; `nav.app-header` is present; `aside.app-sidebar` is present; `main.app-main` is present; `footer.app-footer` is present; toggle button is first nav item in header; MUST NOT merely assert page loads
- [ ] T017 [US1] Manual quickstart walkthrough — follow all 7 steps in `specs/010-cotton-layout-config/quickstart.md` and confirm rendered HTML matches the contract output specs in `specs/010-cotton-layout-config/contracts/`

### Tests for User Story 1 (AFTER design verification)

- [ ] T018 [P] [US1] Contract tests for `<c-app>` attribute→body-class mappings in `tests/test_c_app.py` using `cotton_render_soup` fixture — cover: no attributes (defaults), each boolean attribute individually, `sidebar-expand` variants, combined `sidebar-collapsible + collapsed`, `fill` on wrapper
- [ ] T019 [P] [US1] Contract tests for `<c-app.header>` rendering in `tests/test_c_app.py` using `cotton_render_soup` — cover: default class, custom class, `border=False`, left/right/tray slot content, toggle presence
- [ ] T020 [P] [US1] Contract tests for `<c-app.sidebar>` rendering in `tests/test_c_app.py` using `cotton_render_soup` — cover: default brand text, custom brand attributes, slot override vs auto-menu render, `.app-sidebar.shadow` invariants, overlay div
- [ ] T021 [P] [US1] Contract tests for `<c-app.main>` rendering in `tests/test_c_app.py` using `cotton_render_soup` — cover: `.app-main.pb-0` invariants, default slot content rendered
- [ ] T022 [P] [US1] Contract tests for `<c-app.footer>` rendering in `tests/test_c_app.py` using `cotton_render_soup` — cover: default `text` attribute, slot override, right slot in `.float-end`, custom class attribute
- [ ] T023 [P] [US1] Dedicated component tests for `<c-app.sidebar.toggle>` in `tests/test_c_app.py` using `cotton_render_soup` — cover `data-lte-toggle` attribute, nav-item structure, optional `class` pass-through, and accessible label/ARIA attributes
- [ ] T024 [P] [US1] Dedicated component tests for `<c-app.sidebar.header>` in `tests/test_c_app.py` using `cotton_render_soup` — cover default text, custom `logo`, `icon`, `text`, and `link` attribute output; verify `logo-switch` class applied only when both logo and icon provided
- [ ] T024a [P] [US1] Dedicated component tests for `<c-app.menu>` in `tests/test_c_app.py` using `cotton_render_soup` — cover that `render_menu "Site Navigation"` call is present in rendered output
- [ ] T025 [US1] E2E Playwright test for base shell rendering in `tests/test_e2e_layout.py` — verify initial shell page renders correct body classes, all four layout regions, and functional header toggle before any navigation interactions

### Story 1 Validation (REQUIRED)

- [ ] T026 [US1] Run `python manage.py check` — zero errors MUST be reported
- [ ] T027 [US1] Run `pytest tests/test_c_app.py tests/test_e2e_layout.py` — all pass

**Checkpoint**: User Story 1 fully functional, verified visually, and independently tested. Demo app shows working layout shell.

---

## Phase 4: User Story 2 — Navigate Reliably Within the App Shell (Priority: P1)

**Goal**: End users can navigate through sidebar menus and header controls while header, sidebar, and footer remain stable; the app behaves correctly on narrow viewports.

**Independent Test**: A user loads the demo app, uses sidebar menu items to navigate between pages, uses the sidebar toggle, and confirms layout regions remain stable across pages. On narrow screen, sidebar is accessible via hamburger.

### Design & Implementation for User Story 2

- [ ] T028 [US2] Implement AdminLTE sidebar menu container template in `mvp/templates/cotton/app/sidebar/menu/index.html` — `<ul class="nav sidebar-menu flex-column">` wrapper for all menu items
- [ ] T029 [P] [US2] Implement sidebar menu leaf item template in `mvp/templates/cotton/app/sidebar/menu/item.html` — `<li class="nav-item">` with icon, label, optional badge, active state highlighting
- [ ] T030 [P] [US2] Implement sidebar menu section header/divider template in `mvp/templates/cotton/app/sidebar/menu/group.html` — renders `<li class="nav-header">` style group label
- [ ] T031 [P] [US2] Implement sidebar collapsible group template in `mvp/templates/cotton/app/sidebar/menu/collapse.html` — collapsible `<li>` with Bootstrap collapse toggle, child items rendered recursively, keyboard reachable controls, and appropriate `aria-expanded` state handling
- [ ] T032 [US2] Read `skills/django-mvp/SKILL.md` for current demo-app guidance, then add representative demo menu items to `demo/menus.py` — include at least: a `Dashboard` MenuItem, a `MenuGroup` section header, a `MenuCollapse` with two child `MenuItem` entries, and a standalone leaf item; ensures sidebar renders a real multi-level navigation tree
- [ ] T033 [US2] Add multi-page demo views to `demo/views.py` and corresponding URLs to `demo/urls.py` — at least two navigable pages to test cross-page navigation stability

### Verification for User Story 2

- [ ] T034 [US2] Verify navigation with Playwright MCP server — assert: sidebar renders menu items matching `demo/menus.py` AppMenu; clicking a nav link updates `main.app-main` content; `nav.app-header`, `aside.app-sidebar`, and `footer.app-footer` remain present and unchanged across page transitions; collapsible group expands on click; MUST NOT merely assert page loads
- [ ] T035 [US2] Verify responsive behavior with Playwright MCP server — resize viewport to 640px wide as a focused spot-check, assert hamburger toggle is visible in header, click toggle and confirm sidebar becomes accessible, confirm `main.app-main` content remains readable

### Tests for User Story 2 (AFTER design verification)

- [ ] T036 [P] [US2] Add AdminLTE menu rendering tests to `tests/test_c_app.py` — cover: `AppMenu` with `MenuItem`, `MenuGroup`, `MenuCollapse`; rendered HTML has correct classes and link hrefs; nested items appear under collapse parent
- [ ] T037 [P] [US2] Dedicated component tests for `<c-app.sidebar.menu>` in `tests/test_c_app_sidebar_menu.py` using `cotton_render_soup` — cover wrapper classes, child rendering, and empty/menu-present states
- [ ] T038 [P] [US2] Dedicated component tests for `<c-app.sidebar.menu.item>` in `tests/test_c_app_sidebar_menu_item.py` using `cotton_render_soup` — cover icon, label, badge, href, and active-state output
- [ ] T039 [P] [US2] Dedicated component tests for `<c-app.sidebar.menu.group>` in `tests/test_c_app_sidebar_menu_group.py` using `cotton_render_soup` — cover section header rendering and expected `.nav-header` output
- [ ] T040 [P] [US2] Dedicated component tests for `<c-app.sidebar.menu.collapse>` in `tests/test_c_app_sidebar_menu_collapse.py` using `cotton_render_soup` — cover nested child rendering, expanded/collapsed state markup, and ARIA attributes
- [ ] T041 [US2] E2E Playwright test for sidebar navigation flow in `tests/test_e2e_layout.py` — test: load page, click sidebar item, verify content change, verify layout regions stable, verify collapsible toggle works across a Bootstrap breakpoint matrix (`sm`, `md`, `lg`) rather than a single viewport only

### Story 2 Validation (REQUIRED)

- [ ] T042 [US2] Run `python manage.py check` — zero errors MUST be reported
- [ ] T043 [US2] Run `pytest tests/test_c_app.py tests/test_c_app_sidebar_menu.py tests/test_c_app_sidebar_menu_item.py tests/test_c_app_sidebar_menu_group.py tests/test_c_app_sidebar_menu_collapse.py tests/test_e2e_layout.py` — all pass

**Checkpoint**: User Stories 1 and 2 are both independently functional and tested. App is navigable.

---

## Phase 5: User Story 3 — Apply Advanced Layout Modes Safely (Priority: P2)

**Goal**: Developers can enable advanced layout modes (fixed-sidebar, fixed-header, fixed-footer, fill, collapsed sidebar) via attributes, with documented compatibility rules and configuration presets.

**Independent Test**: A developer applies each layout preset from quickstart.md on a fresh demo page, inspects the rendered HTML, and confirms body classes match the preset specification. An unsupported combo warning is documented in `docs/layout-configuration.md`.

### Design & Implementation for User Story 3

- [ ] T044 [P] [US3] Document supported attribute combinations, incompatible pairs, and fallback behaviour in `docs/layout-configuration.md` — write the compatibility/rules section only, including body-class mapping, valid values, defaults, known incompatibilities, and the statement that invalid attribute handling is delegated to django-cotton
- [ ] T045 [P] [US3] Add preset configuration examples to `specs/010-cotton-layout-config/quickstart.md` Section 5 — three explicit presets: "Fixed sidebar + mini mode + starts collapsed", "Fixed header + footer + fill viewport", "Minimal (no fixed elements)"
- [ ] T046 [US3] Read `skills/django-mvp/SKILL.md` for current demo-app guidance, then add three preset demo views to `demo/views.py` and `demo/urls.py` for each layout preset above, accessible via demo sidebar menu, to enable Playwright verification of each combination
- [ ] T047 [US3] Treat the `collapsed` → `.sidebar-collapse` guard as a core `<c-app>` correctness invariant while implementing `mvp/templates/cotton/app/index.html`; verify and correct it here only if T007 left the invariant incomplete

### Verification for User Story 3

- [ ] T048 [US3] Verify advanced layout combinations with Playwright MCP server — test all three preset pages: (1) `fixed-sidebar sidebar-collapsible collapsed` → body has `.layout-fixed .sidebar-mini .sidebar-collapse`; (2) `fixed-header fixed-footer fill` → body has `.fixed-header .fixed-footer`, `.app-wrapper` has `.fill`; (3) minimal `<c-app>` → body has only `.bg-body-tertiary .sidebar-expand-lg`
- [ ] T049 [US3] Verify `collapsed` guard: render `<c-app collapsed>` (without `sidebar-collapsible`) using Playwright or cotton_render_soup — confirm body does NOT have `.sidebar-collapse`

### Tests for User Story 3 (AFTER design verification)

- [ ] T050 [P] [US3] Expand `<c-app>` advanced attribute tests in `tests/test_c_app.py` — cover all three presets, `collapsed`-without-`sidebar-collapsible` guard, `sidebar-expand` breakpoint variants (`sm`, `md`, `lg`, `xl`, `xxl`), `fill` class on `.app-wrapper`
- [ ] T051 [US3] E2E Playwright test for advanced layout mode rendering in `tests/test_e2e_layout.py` — verify each preset page renders with correct body classes and all four layout regions intact

### Story 3 Validation (REQUIRED)

- [ ] T052 [US3] Run `python manage.py check` — zero errors MUST be reported
- [ ] T053 [US3] Run `pytest tests/test_c_app.py tests/test_e2e_layout.py` — all pass

**Checkpoint**: All three user stories are independently functional, verified, and tested.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation completeness, public API discoverability, lint hygiene, and regression guard.

- [ ] T054 [P] Update `docs/layout-configuration.md` with the complete per-component attribute reference for all five components — extend the document after T044's compatibility/rules section; include attribute name, type, default, effect, slot table, rendered output example, and invariants per contract
- [ ] T055 [P] Update `docs/layout-data-models-api-contracts.md` with the component relationship diagram from `specs/010-cotton-layout-config/data-model.md` (Entity 1–6 relationship tree)
- [ ] T056 [P] Update `skills/django-mvp/SKILL.md` with `<c-app>` shell integration section — cover how to declare the shell, all attribute options, menu registration pattern, and link to quickstart
- [ ] T057 [P] Run `ruff check mvp/ demo/` and `ruff format --check mvp/ demo/` — zero violations; fix any reported issues
- [ ] T058 [P] Run `djlint mvp/templates/ demo/templates/ --check` — zero violations; fix any reported issues
- [ ] T059 Verify accessibility with Playwright MCP server and targeted component tests in `tests/test_c_app.py`, `tests/test_c_app_sidebar_menu_collapse.py`, and `tests/test_e2e_layout.py` — assert keyboard reachability and relevant ARIA attributes on the header toggle, sidebar menu collapse controls, and other interactive shell navigation elements
- [ ] T060 Validate `specs/010-cotton-layout-config/quickstart.md` end-to-end as a final regression pass by following all seven steps in the demo app after all user stories are complete — confirm produced HTML matches all contract invariants documented in `specs/010-cotton-layout-config/contracts/`
- [ ] T061 Run full test suite `pytest` — all pass with zero regressions introduced by this feature

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories
- **Phase 3 (US1)**: Depends on Phase 2 completion — 🎯 MVP deliverable
- **Phase 4 (US2)**: Depends on Phase 2 completion, integrates with US1 components
- **Phase 5 (US3)**: Depends on Phase 2 completion, extends US1 components
- **Phase 6 (Polish)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Core shell — can start after Phase 2; no cross-story dependencies
- **User Story 2 (P1)**: Navigation — can start after Phase 2; uses sidebar component from US1 (T010); T028–T031 can start in parallel with US1 template work since they target different files
- **User Story 3 (P2)**: Advanced modes — can start after Phase 2; extends `<c-app>` template (T007/T047 are the same file — sequence after T007 completes)

### Within Each User Story

- Implementation first, Playwright MCP verification second, pytest tests third
- Template components before demo integration
- Demo integration before Playwright verification
- Playwright verification before test authoring

---

## Parallel Opportunities

### All stories (after Phase 2):

```
US1 templates (T007–T013) run in parallel — different template files
US2 menu templates (T028–T031) run in parallel — different template files
US3 docs (T044–T045) run in parallel with US1/US2 implementation
```

### Within User Story 1:

```
# These can all run in parallel (different files):
T007   mvp/templates/cotton/app/index.html
T008   mvp/templates/cotton/app/header.html
T009   mvp/templates/cotton/app/sidebar/toggle.html
T011   mvp/templates/cotton/app/sidebar/header.html
T011a  mvp/templates/cotton/app/menu.html
T012   mvp/templates/cotton/app/main.html
T013   mvp/templates/cotton/app/footer.html
# T010 (sidebar/index.html) must wait for T009 (toggle) if toggle is included by sidebar
```

### Within User Story 1 tests:

```
# These US1 test scopes are consolidated in one module:
T018   tests/test_c_app.py  (<c-app>)
T019   tests/test_c_app.py  (<c-app.header>)
T020   tests/test_c_app.py  (<c-app.sidebar>)
T021   tests/test_c_app.py  (<c-app.main>)
T022   tests/test_c_app.py  (<c-app.footer>)
T023   tests/test_c_app.py  (<c-app.sidebar.toggle>)
T024   tests/test_c_app.py  (<c-app.sidebar.header>)
T024a  tests/test_c_app.py  (<c-app.menu>)
# T025 (tests/test_e2e_layout.py) depends on demo integration tasks completing first
```

### Within Phase 6:

```
# All polish tasks run in parallel (different files):
T054  docs/layout-configuration.md
T055  docs/layout-data-models-api-contracts.md
T056  skills/django-mvp/SKILL.md
T057  ruff lint + format check
T058  djlint lint
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup audit (T001–T002)
2. Complete Phase 2: Foundation verification (T003–T006)
3. Complete Phase 3: User Story 1 — full shell components + tests (T007–T027)
4. **STOP and VALIDATE**: Shell works end-to-end, follows quickstart guide
5. Complete Phase 4: User Story 2 — navigation + E2E tests (T028–T043)
6. Deploy/demo — integrators can follow quickstart and build a navigable app shell

### Incremental Delivery

1. Phase 1 + 2 → Baseline confirmed
2. Phase 3 (US1) → Working shell, independently tested → **MVP**
3. Phase 4 (US2) → Navigation functional, E2E tested → Demo-ready
4. Phase 5 (US3) → Advanced modes documented and tested → Full feature
5. Phase 6 (Polish) → Docs complete, accessibility verified, lint/format clean, no regressions → Release-ready

### Parallel Team Strategy

With two developers:

1. Both complete Phases 1 + 2 together
2. Developer A: US1 template components (T007–T013) and tests (T018–T025)
3. Developer B: US2 menu templates (T028–T031) and demo menu data (T032–T033) in parallel
4. Merge and run integration verification T034–T043
5. One developer takes US3 while other starts Phase 6 polish

---

## Notes

- `[P]` tasks operate on different files and have no intra-phase dependencies
- `[Story]` labels map each task to a user story for traceability and independent delivery
- All Playwright verification tasks MUST assert specific DOM classes/elements — asserting "page loads" is insufficient
- `cotton_render_soup` is the preferred fixture for component DOM assertion tests (see cotton-test-components skill)
- Component attribute names are kebab-case in template declarations; they are normalized to snake_case inside component templates by django-cotton
- The `collapsed` → `.sidebar-collapse` guard is a correctness invariant per contract and research.md and should already be satisfied by the core `<c-app>` implementation; the US3 task only exists to verify and correct it if needed
- Tests in `tests/test_e2e_layout.py` accumulate across US2 and US3 — coordinate to avoid duplicate test function names
- T017 is the first-pass quickstart validation after US1 is complete; T060 is the final full-feature regression validation after all user stories are integrated
- The hamburger toggle (`<c-app.sidebar.toggle>`) is defined in `sidebar/toggle.html` but rendered inside `<c-app.header>` — file location and render location differ by design
- `<c-app.sidebar.header>` uses attribute names `text`, `icon`, `logo`, `link` (not the old `brand-*` prefix); `sidebar/index.html` must be updated during T010 to call `<c-app.sidebar.header>` (not `<c-app.sidebar.branding>`)
- `<c-app.menu>` renders "Site Navigation" (a separate menu from `AppMenu`); document the distinction in quickstart and docs
- Commit after each phase checkpoint to support incremental review
