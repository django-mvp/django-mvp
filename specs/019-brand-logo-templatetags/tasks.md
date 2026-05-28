# Tasks: Brand Logo & Icon Templatetags

**Feature**: `019-brand-logo-templatetags`
**Input**: [plan.md](plan.md) · [spec.md](spec.md) · [research.md](research.md) · [data-model.md](data-model.md) · [contracts/brand-resolver-api.md](contracts/brand-resolver-api.md) · [quickstart.md](quickstart.md)
**Branch**: `019-brand-logo-templatetags`

---

## Summary

| Metric | Value |
|--------|-------|
| Total tasks | 16 |
| Setup (Phase 1) | 2 — T001, T014 |
| Foundational (Phase 2) | 2 — T002, T015 |
| US1 (Basic SVG logo) | 2 — T003, T004 |
| US2 (Icon URL) | 2 — T005, T006 |
| US3 (Custom resolver) | 1 — T007 |
| US4 (Height forwarding) | 1 — T008 |
| US5 (End-user branding) | 2 — T009, T016 |
| Polish / cross-cutting | 4 — T010–T013 |
| MVP scope | US1 + US2 (stories are tightly coupled) |

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Rename settings constants and wire up the config layer before any tag logic is touched. All user story phases depend on this.

- [X] T001 Rename `MVP_LOGO_URL_FUNC` → `MVP_LOGO_RESOLVER` and `MVP_ICON_URL_FUNC` → `MVP_ICON_RESOLVER` in `mvp/config.py`
- [X] T014 Run `python manage.py check` — confirm no configuration errors after renaming the settings constants

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Update `mvp/templatetags/mvp.py` to use the renamed constants, enforce `height` as required, keep `takes_context=True`, and add `ImproperlyConfigured` + silent-`""` error handling. All user story phases depend on this.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 Update `logo_url` and `icon_url` in `mvp/templatetags/mvp.py`: import renamed constants (`MVP_LOGO_RESOLVER`, `MVP_ICON_RESOLVER`); keep `takes_context=True`; keep `height` as required positional arg; add `ImproperlyConfigured` when setting present but import fails; return `""` on any resolver runtime exception
- [X] T015 Run `python manage.py check` — confirm no configuration errors after updating the templatetags module

**Checkpoint**: Tags callable from templates with the correct signature. Error paths exercisable.

---

## Phase 3: User Story 1 — Basic SVG Logo in Template (Priority: P1) 🎯 MVP

**Goal**: `{% logo_url height=N %}` works zero-config, returning the bundled `brand/logo.svg` for any theme.

**Independent Test**: Render a template with `{% load mvp %}{% logo_url height=40 %}` — returns a non-empty URL ending in `logo.svg`.

### Tests for User Story 1

- [X] T003 [P] [US1] Write pytest tests for `logo_url` default resolver in `tests/test_templatetags.py`:
  - Tag returns URL ending in `logo.svg` for `theme="light"`
  - Tag returns URL ending in `logo.svg` for `theme="dark"` (light fallback — no dark asset bundled)
  - Tag returns URL ending in `logo.svg` with no `theme` argument (default `"light"`)
  - Tag returns URL ending in `logo.svg` for an unrecognised theme value
  - Tag renders without exception when `request` is absent from the template context (`context.get("request")` returns `None`) — SC-006

### Implementation for User Story 1

- [X] T004 [P] [US1] Review `mvp/utils.py` `logo_url` default resolver: confirm it returns `static("brand/logo.svg")` for all themes (light fallback per FR-009/FR-010). Update docstring to document light-fallback behaviour. No logic change required.

**Checkpoint**: US1 fully functional and tested independently. `{% logo_url height=40 %}` works zero-config.

---

## Phase 4: User Story 2 — Icon URL in Template (Priority: P1) 🎯 MVP

**Goal**: `{% icon_url height=N %}` works zero-config, returning light/dark icon based on theme.

**Independent Test**: Render a template with `{% load mvp %}{% icon_url height=32 %}` — returns a non-empty URL. `{% icon_url height=32 theme="dark" %}` returns a different URL than `{% icon_url height=32 theme="light" %}`.

### Tests for User Story 2

- [X] T005 [P] [US2] Add pytest tests for `icon_url` default resolver to `tests/test_templatetags.py`:
  - Tag returns URL ending in `icon_light.svg` for `theme="light"`
  - Tag returns URL ending in `icon_dark.svg` for `theme="dark"`
  - Tag returns URL ending in `icon_light.svg` with no `theme` argument (default)
  - Tag returns URL ending in `icon.svg` for an unrecognised theme value (fallback)
  - Tag renders without exception when `request` is absent from the template context (`context.get("request")` returns `None`) — SC-006

### Implementation for User Story 2

- [X] T006 [P] [US2] Review `mvp/utils.py` `icon_url` default resolver: confirm light/dark/fallback logic is correct per FR-008/FR-009/FR-010. Update docstring. No logic change required.

**Checkpoint**: US2 fully functional and tested. Both `logo_url` and `icon_url` work zero-config. MVP deliverable complete.

---

## Phase 5: User Story 3 — Per-User/Tenant Logo via Custom Resolver (Priority: P2)

**Goal**: A custom callable registered via `MVP_LOGO_RESOLVER` / `MVP_ICON_RESOLVER` in settings is invoked by the tag and its return value is rendered. `ImproperlyConfigured` raised on bad import path; `""` returned silently on runtime exception.

**Independent Test**: Configure `MVP_LOGO_RESOLVER = "tests.fixtures.my_resolver"` in test settings and confirm the tag calls the custom function and renders its return value. Configure a bad path and confirm `ImproperlyConfigured`. Configure a resolver that raises and confirm `""` is rendered.

### Tests for User Story 3

- [X] T007 [P] [US3] Add pytest tests for custom resolver paths to `tests/test_templatetags.py`:
  - `MVP_LOGO_RESOLVER` absent from settings → tag renders default logo URL, no `ImproperlyConfigured` raised — FR-007 / M3
  - Custom `MVP_LOGO_RESOLVER` is called with `(request, height, theme)` — assert callable receives correct args
  - Custom resolver return value is rendered as tag output
  - Custom resolver returning `None` → tag renders as `""`
  - Custom resolver raising an exception → tag renders as `""` (no re-raise)
  - `MVP_LOGO_RESOLVER` set to a non-existent import path → `ImproperlyConfigured` raised on tag call
  - Same four tests for `MVP_ICON_RESOLVER`
  - Tag output is a plain `str`, not a `SafeData` instance — `assert not isinstance(result, SafeData)` — FR-017 / M1
  - Template renders template calling both `logo_url` and `icon_url` four times each without error — SC-004 / M4
  - SC-002 is verified architecturally: switching from default to custom resolver requires only a settings key change; no template-change test is needed because T003/T004 and T007 use the same template syntax

**Checkpoint**: US3 fully functional and tested. Custom resolver path exercised for both tags.

---

## Phase 6: User Story 4 — Height Argument Forwarding (Priority: P3)

**Goal**: The `height` argument value is forwarded unchanged to the resolver callable. Template always supplies it; no default.

**Independent Test**: Write a custom resolver that records the `height` it receives. Call `{% logo_url height=40 %}` and assert the resolver received `40`.

### Tests for User Story 4

- [X] T008 [P] [US4] Add pytest tests for height forwarding to `tests/test_templatetags.py`:
  - `{% logo_url height=40 %}` → resolver receives `height=40`
  - `{% logo_url height=100 theme="dark" %}` → resolver receives `height=100` and `theme="dark"`
  - `{% icon_url height=32 %}` → resolver receives `height=32`

**Checkpoint**: US4 verified. Height value is forwarded to resolver correctly.

---

## Phase 7: User Story 5 — Correct Branding for End Users in Multi-Tenant Apps (Priority: P2)

**Goal**: Browser-level verification that the logo and icon render correctly for end users; and formal pytest-playwright tests that assert behavior-level criteria and run in CI.

**Scope note**: The demo app uses a single default resolver (not a multi-tenant setup), so T009 and T016 verify the acceptance criteria via a **proxy**: correct logo renders for the single configured identity, and light/dark icon src values differ. True multi-tenant verification (Tenant A logo ≠ Tenant B logo) requires a test fixture with a resolver that switches on user identity — this can be injected via `override_settings` in T016 without needing demo app accounts.

### Implementation for User Story 5

- [X] T009 [US5] Using the playwright-cli skill: verify in the running demo app (`http://localhost:8001`) that:
  - A logo `<img>` element with a non-empty `src` attribute is present in the page header / sidebar
  - The light-theme icon `src` and dark-theme icon `src` are different values (confirming theme routing works)
  - No broken image elements (missing or empty `src`) for logo or icon in default configuration
  - No console errors related to image loading

- [X] T016 [US5] Create `tests/test_e2e_brand.py` using pytest-playwright (Constitution VIII — formal CI regression suite):
  - Navigate to demo home page; assert logo `<img>` has a non-empty `src` containing `logo.svg`
  - Inject a multi-tenant resolver via `override_settings(MVP_LOGO_RESOLVER=...)` in a test view; assert that the resolver output changes when the simulated identity changes (verifies US5 AC-1 and AC-2)
  - Assert that a resolver returning `None` or `""` produces no broken `<img>` element (US5 AC-3)
  - Run with `poetry run pytest tests/test_e2e_brand.py --headed` to confirm visually, then `--headless` for CI

**Checkpoint**: US5 verified at two levels — playwright-cli interactive (T009) and pytest-playwright formal suite (T016).

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Documentation update, SKILL.md, and final validation.

- [X] T010 [P] Update `skills/django-mvp/SKILL.md`: add a "Brand Templatetags" section documenting `MVP_LOGO_RESOLVER` / `MVP_ICON_RESOLVER` settings keys, the resolver callable signature `fn(request, height, theme) -> str | None`, and template usage (`{% logo_url height=N %}` / `{% icon_url height=N theme="dark" %}`)

- [X] T011 [P] Run `poetry run pytest tests/test_templatetags.py -v` and confirm all tests pass; run `poetry run ruff check mvp/config.py mvp/utils.py mvp/templatetags/mvp.py tests/test_templatetags.py` and confirm zero linting errors

- [X] T012 [P] Run `poetry run djlint mvp/templates/ --check` to confirm no template linting regressions from any template changes

- [X] T013 Confirm the old settings keys (`MVP_LOGO_URL_FUNC`, `MVP_ICON_URL_FUNC`) are fully removed from `mvp/config.py` and `mvp/templatetags/mvp.py`; grep for any remaining references across the codebase and update them

---

## Dependencies

```
T001 (rename config) ─► T014 (manage.py check)
  └─► T002 (update templatetags) ─► T015 (manage.py check)
        ├─► T003 (US1 tests) ─► T004 (US1 impl review)
        ├─► T005 (US2 tests) ─► T006 (US2 impl review)
        ├─► T007 (US3 tests)         ← parallel with US1/US2
        ├─► T008 (US4 tests)         ← parallel with US1/US2/US3
        ├─► T009 (US5 playwright)    ← needs running server; after T002
        └─► T016 (US5 pytest-playwright) ← parallel with T009; after T002
              └─► T010/T011/T012/T013 (polish — all parallel)
```

**Parallel opportunities per story** (once T002 is done):

- T003 and T005 can run in parallel (different test functions, same file)
- T004 and T006 can run in parallel (same file `utils.py`, non-conflicting functions)
- T007 and T008 test additions are additive — can be written together
- T009 and T016 can run in parallel (interactive verification vs test file creation)
- T010, T011, T012, T013 are all independent

---

## Implementation Strategy

**MVP first**: Complete Phase 1–4 (T001–T006) before starting Phase 5+. At that point:

- Both tags work zero-config with correct default resolvers
- Full pytest coverage for happy paths
- Linting clean

**Then**: Add custom resolver tests (T007), height forwarding tests (T008), Playwright verification (T009), and polish (T010–T013).

**Key constraints** (from spec + research):

- `takes_context=True` — tag reads `request` from context; never a template argument
- `height` — required in template calls, no Python default
- `theme` — keyword arg, defaults to `"light"`
- Return `""` on runtime resolver exception; `ImproperlyConfigured` only on bad import path
- No `mark_safe()`; plain string output
- No caching at tag level
- No new dependencies
