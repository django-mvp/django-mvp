# Tasks: Vendored Theme Variable Overrides

**Input**: Design documents from `/specs/018-vendor-adminlte-scss/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/public-api.md, quickstart.md
**Propagated**: 2026-05-26 — Updated from spec.md refinement: T040, T041, T042 changed from Playwright MCP server to playwright-cli skill

**Tests**: Include targeted pytest and Playwright verification tasks because this feature changes user-visible compiled CSS and build behavior.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare repository structure for vendored AdminLTE source management and validation.

- [ ] T001 Create vendored source root directory marker in mvp/static/adminlte/README.md
- [ ] T002 Create vendored SCSS destination directory marker in mvp/static/adminlte/scss/.gitkeep
- [ ] T003 [P] Create asset pipeline contract test module scaffold in tests/test_static_assets.py
- [ ] T004 [P] Create theme UI verification test module scaffold in tests/test_ui_theme.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement core refresh and compilation plumbing that blocks all user stories.

**⚠️ CRITICAL**: No user story work should begin until this phase is complete.

- [ ] T005 Implement shared vendor path constants and helper functions in tasks.py
- [ ] T006 Implement Invoke task skeleton for AdminLTE SCSS refresh in tasks.py
- [ ] T007 Configure vendored import include path contract comments in mvp/static/scss/mvp.scss
- [ ] T008 Add foundational validation for compiler configuration in tests/test_static_assets.py
- [ ] T009 Run Django system checks for foundational changes via `poetry run python manage.py check --settings=tests.settings`
- [ ] T010 Run foundational pytest coverage via poetry run pytest tests/test_static_assets.py -q

**Checkpoint**: Foundation complete; user stories can proceed.

---

## Phase 3: User Story 1 - Configure App Theme Quickly (Priority: P1) 🎯 MVP

**Goal**: Downstream developers can override theme tokens using one `_mvp_variables.scss` file.

**Independent Test**: Edit `_mvp_variables.scss`, build through compressor/libsass, and confirm rendered styles change without editing vendor sources.

### Tests for User Story 1

- [ ] T011 [P] [US1] Add Sass load-order unit assertions in tests/test_static_assets.py
- [ ] T012 [P] [US1] Add default-fallback behavior assertions in tests/test_static_assets.py
- [ ] T013 [P] [US1] Add Playwright visual theme override verification in tests/test_ui_theme.py

### Implementation for User Story 1

- [ ] T014 [US1] Create downstream override entrypoint in mvp/static/scss/_mvp_variables.scss
- [ ] T015 [US1] Update SCSS import order to load _mvp_variables before vendor defaults in mvp/static/scss/mvp.scss
- [ ] T016 [US1] Wire vendored AdminLTE import roots into main stylesheet in mvp/static/scss/mvp.scss
- [ ] T017 [US1] Add inline override usage guidance comments in mvp/static/scss/_mvp_variables.scss
- [ ] T040 [US1] Use playwright-cli skill to open the themed pages, verify variable override changes are visually reflected in the browser, and capture a screenshot as evidence
- [ ] T043 [P] [US1] Add failing test in tests/test_static_assets.py asserting invalid SCSS override errors include the problematic variable name
- [ ] T044 [US1] Implement actionable diagnostic output for invalid override values in build/refresh path in tasks.py
- [ ] T045 [US1] Document invalid-override troubleshooting steps in specs/018-vendor-adminlte-scss/quickstart.md
- [ ] T046 [US1] Run diagnostics pytest coverage via `poetry run pytest tests/test_static_assets.py -q`
- [ ] T018 [US1] Run Django system checks for US1 via `poetry run python manage.py check --settings=tests.settings`
- [ ] T019 [US1] Run US1 pytest suite via `poetry run pytest tests/test_static_assets.py tests/test_ui_theme.py -q`

**Checkpoint**: User Story 1 is functional and independently testable.

---

## Phase 4: User Story 2 - Keep Upstream Style Updates Safe (Priority: P2)

**Goal**: Maintainers can refresh AdminLTE SCSS safely with lockfile pinning and full directory replacement.

**Independent Test**: Run Invoke refresh task and verify latest package installation, lockfile pinning, full directory replace, and successful recompilation.

### Tests for User Story 2

- [ ] T020 [P] [US2] Add Invoke refresh command behavior tests in tests/test_static_assets.py
- [ ] T021 [P] [US2] Add stale-file-removal regression tests for vendor refresh in tests/test_static_assets.py
- [ ] T022 [P] [US2] Add lockfile pinning assertions for npm refresh workflow in tests/test_static_assets.py

### Implementation for User Story 2

- [ ] T023 [US2] Implement npm latest AdminLTE install flow in Invoke refresh task in tasks.py
- [ ] T024 [US2] Implement delete-then-copy vendor directory refresh flow targeting mvp/static/adminlte/scss/ in tasks.py
- [ ] T025 [US2] Implement lockfile-preserving refresh behavior documentation output in tasks.py
- [ ] T026 [US2] Update vendored-source ownership note for maintainers in mvp/static/adminlte/README.md
- [ ] T041 [US2] Use playwright-cli skill to open core themed pages after running the vendor refresh task and confirm the UI renders correctly with no visual regression
- [ ] T048 [US2] Add SC-003 refresh repeatability sampling protocol to specs/018-vendor-adminlte-scss/contracts/public-api.md
- [ ] T027 [US2] Run Django system checks for US2 via `poetry run python manage.py check --settings=tests.settings`
- [ ] T028 [US2] Run US2 pytest suite via `poetry run pytest tests/test_static_assets.py -q`

**Checkpoint**: User Story 2 is functional and independently testable.

---

## Phase 5: User Story 3 - Onboard New Teams Faster (Priority: P3)

**Goal**: New teams can apply branding quickly with clear docs and minimal errors.

**Independent Test**: A new contributor follows docs to perform one override and one vendor refresh without editing vendored SCSS manually.

### Tests for User Story 3

- [ ] T029 [P] [US3] Add quickstart command-path validation test in tests/test_smoke.py
- [ ] T030 [P] [US3] Add documentation snippet consistency test for override path in tests/test_smoke.py

### Implementation for User Story 3

- [ ] T031 [US3] Update theming workflow documentation for override usage in specs/018-vendor-adminlte-scss/quickstart.md
- [ ] T032 [US3] Update public theming contract examples in specs/018-vendor-adminlte-scss/contracts/public-api.md
- [ ] T033 [US3] Add maintainer-facing vendor refresh usage section in README.md
- [ ] T047 [US3] Add SC-002 first-time developer timing protocol to specs/018-vendor-adminlte-scss/quickstart.md
- [ ] T049 [US3] Add recording checklist for timing and refresh protocol runs to specs/018-vendor-adminlte-scss/quickstart.md
- [ ] T050 [US3] Execute one baseline protocol run and record results in specs/018-vendor-adminlte-scss/quickstart.md
- [ ] T034 [US3] Run Django system checks for US3 via `poetry run python manage.py check --settings=tests.settings`
- [ ] T035 [US3] Run US3 pytest suite via `poetry run pytest tests/test_smoke.py -q`

**Checkpoint**: User Story 3 is functional and independently testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, cleanup, and cross-story hardening.

- [ ] T036 [P] Verify quickstart end-to-end commands against current repository state in specs/018-vendor-adminlte-scss/quickstart.md
- [ ] T037 [P] Run full targeted test sweep across affected suites via poetry run pytest tests/test_static_assets.py tests/test_ui_theme.py tests/test_smoke.py -q
- [ ] T038 Run full Django system checks post-integration via `poetry run python manage.py check --settings=tests.settings`
- [ ] T039 [P] Update release notes for vendored SCSS workflow in CHANGELOG.md
- [ ] T042 [P] Run final playwright-cli acceptance pass on primary themed pages, capture screenshots, and record acceptance evidence in specs/018-vendor-adminlte-scss/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies.
- **Phase 2 (Foundational)**: Depends on Phase 1; blocks all user stories.
- **Phase 3 (US1)**: Depends on Phase 2.
- **Phase 4 (US2)**: Depends on Phase 2 and can run in parallel with US1 after foundation, but recommended after US1 for easier validation.
- **Phase 5 (US3)**: Depends on US1 and US2 implementation details to document final behavior accurately.
- **Phase 6 (Polish)**: Depends on completion of all user stories.

### User Story Dependencies

- **US1 (P1)**: No dependency on other stories after foundation.
- **US2 (P2)**: No hard dependency on US1, but shares asset pipeline files.
- **US3 (P3)**: Depends on finalized behavior from US1 and US2 for accurate documentation.

### Within Each User Story

- Tests first (TDD style): write assertions, confirm failures, then implement.
- Asset/path changes before behavioral verification.
- Run `poetry run python manage.py check --settings=tests.settings` and targeted pytest before story checkpoint.

### Parallel Opportunities

- Phase 1 tasks `T003` and `T004` can run in parallel.
- In US1, `T011`, `T012`, `T013`, and `T043` can run in parallel.
- In US2, `T020`, `T021`, and `T022` can run in parallel.
- In US3, `T029` and `T030` can run in parallel.
- In Polish, `T036`, `T037`, `T039`, and `T042` can run in parallel.

---

## Parallel Example: User Story 2

```bash
# Parallelize test-first tasks:
Task T020: Add Invoke refresh command behavior tests in tests/test_static_assets.py
Task T021: Add stale-file-removal regression tests in tests/test_static_assets.py
Task T022: Add lockfile pinning assertions in tests/test_static_assets.py

# Then implement refresh behavior:
Task T023: npm latest install flow in tasks.py
Task T024: delete-then-copy vendor refresh flow in tasks.py
Task T025: lockfile-preserving refresh output in tasks.py
```

---

## Implementation Strategy

### MVP First (US1)

1. Finish Setup and Foundational phases.
2. Deliver US1 override entrypoint and import ordering.
3. Validate with system checks, targeted pytest, and browser verification.

### Incremental Delivery

1. Deliver US1 to unlock immediate downstream customization value.
2. Deliver US2 for maintainable upstream refresh workflow.
3. Deliver US3 documentation and onboarding polish.
4. Run cross-cutting validation in Phase 6.

### Team Parallelization

1. One engineer completes foundation (`T005`-`T010`).
2. After foundation: one engineer handles US1, another handles US2.
3. US3 documentation starts after US1/US2 behavior stabilizes.

---

## Notes

- All tasks use the required checklist format.
- `[P]` marks tasks that are parallelizable with no blocking file dependencies.
- `[US1]`, `[US2]`, and `[US3]` labels map directly to spec user stories.
- Invoke-based refresh behavior is explicitly captured in `tasks.py` tasks.
