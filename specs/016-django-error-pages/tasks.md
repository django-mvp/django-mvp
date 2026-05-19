# Tasks: Django Error Pages

**Input**: Design documents from `specs/016-django-error-pages/`
**Branch**: `feature/016-django-error-pages`
**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/template-block-api.md ✅

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1–US5)
- All paths are relative to repository root (`django-mvp/`)

---

## Phase 1: Setup

**Purpose**: Verify baseline state before making any changes.

- [ ] T001 Audit existing error templates: read `mvp/templates/mvp/error_base.html`, `mvp/templates/404.html`, and `mvp/templates/500.html` in full; confirm all 5 blocks (`error_title`, `error_code`, `error_heading`, `error_description`, `error_actions`) exist in `error_base.html` and note any gaps

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before any user story begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T002 Harden `mvp/templates/mvp/error_base.html` — verify all 5 named blocks (`error_title`, `error_code`, `error_heading`, `error_description`, `error_actions`) are defined with sensible empty defaults; fix any missing blocks
- [ ] T003 Create `mvp/views/error.py` with skeleton stubs for all four handler functions: `bad_request(request, exception)` returns `HttpResponse(status=400)`, `permission_denied(request, exception)` returns 403, `not_found(request, exception)` returns 404, `server_error(request)` returns 500 — stubs render the correct template but `server_error` passes an empty context for now (support_email logic is added in T012)
- [ ] T004 Update `mvp/views/__init__.py` to export `bad_request`, `permission_denied`, `not_found`, `server_error` in `__all__`
- [ ] T005 Register Django error handlers in `demo/urls.py`: `handler400 = "mvp.views.error.bad_request"`, `handler403 = "mvp.views.error.permission_denied"`, `handler404 = "mvp.views.error.not_found"`, `handler500 = "mvp.views.error.server_error"`
- [ ] T006 Run `python manage.py check` — must pass with zero errors before proceeding

**Checkpoint**: Foundation ready — error handler functions exist and are wired. User story work can begin.

---

## Phase 3: User Story 1 — [End User] 404 Not Found (Priority: P1) 🎯 MVP

**Goal**: A visitor navigating to a missing URL sees a styled, branded 404 page with a "Back to dashboard" action.

**Independent Test**: Navigate to any non-existent URL with `DEBUG=False` (or use the demo preview at `/errors/404/`); confirm the styled 404 page renders, heading reads "Oops! Page not found.", and the back button links to `/`.

### Tests — User Story 1

> **Write these FIRST. Observe them FAILING before touching the template.**

- [ ] T007 [P] [US1] Write unit tests for `not_found` view in `tests/test_views/test_error_views.py`:
  - Default: response status is 404, template `404.html` is used, response contains heading text, link to `/` is present
  - `@override_settings(DEBUG=False)`: make a GET request to a nonexistent URL via `Client().get("/nonexistent-url/")` and assert the response status is 404 and the custom template (not Django's default debug 404) is rendered

### Implementation — User Story 1

- [ ] T008 [US1] Update `mvp/templates/404.html`: confirm all 5 blocks are filled — `error_title` = "404 — Page Not Found", `error_code` = blue display-1 div, `error_heading` = `<h1>` "Oops! Page not found.", `error_description` with helpful copy, `error_actions` with a single `<c-button>` linking to `/`; wrap all user-visible text in `{% trans %}`
- [ ] T009 [US1] Playwright MCP verification — open `http://localhost:8003/errors/404/` in browser; confirm: 404 code is prominent and blue, `<h1>` is visible, "Back to dashboard" button exists and links to `/`, page is readable on mobile viewport (375px wide)

**Checkpoint**: 404 page is independently functional and visually verified.

- [ ] T010 [US1] Run `python manage.py check` and `pytest tests/test_views/test_error_views.py` — all tests must pass

---

## Phase 4: User Story 2 — [End User] 500 Server Error (Priority: P2)

**Goal**: A visitor encountering an unhandled exception sees a calm, neutral 500 page with optional support contact, and no debug information is exposed.

**Independent Test**: Open the demo preview at `/errors/500/`; confirm neutral copy ("Something went wrong"), no stack trace visible, "Back to dashboard" button present, and "Contact support" button conditionally visible based on `DEFAULT_FROM_EMAIL`.

### Tests — User Story 2

> **Write these FIRST. Observe them FAILING before touching the template or view.**

- [ ] T011 [P] [US2] Write unit tests for `server_error` view in `tests/test_views/test_error_views.py`:
  - When `settings.DEFAULT_FROM_EMAIL = "support@example.com"`: response status 500, `support_email` in context equals `"support@example.com"`, template `500.html` used
  - When `settings.DEFAULT_FROM_EMAIL = ""`: `support_email` in context is `None`
  - Response contains no Django debug information
  - DB query guard: call `server_error(request)` inside `django_assert_num_queries(0)` to formally prove SC-007 (zero DB queries even during error handling)
  - `@override_settings(DEBUG=False)`: assert the real handler fires when an unhandled exception occurs (use a view that raises an exception in a test URLconf) and returns 500 with no stack trace in the response body

### Implementation — User Story 2

- [ ] T012 [US2] Complete `server_error` function in `mvp/views/error.py` — add `support_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or None` to the context dict passed to `render()`; this makes T011 DB-query and context assertions pass
- [ ] T013 [US2] Update `mvp/templates/500.html`: set heading copy to `"Something went wrong."` (neutral, no fault attribution — per clarification Q1), set description to `"Please try again, or contact support if the issue persists."`, wrap contact button in `{% if support_email %}...{% endif %}` with `href="mailto:{{ support_email }}"`, ensure all text is wrapped in `{% trans %}`
- [ ] T014 [US2] Playwright MCP verification — open `http://localhost:8003/errors/500/`; confirm: neutral copy visible, "Back to dashboard" button present, no stack trace, contact button visible when `DEFAULT_FROM_EMAIL` is set, button hidden when setting is empty

**Checkpoint**: 500 page is independently functional with conditional support email.

- [ ] T015 [US2] Run `python manage.py check` and `pytest tests/test_views/test_error_views.py` — all tests must pass

---

## Phase 5: User Story 3 — [End User] 403 Forbidden (Priority: P3)

**Goal**: A visitor denied access sees a styled 403 page explaining the situation with a single "Back to home" action.

**Independent Test**: Open the demo preview at `/errors/403/`; confirm the 403 code is displayed, heading reads "Access Denied", and a single "Back to home" button is present (no sign-in link).

### Tests — User Story 3

> **Write these FIRST. Observe them FAILING before creating the template.**

- [ ] T016 [P] [US3] Write unit tests for `permission_denied` view in `tests/test_views/test_error_views.py`:
  - Default: response status is 403, template `403.html` is used, response contains "Back to home" text and a link to `/`
  - `@override_settings(DEBUG=False)`: request a permission-denied URL and assert the custom 403 template is rendered (not Django's generic response)

### Implementation — User Story 3

- [ ] T017 [US3] Create `mvp/templates/403.html`: extends `mvp/error_base.html`, `error_title` = "403 — Forbidden", `error_code` = amber/warning display-1 div (`text-warning`), `error_heading` = `<h1>` "Access Denied.", `error_description` = plain-language explanation, `error_actions` = single `<c-button variant="outline-secondary">` linking to `/` with "Back to home" label; wrap all text in `{% trans %}`
- [ ] T018 [US3] Playwright MCP verification — open `http://localhost:8003/errors/403/`; confirm: 403 code visible and amber-coloured, `<h1>` "Access Denied" present, single "Back to home" button with href `/`, no sign-in link, responsive on mobile

**Checkpoint**: 403 page is independently functional.

- [ ] T019 [US3] Run `python manage.py check` and `pytest tests/test_views/test_error_views.py` — all tests must pass

---

## Phase 6: User Story 4 — [End User] 400 Bad Request (Priority: P4)

**Goal**: A visitor sending a malformed request sees a styled 400 page with a plain-language explanation and a "Back to home" action.

**Independent Test**: Open the demo preview at `/errors/400/`; confirm the 400 code is displayed, heading is "Bad Request", and a single "Back to home" button is present.

### Tests — User Story 4

> **Write these FIRST. Observe them FAILING before creating the template.**

- [ ] T020 [P] [US4] Write unit tests for `bad_request` view in `tests/test_views/test_error_views.py`:
  - Default: response status is 400, template `400.html` is used, response contains "Back to home" text and a link to `/`
  - `@override_settings(DEBUG=False)`: assert the custom 400 template is rendered when the handler is triggered

### Implementation — User Story 4

- [ ] T021 [US4] Create `mvp/templates/400.html`: extends `mvp/error_base.html`, `error_title` = "400 — Bad Request", `error_code` = muted/secondary display-1 div (`text-secondary`), `error_heading` = `<h1>` "Bad Request.", `error_description` = plain-language explanation (e.g. "Your browser sent a request the server could not understand."), `error_actions` = single `<c-button variant="outline-secondary">` linking to `/` with "Back to home"; wrap all text in `{% trans %}`
- [ ] T022 [US4] Playwright MCP verification — open `http://localhost:8003/errors/400/`; confirm: 400 code visible, `<h1>` "Bad Request" present, "Back to home" button with href `/`, responsive on mobile

**Checkpoint**: All four error pages are independently functional.

- [ ] T023 [US4] Run `python manage.py check` and `pytest tests/test_views/test_error_views.py` — all tests must pass

---

## Phase 7: User Story 5 — [Developer] Developer Previews Error Pages (Priority: P5)

**Goal**: A developer can navigate to `/errors/400/`, `/errors/403/`, `/errors/404/`, `/errors/500/` in the demo app and visually inspect each error page without triggering a real error.

**Independent Test**: Start the dev server, open each `/errors/NNN/` URL in a browser, confirm each renders the correct styled page. Also confirm the "Error Pages" section appears in the sidebar and links to each preview.

### Implementation — User Story 5

- [ ] T024 [US5] Add a single `ErrorPagePreviewView(TemplateView)` base class to `demo/views.py`; wire four `.as_view(template_name="NNN.html")` call-sites in `demo/urls.py` (T025) — no per-code subclasses needed; for the 500 preview, pass `extra_context={"support_email": settings.DEFAULT_FROM_EMAIL or None}` in the `.as_view()` call
- [ ] T025 [US5] Add four preview URL routes to `demo/urls.py` under the `errors/` prefix: `path("errors/400/", ...)`, `path("errors/403/", ...)`, `path("errors/404/", ...)`, `path("errors/500/", ...)` with names `error-preview-400`, `error-preview-403`, `error-preview-404`, `error-preview-500`
- [ ] T026 [P] [US5] Add "Error Pages" `MenuGroup` to `demo/menus.py` with four child `MenuItem` entries (one per error code), each linking to the corresponding preview route via `view_name`
- [ ] T027 [US5] Playwright MCP verification — open the demo app sidebar; confirm the "Error Pages" group is present and expanded; click each of the four links and verify the correct page renders; confirm all four preview routes return HTTP 200

**Checkpoint**: Developer preview routes are fully functional and accessible from the sidebar.

- [ ] T028 [US5] Run `python manage.py check` and `pytest tests/test_views/test_error_views.py`

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end coverage, skill documentation, and final quality gates.

- [ ] T029 [P] Write `tests/test_views/test_error_views_e2e.py` with pytest-playwright E2E tests for all four error pages: for each preview URL assert — error code text is visible in the DOM, a single `<h1>` element is present, a link with `href="/"` exists, page `<title>` contains the numeric code, HTTP response is 200 (preview) and correct status (handler); also run an axe-core accessibility sweep on each page using `page.evaluate(axe_script)` and assert zero critical WCAG 2.1 AA violations (satisfies SC-005)
- [ ] T030 [P] Update `skills/django-mvp/SKILL.md` — add a section documenting the error page template block API (`error_title`, `error_code`, `error_heading`, `error_description`, `error_actions`), the handler registration pattern (`handler400/403/404/500` string paths in root URLconf), and the `DEFAULT_FROM_EMAIL` → `support_email` context variable for the 500 page
- [ ] T031 Run full test suite: `poetry run pytest` — all tests must pass including new unit and E2E tests; SC-002 (<1s render) is verified by design — zero DB queries + static template rendering guarantees sub-second response, no wall-clock assertion required
- [ ] T032 [P] Run Ruff: `poetry run ruff check . && poetry run ruff format --check .` — zero violations
- [ ] T033 [P] Run djlint on new and updated templates: `poetry run djlint mvp/templates/400.html mvp/templates/403.html mvp/templates/404.html mvp/templates/500.html mvp/templates/mvp/error_base.html --check` — zero violations

---

## Dependencies & Execution Order

### Phase Dependencies

| Phase | Depends On | Notes |
|-------|-----------|-------|
| Phase 1: Setup | — | Start immediately |
| Phase 2: Foundational | Phase 1 | **BLOCKS all user story phases** |
| Phase 3: US1 (404) | Phase 2 | First priority after foundation |
| Phase 4: US2 (500) | Phase 2 | Can start after Phase 2; independent of US1 |
| Phase 5: US3 (403) | Phase 2 | Can start after Phase 2; independent of US1/US2 |
| Phase 6: US4 (400) | Phase 2 | Can start after Phase 2; independent of US1–US3 |
| Phase 7: US5 (Preview) | Phases 3–6 | Requires all 4 templates to exist |
| Phase 8: Polish | Phases 3–7 | Run after all stories complete |

### User Story Dependencies

- **US1 (404)**: No dependency on other stories
- **US2 (500)**: No dependency on other stories; `server_error` view update (T012) depends on T003
- **US3 (403)**: No dependency on other stories
- **US4 (400)**: No dependency on other stories
- **US5 (Preview)**: Depends on all four templates existing (after Phases 3–6)

### Within Each User Story

1. Write tests (T00x [P]) — confirm they FAIL
2. Implement template/view change
3. Playwright MCP verification
4. `python manage.py check` + pytest validation

### Parallel Opportunities

All tasks marked `[P]` within a phase can run concurrently (they touch different files):
- T007, T011, T016, T020 (story test files — each tests a different view)
- T026, T029, T030, T032, T033 (independent in Phase 7/8)
- US1–US4 can be implemented in parallel after Phase 2 completes (different templates)

---

## Parallel Example: Phase 3–6 (After Foundational Complete)

```bash
# After T006 (manage.py check) passes, launch in parallel:

Stream A — US1 (404):  T007 → T008 → T009 → T010
Stream B — US2 (500):  T011 → T012 → T013 → T014 → T015
Stream C — US3 (403):  T016 → T017 → T018 → T019
Stream D — US4 (400):  T020 → T021 → T022 → T023

# Then converge for US5 (Preview):  T024 → T025 → T026 → T027 → T028

# Then polish in parallel:
T029 (E2E tests)  |  T030 (SKILL.md)  |  T032 (Ruff)  |  T033 (djlint)

# Final gate:
T031 (full pytest suite)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002–T006) — **REQUIRED before anything else**
3. Complete Phase 3: US1 — 404 Not Found (T007–T010)
4. **STOP and VALIDATE**: Demo server running, navigate to `/errors/404/` with Playwright MCP, confirm layout
5. The 404 page is independently deployable as an MVP

### Incremental Delivery

- After Phase 2: error handler infrastructure deployed
- After Phase 3 (US1): 404 page live and tested
- After Phase 4 (US2): 500 page live with conditional support email
- After Phase 5 (US3): 403 page live
- After Phase 6 (US4): all four pages live
- After Phase 7 (US5): developer preview routes and sidebar navigation live
- After Phase 8: full test coverage, skill documented, CI-clean

### Notes

- Read `django-cotton-bs5` skill and `django-cotton` skill BEFORE authoring any template markup (Principle IX)
- Use context7 to retrieve current Django error view API docs before implementing `mvp/views/error.py` (Principle VII)
- All Playwright tasks MUST assert specific UX outcomes (error code text, `<h1>` heading, button href) — not just "page loads"
- Commit after each checkpoint (after T006, T010, T015, T019, T023, T028, T031)
