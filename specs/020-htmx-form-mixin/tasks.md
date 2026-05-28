# Tasks: HTMX Form Mixin

**Input**: Design documents from `specs/020-htmx-form-mixin/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, quickstart.md ✓

**User Stories**:
- US1 (P1): Submit a Form Without a Full Page Reload
- US2 (P1): Wire Up HTMX Enhancement with Minimal Configuration
- US3 (P2): Return an HX-Redirect Header on Success
- US4 (P3): Emit HTMX Response Triggers on Success

---

## Phase 1: Setup

**Purpose**: Add `django-htmx` as a required package dependency and wire it into the shared settings.

- [ ] T001 Add `"django-htmx (>=1.0,<2.0)"` to `[project] dependencies` in `pyproject.toml` and run `poetry lock`
- [ ] T002 Add `"django_htmx.middleware.HtmxMiddleware"` to `MIDDLEWARE` in `tests/settings.py` after `SessionMiddleware` and before `CsrfViewMiddleware` — `django_htmx` does NOT need to be added to `INSTALLED_APPS`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the `HtmxFormMixin` class skeleton and test scaffold. No user story can begin until this phase is complete.

**⚠️ CRITICAL**: Complete before any Phase 3+ work begins.

- [ ] T003 Create `mvp/views/htmx.py` with `HtmxFormMixin` class: declare all five class attributes (`htmx_success_template = None`, `htmx_form_template = None`, `htmx_redirect_on_success = False`, `htmx_trigger = None`, `htmx_trigger_after = "receive"`) and stub `get_htmx_success_template()`, `get_htmx_form_template()`, `form_valid()`, `form_invalid()` with `pass` bodies — `ImproperlyConfigured` guards are intentionally deferred to T022/T023; do not add them to the stubs now
- [ ] T004 Add `from .htmx import HtmxFormMixin` import and `"HtmxFormMixin"` entry to `__all__` in `mvp/views/__init__.py`
- [ ] T005 [P] Create `tests/test_views/test_htmx_form_mixin.py` with module docstring, all required imports (`pytest`, `RequestFactory`, `HtmxFormMixin`, `MVPCreateView`, `Product`), and a `make_htmx_view()` helper that builds a stub `HtmxFormMixin` + `MVPCreateView` subclass with a fake request bearing `HTTP_HX_REQUEST="true"`
- [ ] T006 Run `python manage.py check` — must report zero errors before user story work begins

**Checkpoint**: `HtmxFormMixin` is importable; test file and helper exist; system check passes.

---

## Phase 3: US1 — Submit a Form Without a Full Page Reload (Priority: P1) 🎯 MVP

**Goal**: On a valid htmx POST return a Cotton partial via `render_component()`; on an invalid htmx POST return the form Cotton partial at HTTP 200; non-htmx requests delegate unchanged to the base view; Django success messages are drained on htmx success paths.

**Independent Test**: A `HtmxFormMixin` + `MVPCreateView` subclass with both templates configured, submitted via htmx with valid data, returns an `HttpResponse` containing only the success partial content (no full-page layout markup). The same view submitted without htmx headers redirects normally.

### Tests for US1 ⚠️ Write FIRST, confirm failing before T011

- [ ] T007 [US1] Write test `test_form_valid_htmx_returns_success_partial`: htmx POST with valid data returns `HttpResponse` whose body is the `render_component()` output for `htmx_success_template`, not a redirect in `tests/test_views/test_htmx_form_mixin.py`
- [ ] T008 [US1] Write test `test_form_invalid_htmx_returns_form_partial_at_200`: htmx POST with invalid data returns `HttpResponse(status=200)` whose body is the `render_component()` output for `htmx_form_template` in `tests/test_views/test_htmx_form_mixin.py`
- [ ] T009 [US1] Write tests `test_form_valid_non_htmx_redirects` and `test_form_invalid_non_htmx_full_page`: non-htmx POST delegates entirely to base view (standard redirect on success; full-page re-render on error; no partial body) in `tests/test_views/test_htmx_form_mixin.py`
- [ ] T010 [US1] Write test `test_messages_drained_on_htmx_success_path`: after a valid htmx POST the Django message queue is empty (call `list(get_messages(request))` after the response and assert length is 0) in `tests/test_views/test_htmx_form_mixin.py`
- [ ] T010a [US1] Run `pytest tests/test_views/test_htmx_form_mixin.py` — confirm all US1 tests FAIL before implementation proceeds

### Implementation for US1

- [ ] T011 [US1] Implement `form_valid()` htmx branch in `mvp/views/htmx.py`: when `request.htmx`, call `super().form_valid(form)`, drain messages via `list(get_messages(request))`, build context from `self.get_context_data(form=form)`, and return `HttpResponse(render_component(request, self.get_htmx_success_template(), context))`
- [ ] T012 [US1] Implement `form_invalid()` htmx branch in `mvp/views/htmx.py`: when `request.htmx`, build context from `self.get_context_data(form=form)` and return `HttpResponse(render_component(request, self.get_htmx_form_template(), context), status=200)`
- [ ] T013 [P] [US1] Create demo Cotton form-error component `demo/templates/cotton/demo/htmx-product-form.html` with `<form hx-post="{{ request.path }}" hx-target="#htmx-demo-form" hx-swap="outerHTML">`, CSRF token, `{{ form.as_div }}`, and a submit button — `Product.name` is a required `CharField`; leaving it blank will produce a visible validation error for the T018(c) error scenario
- [ ] T014 [P] [US1] Create demo Cotton success component `demo/templates/cotton/demo/htmx-product-created.html` with success feedback referencing `{{ object.name }}`
- [ ] T014b [US1] Create demo page template `demo/templates/htmx_demo.html` that extends the base layout, wraps `<c-demo.htmx-product-form :form="form" />` in `<div id="htmx-demo-form">...</div>`, and includes `<script src="https://unpkg.com/htmx.org@2" defer></script>` in the `{% block extra_js %}` section — this is the swap target and outer page served on non-htmx GET requests
- [ ] T015 [US1] Add `HtmxProductCreateView` (subclass of `HtmxFormMixin` + `MVPCreateView` with `Product` model, both cotton templates configured, `template_name="htmx_demo.html"`, `success_url="list"`) to `demo/views.py` and register URL `htmx-demo/` with `name="htmx_demo"` in `demo/urls.py`
- [ ] T016 [US1] Add sidebar menu entry for `htmx_demo` view in `demo/menus.py`
- [ ] T017 [US1] Run `pytest tests/test_views/test_htmx_form_mixin.py -x` — all US1 tests must pass; then run `python manage.py check`
- [ ] T018 [US1] Playwright verification using playwright-cli skill in a real browser: (a) navigate to the htmx demo view, submit the form via htmx with valid data → assert success partial replaces the form container without any page navigation (URL unchanged); (b) submit the form with JS/htmx disabled → assert standard redirect occurs; (c) submit invalid data via htmx → assert validation errors appear inside the form partial

**Checkpoint**: US1 fully functional. Partials served on htmx paths. Full-page fallback unchanged. Messages drained.

---

## Phase 4: US2 — Wire Up with Minimal Configuration (Priority: P1)

**Goal**: Raise `ImproperlyConfigured` with a clear developer-facing message when `htmx_success_template` or `htmx_form_template` are not configured and an htmx request hits the relevant path. Support overriding `get_htmx_success_template()` and `get_htmx_form_template()` for per-request dynamic resolution.

**Independent Test**: A mixin-enhanced view missing `htmx_success_template` (with `htmx_redirect_on_success=False`) raises `ImproperlyConfigured` on a valid htmx POST. A view missing `htmx_form_template` raises `ImproperlyConfigured` on an invalid htmx POST.

### Tests for US2 ⚠️ Write FIRST, confirm failing before T023

- [ ] T019 [US2] Write test `test_missing_success_template_raises_improperly_configured`: htmx POST with valid data on a view where `htmx_success_template` is `None` and `htmx_redirect_on_success=False` raises `ImproperlyConfigured` in `tests/test_views/test_htmx_form_mixin.py`
- [ ] T020 [US2] Write test `test_missing_form_template_raises_improperly_configured`: htmx POST with invalid data on a view where `htmx_form_template` is `None` raises `ImproperlyConfigured` in `tests/test_views/test_htmx_form_mixin.py`
- [ ] T021 [US2] Write tests `test_get_htmx_success_template_override_used` and `test_get_htmx_form_template_override_used`: subclasses that override `get_htmx_success_template()` / `get_htmx_form_template()` to return a different component name have that name used by `render_component()` in `tests/test_views/test_htmx_form_mixin.py`
- [ ] T021a [US2] Run `pytest tests/test_views/test_htmx_form_mixin.py -k "improperly or override"` — confirm US2 tests FAIL

### Implementation for US2

- [ ] T022 [US2] Implement `get_htmx_success_template()` in `mvp/views/htmx.py`: return `self.htmx_success_template` if truthy; raise `ImproperlyConfigured("HtmxFormMixin requires 'htmx_success_template' or 'htmx_redirect_on_success = True'.")` otherwise
- [ ] T023 [US2] Implement `get_htmx_form_template()` in `mvp/views/htmx.py`: return `self.htmx_form_template` if truthy; raise `ImproperlyConfigured("HtmxFormMixin requires 'htmx_form_template' to be set.")` otherwise
- [ ] T024 [US2] Update `form_valid()` to call `self.get_htmx_success_template()` only when `htmx_redirect_on_success` is falsy; update `form_invalid()` to call `self.get_htmx_form_template()` unconditionally when on the htmx path in `mvp/views/htmx.py`
- [ ] T025 [US2] Run `pytest tests/test_views/test_htmx_form_mixin.py` — all US1 + US2 tests pass; run `python manage.py check`
- [ ] T026 [US2] Playwright verification: (a) temporarily remove `htmx_form_template` from the demo view class and restart the server; submit an invalid htmx POST → assert Django DEBUG error page contains `ImproperlyConfigured` and the text `htmx_form_template`; (b) restore `htmx_form_template` to its original value and immediately run `pytest tests/test_views/test_htmx_form_mixin.py -x` to confirm the restoration — do not proceed until pytest is green; (c) reload the browser and submit a valid htmx POST → assert the success partial is returned normally (positive US2 acceptance scenario 1); also verify a non-htmx GET renders the full page without errors

**Checkpoint**: US2 complete. Misconfiguration caught early with clear messages. Override hooks work.

---

## Phase 5: US3 — Return an HX-Redirect Header on Success (Priority: P2)

**Goal**: When `htmx_redirect_on_success = True`, return `HttpResponseClientRedirect(success_url)` on a valid htmx POST. When both `htmx_redirect_on_success` and `htmx_success_template` are set, redirect takes precedence.

**Independent Test**: A mixin-enhanced view with `htmx_redirect_on_success = True` receiving a valid htmx POST returns a response with `HX-Redirect` header set to the resolved `success_url`; no partial body is rendered.

### Tests for US3 ⚠️ Write FIRST, confirm failing before T030

- [ ] T027 [US3] Write test `test_htmx_redirect_on_success_returns_client_redirect`: valid htmx POST on a view with `htmx_redirect_on_success=True` returns `HttpResponseClientRedirect` with `HX-Redirect` header equal to `get_success_url()` in `tests/test_views/test_htmx_form_mixin.py`
- [ ] T028 [US3] Write test `test_redirect_takes_precedence_over_success_template`: view with both `htmx_redirect_on_success=True` and `htmx_success_template` set returns `HttpResponseClientRedirect`, not the partial in `tests/test_views/test_htmx_form_mixin.py`
- [ ] T028a [US3] Run `pytest tests/test_views/test_htmx_form_mixin.py -k "redirect"` — confirm US3 tests FAIL

### Implementation for US3

- [ ] T029 [US3] Update `form_valid()` htmx branch in `mvp/views/htmx.py`: before the `render_component()` path, add `if self.htmx_redirect_on_success: return HttpResponseClientRedirect(self.get_success_url())`; import `HttpResponseClientRedirect` from `django_htmx.http` at top of file
- [ ] T030 [US3] Run `pytest tests/test_views/test_htmx_form_mixin.py` — all US1 + US2 + US3 tests pass; run `python manage.py check`
- [ ] T031 [US3] Playwright verification: configure the demo view with `htmx_redirect_on_success = True`; submit valid data via htmx → assert browser navigates to the success URL (full navigation, no partial swap); restore demo view to partial-swap mode after verification

**Checkpoint**: US3 complete. `HX-Redirect` path working; redirect takes precedence over partial.

---

## Phase 6: US4 — Emit HTMX Response Triggers on Success (Priority: P3)

**Goal**: When `htmx_trigger` is a string or dict, call `trigger_client_event()` on the success response (both partial and redirect paths) using the timing from `htmx_trigger_after`.

**Independent Test**: A mixin-enhanced view with `htmx_trigger = "itemCreated"` returns a success response bearing the `HX-Trigger: itemCreated` header (applied by `trigger_client_event(response, "itemCreated", after="receive")`).

### Tests for US4 ⚠️ Write FIRST, confirm failing before T036

- [ ] T032 [US4] Write test `test_htmx_trigger_string_adds_hx_trigger_header`: valid htmx POST with `htmx_trigger="itemCreated"` returns a response with `HX-Trigger` header containing `"itemCreated"` in `tests/test_views/test_htmx_form_mixin.py`
- [ ] T033 [US4] Write test `test_htmx_trigger_dict_adds_events_for_each_key`: `htmx_trigger={"eventA": None, "eventB": {"id": 1}}` results in both events present in the trigger header in `tests/test_views/test_htmx_form_mixin.py`
- [ ] T034 [US4] Write tests `test_htmx_trigger_after_settle_uses_correct_header` (response has `HX-Trigger-After-Settle`, not `HX-Trigger`) and `test_htmx_trigger_after_swap_uses_correct_header` in `tests/test_views/test_htmx_form_mixin.py`
- [ ] T035 [US4] Write test `test_htmx_trigger_none_adds_no_trigger_header`: when `htmx_trigger` is `None` no `HX-Trigger` family header is added to the response in `tests/test_views/test_htmx_form_mixin.py`
- [ ] T035a [US4] Run `pytest tests/test_views/test_htmx_form_mixin.py -k "trigger"` — confirm US4 tests FAIL

### Implementation for US4

- [ ] T036 [US4] Add `_apply_htmx_triggers(self, response)` private method to `HtmxFormMixin` in `mvp/views/htmx.py`: no-op when `htmx_trigger` is falsy; calls `trigger_client_event(response, self.htmx_trigger, after=self.htmx_trigger_after)` for a string; iterates `self.htmx_trigger.items()` and calls `trigger_client_event(response, name, params, after=self.htmx_trigger_after)` for each entry when a dict; import `trigger_client_event` from `django_htmx.http`
- [ ] T037 [US4] Call `self._apply_htmx_triggers(response)` at the end of both the partial and redirect branches in `form_valid()` in `mvp/views/htmx.py`
- [ ] T038 [US4] Run `pytest tests/test_views/test_htmx_form_mixin.py` — all US1 + US2 + US3 + US4 tests pass; run `python manage.py check`
- [ ] T039 [US4] Playwright verification: (a) add `htmx_trigger = "productCreated"` to `HtmxProductCreateView` in `demo/views.py`; (b) update `demo/templates/htmx_demo.html` to add a `<div hx-get="{{ request.path }}" hx-trigger="productCreated from:body" hx-target="this">product count</div>` panel below the form container; (c) submit a valid htmx POST → assert the listening panel refreshes without a full-page reload; (d) revert both changes (htmx_trigger and the template panel) after verification — trigger emission is not a permanent feature of the demo view

**Checkpoint**: US4 complete. All four user stories fully functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Docstrings, export verification, coverage gate, full regression suite.

- [ ] T040 [P] Write class and method docstrings for `HtmxFormMixin` in `mvp/views/htmx.py` (class-level attribute table, `form_valid()` / `form_invalid()` contracts, and a minimal usage example matching `specs/020-htmx-form-mixin/quickstart.md`)
- [ ] T041 [P] Verify `from mvp.views import HtmxFormMixin` resolves correctly in a Python shell; confirm entry in `__all__` in `mvp/views/__init__.py`
- [ ] T042 Run `pytest tests/test_views/test_htmx_form_mixin.py --cov=mvp/views/htmx --cov-report=term-missing` — confirm 100% branch coverage on `mvp/views/htmx.py` (SC-006)
- [ ] T043 Run full test suite `poetry run pytest tests/` — all pre-existing tests pass; zero regressions on non-htmx paths (SC-002)
- [ ] T044 Run `python manage.py check` and `ruff check mvp/views/htmx.py` — zero errors and zero linting violations

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)
    └─→ Phase 2 (Foundational) [BLOCKS all US phases]
            ├─→ Phase 3 (US1, P1) 🎯 MVP — start here
            │       └─→ Phase 4 (US2, P1) — completes P1 scope
            ├─→ Phase 5 (US3, P2) — independent of US2
            └─→ Phase 6 (US4, P3) — independent of US2/US3
                        └─→ Phase 7 (Polish)
```

### User Story Dependencies

| Story | Priority | Depends On | Can Overlap With |
|---|---|---|---|
| US1 | P1 | Phase 2 | — |
| US2 | P1 | US1 (fills in guards on existing logic) | US3, US4 |
| US3 | P2 | Phase 2 | US2, US4 |
| US4 | P3 | Phase 2 | US2, US3 |

### Parallel Opportunities Within Phases

| Phase | Parallel Tasks |
|---|---|
| Phase 1 | T001 and T002 (independent files) |
| Phase 2 | T005 (test scaffold) runs in parallel with T003 and T004 |
| Phase 3 | T013 (form component) and T014 (success component) run in parallel with T011/T012 |
| Phase 7 | T040 (docstrings) and T041 (export verify) run in parallel |

### Implementation Strategy (MVP-First Delivery)

1. **MVP** — Complete Phases 1–3 (US1 only). Delivers the core no-reload form submission value. Verify in browser.
2. **Increment 1** — Add Phase 4 (US2 guards). Completes all P1 scope.
3. **Increment 2** — Add Phase 5 (US3 redirect). Completes P2 scope.
4. **Increment 3** — Add Phase 6 (US4 triggers). Completes P3 scope.
5. **Final** — Phase 7 polish, coverage gate, full regression.
