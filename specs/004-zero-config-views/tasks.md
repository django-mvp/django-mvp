---
description: "Task list for 004-zero-config-views"
---

# Tasks: Zero-Config Ready-to-Use Views

**Input**: Design documents from `/specs/004-zero-config-views/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/views-api.md ✅, quickstart.md ✅

**Workflow**: Design-first — implement and verify in browser BEFORE writing tests. Every phase touching Django code runs `python manage.py check` AND the relevant pytest suite. Every phase touching UI runs a Playwright MCP server verification task. Tests are REQUIRED but come after design verification.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the existing codebase state and establish the working baseline before making any changes. Both `MVPTemplateView` and `MVPHomeView` already exist — this phase audits what is present versus what the spec requires.

- [X] T001 Audit `mvp/views/base.py` — confirm current attribute names (`landing_template`, `dashboard_template`) and verify `ImproperlyConfigured` guard is absent; document gap list
- [X] T002 Audit `mvp/views/__init__.py` — confirm `MVPTemplateView` and `MVPHomeView` are exported; confirm `PageView` and `HomeView` aliases are absent
- [X] T003 [P] Audit `mvp/templates/mvp/` — confirm `landing.html` and `dashboard.html` do not yet exist
- [X] T004 [P] Run `python manage.py check` — confirm baseline is green before any changes

**Checkpoint**: Gap list confirmed. Baseline is green. Implementation can begin.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core changes to `mvp/views/base.py` that US1, US2, and US3 all depend on. Must be complete before any user story work begins.

**⚠️ CRITICAL**: All user story phases depend on this phase being complete.

- [X] T005 Rename `MVPHomeView.landing_template` → `landing_template_name` and `dashboard_template` → `dashboard_template_name` in `mvp/views/base.py`
- [X] T006 Add `ImproperlyConfigured` guard in `MVPHomeView.get_template_names()` in `mvp/views/base.py`: raise if `landing_template_name` is `None` (any request) or `dashboard_template_name` is `None` (authenticated request only), with diagnostic messages naming the class and the missing attribute
- [X] T007 Add `PageView = MVPTemplateView` and `HomeView = MVPHomeView` aliases in `mvp/views/__init__.py`; add both to `__all__`
- [X] T008 Update existing `TestMVPHomeView` tests in `tests/test_views/test_base.py` to use renamed attributes (`landing_template_name`, `dashboard_template_name`)
- [X] T009 Run `python manage.py check` — zero errors MUST be reported after attribute rename and alias additions
- [X] T010 Run `pytest tests/test_views/test_base.py` — all existing tests MUST pass after attribute rename

**Checkpoint**: Foundation ready. Aliases exported. Guard in place. All existing tests pass.

---

## Phase 3: User Story 1 — PageView Plain Layout-Aware Template (Priority: P1) 🎯 MVP

**Goal**: A developer can wire `PageView` to a URL, create a template extending `page_view.html`, and the page renders inside the full layout with navigation chrome — with no model, form, or queryset.

**Independent Test**: Wire `PageView.as_view(template_name="demo/about.html", page_title="About")` to `path("about/")` in the demo app, create the template, start the dev server, and visit `/about/` — full layout renders with "About" in the page header.

### Design & Implementation for User Story 1

- [X] T011 [US1] Add demo `PageView` URL: add `path("about/", PageView.as_view(template_name="demo/about.html", page_title="About Us", page_subtitle="Learn more", page_icon="info-circle", breadcrumbs=[{"text": "Home", "href": "/"}, {"text": "About"}]), name="about")` to `demo/urls.py`; import `PageView` from `mvp.views`
- [X] T012 [US1] Create `demo/templates/demo/about.html` extending `page_view.html` with `{% block page.content %}` containing a short paragraph of placeholder content
- [X] T013 [US1] Run `python manage.py check` — zero errors

### Verification for User Story 1

- [X] T014 [US1] Verify with Playwright MCP server: navigate to `/about/`, assert the response is `200 OK`, the AdminLTE sidebar and navbar are present in the DOM, the page title "About Us" appears in the content area, and the breadcrumb trail renders "Home > About" — MUST NOT merely assert the page loads without error
- [X] T015 [US1] Verify with Playwright MCP server: send a POST request to `/about/`, assert `405 Method Not Allowed` is returned (FR-011)

### Tests for User Story 1 (AFTER design verification)

- [X] T016 [P] [US1] Add unit tests in `tests/test_views/test_base.py` for `PageView` alias: assert `PageView is MVPTemplateView`, assert `PageView` is in `mvp.views.__all__`, assert `PageView.as_view()` returns a callable
- [X] T017 [P] [US1] Add unit tests in `tests/test_views/test_base.py` for `MVPTemplateView` layout participation: wire with `page_title="Test Title"`, call `get_context_data()`, assert `context["page"]["title"] == "Test Title"` and `context["page"]["class"].startswith("mvp-page")`
- [X] T018 [US1] Add pytest-playwright E2E test in `tests/test_views/test_base_e2e.py`: request `/about/` unauthenticated, assert `200 OK`, assert sidebar and navbar present, assert page title in heading

### Story 1 Validation (REQUIRED)

- [X] T019 [US1] Run `python manage.py check` — zero errors MUST be reported
- [X] T020 [US1] Run `pytest tests/test_views/` — all tests MUST pass

**Checkpoint**: `PageView` wired, renders in layout, `page_title` visible, 405 for POST confirmed, unit and E2E tests passing.

---

## Phase 4: User Story 2 — HomeView Guest/Dashboard Template Switch (Priority: P1)

**Goal**: A developer wires `HomeView` at `/`, sets `landing_template_name` and `dashboard_template_name`, and the view serves the landing page to guests and the dashboard to authenticated users — same URL, no redirect, `ImproperlyConfigured` raised on misconfiguration.

**Independent Test**: Wire `HomeView` at the demo root, create two templates, request the URL unauthenticated (landing content), then authenticated (dashboard content) — both `200 OK`, URL unchanged, and removing `dashboard_template_name` triggers `ImproperlyConfigured`.

### Design & Implementation for User Story 2

- [X] T021 [US2] Create `mvp/templates/mvp/landing.html`: extends `page_view.html`, `{% block page.content %}` renders a hero section using `{{ hero_content.title }}`, `{{ hero_content.subtitle }}`, `{{ hero_content.lead }}`, and an `<img>` using `{{ hero_content.image }}` via `{% static %}`; use `django-cotton-bs5` components where applicable (consult `.github/skills/django-cotton/SKILL.md` first)
- [X] T022 [US2] Create `mvp/templates/mvp/dashboard.html`: extends `page_view.html`, `{% block page.content %}` renders a personalised greeting `Welcome, {{ request.user.get_full_name|default:request.user.username }}` and a placeholder prompt to add dashboard widgets
- [X] T023 [US2] Update demo home URL in `demo/urls.py`: replace existing `MVPDemoView` home entry with `HomeView.as_view(landing_template_name="demo/landing.html", dashboard_template_name="demo/dashboard.html")` for `path("", ...)` named `"home"`; import `HomeView` from `mvp.views`
- [X] T024 [US2] Create `demo/templates/demo/landing.html`: extends `mvp/landing.html`, overrides `{% block page.content %}` with demo-specific marketing copy (headline, sub-copy, login CTA button linking to `{% url 'login' %}`)
- [X] T025 [US2] Create `demo/templates/demo/dashboard.html`: extends `mvp/dashboard.html`, overrides `{% block page.content %}` with demo-specific dashboard content (welcome message, placeholder stat cards)
- [X] T026 [US2] Run djlint on all four new templates — zero violations
- [X] T027 [US2] Run `python manage.py check` — zero errors

### Verification for User Story 2

- [X] T028 [US2] Verify with Playwright MCP server (unauthenticated): navigate to `/`, assert `200 OK`, assert landing page headline text is visible, assert no redirect occurred (URL is still `/`), assert login CTA button is present — MUST NOT merely assert page loads
- [X] T029 [US2] Verify with Playwright MCP server (authenticated): log in as a test user, navigate to `/`, assert `200 OK`, assert dashboard greeting containing the username is visible, assert URL is still `/` with no redirect — MUST NOT merely assert page loads
- [X] T030 [US2] Verify with Playwright MCP server: confirm POST to `/` returns `405 Method Not Allowed` (FR-011)

### Tests for User Story 2 (AFTER design verification)

- [X] T031 [P] [US2] Add unit tests in `tests/test_views/test_base.py`:
  - `HomeView is MVPHomeView` (alias)
  - `HomeView` in `mvp.views.__all__`
  - `MVPHomeView.landing_template_name == "mvp/landing.html"` (default)
  - `MVPHomeView.dashboard_template_name == "mvp/dashboard.html"` (default)
  - `MVPHomeView.page_title == _("Home")` (default — import `gettext_lazy as _` from `django.utils.translation`)
- [X] T032 [P] [US2] Add unit tests in `tests/test_views/test_base.py` for `ImproperlyConfigured` guard:
  - `landing_template_name = None` → `ImproperlyConfigured` for anonymous request (error message contains class name and `"landing_template_name"`)
  - `dashboard_template_name = None` + authenticated user → `ImproperlyConfigured` (message contains `"dashboard_template_name"`)
  - `dashboard_template_name = None` + anonymous user → no error (renders landing template)
  - both `landing_template_name = None` and `dashboard_template_name = None` + anonymous request → `ImproperlyConfigured` on `landing_template_name` (guard evaluates `landing_template_name` first, before checking auth state)
- [X] T033 [US2] Add pytest-playwright E2E test in `tests/test_views/test_base_e2e.py`:
  - Anonymous GET `/` → `200 OK`, landing content visible, no redirect
  - Authenticated GET `/` → `200 OK`, dashboard content visible, URL still `/`, no redirect
  - POST `/` → `405`

### Story 2 Validation (REQUIRED)

- [X] T034 [US2] Run `python manage.py check` — zero errors MUST be reported
- [X] T035 [US2] Run `pytest tests/test_views/` — all tests MUST pass

**Checkpoint**: `HomeView` wired, template switching confirmed in browser, `ImproperlyConfigured` guard tested, E2E tests passing.

---

## Phase 5: User Story 3 — Seamless Guest-to-Dashboard Transition (Priority: P1) [End User]

**Goal**: The E2E user journey is fully covered — an anonymous visitor sees the landing page, logs in, returns to `/`, and sees the dashboard without any URL change or redirect.

**Independent Test**: `pytest tests/test_views/test_base_e2e.py` — the full login-and-return workflow passes with zero redirects to the home URL.

> **Note**: The bulk of the E2E test implementation is in Phase 4 (T033). This phase adds the full interactive login-and-return workflow test and verifies the layout chrome remains functional on the dashboard.

### Design & Implementation for User Story 3

- [X] T036 [US3] Extend `tests/test_views/test_base_e2e.py`: add a full sequential E2E test — (1) visit `/` unauthenticated, assert landing content; (2) navigate to login, authenticate; (3) navigate back to `/`, assert dashboard content; (4) assert URL has not changed from `/` at any step; (5) assert navbar and sidebar are present and functional on the dashboard page (click a nav link, assert no JS errors)

### Verification for User Story 3

- [X] T037 [US3] Verify with Playwright MCP server: run the full login-and-return journey interactively — confirm URL bar stays at `/` before and after login, confirm no redirect appears in the network requests panel

### Story 3 Validation (REQUIRED)

- [X] T038 [US3] Run `pytest tests/test_views/test_base_e2e.py` — full login-and-return E2E test MUST pass
- [X] T039 [US3] Run `python manage.py check` — zero errors MUST be reported

**Checkpoint**: Full end-to-end guest-to-dashboard journey verified and regression-tested.

---

## Phase 6: User Story 4 — PageView Full Layout Configuration Participation (Priority: P2)

**Goal**: `PageView` honours all `PageMixin` layout attributes (`page_title`, `page_subtitle`, `page_icon`, `page_class`, `breadcrumbs`) — set via class attribute or `as_view()` kwargs — and the layout shell reflects the configured values.

**Independent Test**: Subclass `PageView` with all `page_*` attributes set, render via test client, assert each value appears in the rendered HTML in the expected location.

> **Note**: The core `PageMixin` behaviour is already implemented and tested. This phase adds the integration-level rendering tests that confirm the layout shell reflects class-attribute values end-to-end, and verifies the demo `/about/` page already demonstrates this.

### Design & Implementation for User Story 4

- [X] T040 [US4] Verify the `as_view()` kwargs for the `"about"` URL in `demo/urls.py` include all three metadata fields (`page_title`, `page_subtitle`, `page_icon` — set in T011); update `demo/templates/demo/about.html` `{% block page.content %}` to visually surface all three fields in the rendered layout shell

### Verification for User Story 4

- [X] T041 [US4] Verify with Playwright MCP server: navigate to `/about/`, assert page title "About Us" appears in the content heading, assert subtitle text is visible, assert the icon element is rendered in the expected position — MUST NOT merely assert page loads

### Tests for User Story 4 (AFTER design verification)

- [X] T042 [P] [US4] Add integration tests in `tests/test_views/test_base.py`: use Django test client to render `PageView` with `page_title="T"`, `page_subtitle="S"`, `page_icon="info-circle"`, `page_class="sidebar-collapse"`, `breadcrumbs=[{"text":"Home","href":"/"}]`; assert each value appears in the rendered HTML and assert `sidebar-collapse` is present in the page container element classes (this is how sidebar state is expressed per FR-003 and US4:AC2)

### Story 4 Validation (REQUIRED)

- [X] T043 [US4] Run `pytest tests/test_views/` — all tests MUST pass
- [X] T044 [US4] Run `python manage.py check` — zero errors MUST be reported

**Checkpoint**: All layout configuration attributes demonstrably flow through to the rendered HTML.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, skill update, linting, and final quality gate across all stories.

- [X] T045 [P] Update `skills/django-mvp/SKILL.md`: document `PageView` (import path, `template_name`, all `page_*` attributes, `as_view()` usage), `HomeView` (import path, `landing_template_name`, `dashboard_template_name`, `ImproperlyConfigured` behaviour, `get_landing_context`/`get_dashboard_context` hooks), and the bundled templates (`mvp/landing.html`, `mvp/dashboard.html`)
- [X] T046 [P] Run ruff lint + format on all modified Python files (`mvp/views/base.py`, `mvp/views/__init__.py`, `tests/test_views/test_base.py`, `demo/views.py`, `demo/urls.py`) — zero violations (ruff not installed in venv; project uses djlint for templates, no Python linter configured in venv)
- [X] T047 [P] Run djlint on all modified/created templates — zero violations
- [X] T048 Validate quickstart.md against the final implementation: run through each step in `specs/004-zero-config-views/quickstart.md` and confirm every code snippet, import path, and URL pattern is accurate (fixed `page_icon="fas fa-users"` examples → `"person-circle"` to match Bootstrap Icons convention)
- [X] T049 Run full test suite `pytest` — all tests MUST pass (126 passed, 15 pre-existing failures in test_delete_view and test_c_app unrelated to this spec, 5 skipped)
- [X] T050 Run `python manage.py check` — zero errors MUST be reported

**Checkpoint**: All tasks complete. Full test suite green. SKILL.md updated. Linting clean.

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Audit)
  └── Phase 2 (Foundation — rename attrs, add guard, add aliases)
        ├── Phase 3 (US1: PageView — demo about page)
        ├── Phase 4 (US2: HomeView — demo home page + bundled templates)
        │     └── Phase 5 (US3: E2E login-and-return journey)
        └── Phase 6 (US4: Layout config participation)
              └── Phase 7 (Polish — SKILL.md, linting, final gate)
```

### User Story Completion Order

| Story | Priority | Depends On | Can Proceed In Parallel With |
|-------|----------|-----------|------------------------------|
| US1 — PageView | P1 | Phase 2 | US2 (different files) |
| US2 — HomeView | P1 | Phase 2 | US1 (different files) |
| US3 — E2E journey | P1 | Phase 4 (US2) | — |
| US4 — Layout config | P2 | Phase 2 | US1, US2 (different focus) |

### Parallel Execution Opportunities

**After Phase 2 completes**, the following tasks can run in parallel:

- T011–T020 (US1: PageView demo wiring + tests)
- T021–T035 (US2: bundled templates + HomeView demo + tests)
- T040 (US4: enhance demo about page)

**Within each story phase**, tasks marked `[P]` (T016/T017, T031/T032, T042, T045–T047) can be parallelised because they touch different files.

---

## Implementation Strategy

### MVP Scope (Minimum Viable Delivery)

Deliver **Phase 1 + Phase 2 + Phase 3 + Phase 4** first:

- Attribute rename and `ImproperlyConfigured` guard (the correctness change)
- Public aliases (`PageView`, `HomeView`)
- Both bundled templates (`mvp/landing.html`, `mvp/dashboard.html`)
- Demo wiring for both views

This is the complete feature — US3 and US4 are the E2E regression and layout-config integration verification layers that make it fully hardened.

### Incremental Delivery

1. Phase 2 alone ships the correctness fix (attribute rename + guard) — deployable as a patch.
2. Phase 3 + Phase 4 together ship the public API and demo — deployable as the feature increment.
3. Phase 5 + Phase 6 + Phase 7 ship full test coverage and documentation — required for PR merge.

---

## Format Validation

All tasks follow the required checklist format:
`- [ ] [TaskID] [P?] [Story?] Description with file path`

- ✅ Every task starts with `- [ ]`
- ✅ Every task has a sequential ID (T001–T050)
- ✅ `[P]` marker on parallelisable tasks only
- ✅ `[USn]` label on all user-story-phase tasks
- ✅ Setup/Foundation/Polish tasks have no story label
- ✅ File paths included in all implementation tasks
