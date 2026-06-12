# Tasks: HTMX Form Mixin

**Input**: Design documents from `specs/020-htmx-form-mixin/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, quickstart.md ✓
**Propagated**: 2026-05-28 — Updated from spec.md refinement
**Propagated**: 2026-05-29 — Added Phase 8 (US5) for `htmx_success_components` allowlist and `X-Success-Component` client-driven component selection
**Propagated**: 2026-05-29 — Added Phase 9 (architectural refactor): `HtmxMixin` base class; `get_context_data()` moves from `HtmxFormMixin` to `HtmxMixin`; `HtmxFormMixin` inherits from `HtmxMixin` (FR-025–FR-026)
**Propagated**: 2026-05-29 — Added Phase 10 (expanded HtmxMixin): trigger subsystem (`htmx_trigger`, `htmx_trigger_after`, `_apply_htmx_triggers()`) and `_resolve_component()` helper move from `HtmxFormMixin` to `HtmxMixin`; `get_htmx_success_component()` delegates to `_resolve_component()` (FR-027–FR-028)

**User Stories**:

- US1 (P1): Submit a Form Without a Full Page Reload
- US2 (P1): Wire Up HTMX Enhancement with Minimal Configuration
- US3 (P2): Return an HX-Redirect Header on Success
- US4 (P3): Emit HTMX Response Triggers on Success
- US5 (P3): Select the Success Component from the Client Side

---

## Phase 1: Setup

**Purpose**: Add `django-htmx` as a dev/optional dependency (not a package dependency — developers install it themselves) and wire it into the shared test settings.

- [X] T001 Add `"django-htmx (>=1.0,<2.0)"` to `[tool.poetry.group.dev.dependencies]` in `pyproject.toml` (dev dep only, NOT `[project] dependencies`) and run `poetry lock`
- [X] T002 Add `"django_htmx.middleware.HtmxMiddleware"` to `MIDDLEWARE` in `tests/settings.py` after `SessionMiddleware` and before `CsrfViewMiddleware` — `django_htmx` does NOT need to be added to `INSTALLED_APPS`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the `HtmxFormMixin` class skeleton and test scaffold. No user story can begin until this phase is complete.

**⚠️ CRITICAL**: Complete before any Phase 3+ work begins.

- [X] T003 Create `mvp/views/htmx.py` with `HtmxFormMixin` class: declare all five class attributes (`htmx_success_component = None`, `htmx_form_component = "form"`, `htmx_redirect_on_success = False`, `htmx_trigger = None`, `htmx_trigger_after = "receive"`) and stub `get_htmx_success_component()`, `get_htmx_form_component()`, `get_context_data()`, `form_valid()`, `form_invalid()` with `pass` bodies — `ImproperlyConfigured` guards are intentionally deferred to T022/T023; do not add them to the stubs now **[REVISED — see Phase 9: `HtmxMixin` base class is now also created in this file; `get_context_data()` moves to `HtmxMixin`]**
- [X] T004 ~~Add `from .htmx import HtmxFormMixin` import and `"HtmxFormMixin"` entry to `__all__` in `mvp/views/__init__.py`~~ **[REVISED]** Ensure `mvp/views/__init__.py` does NOT import or re-export `HtmxFormMixin` — remove any such import or `__all__` entry if present. Developers import directly: `from mvp.views.htmx import HtmxFormMixin`.
- [X] T005 [P] Create `tests/test_views/test_htmx_form_mixin.py` with module docstring, all required imports (`pytest`, `RequestFactory`, `HtmxFormMixin` via `from mvp.views.htmx import HtmxFormMixin`, `MVPCreateView`, `Product`), and a `make_htmx_view()` helper that builds a stub `HtmxFormMixin` + `MVPCreateView` subclass with a fake request bearing `HTTP_HX_REQUEST="true"`
- [X] T005a [P] Write test `test_htmx_enabled_in_context`: a GET request on a mixin-enhanced view returns context with `htmx_enabled = True`; a request on a view that does NOT use the mixin does not have this key in context — in `tests/test_views/test_htmx_form_mixin.py`
- [X] T005b Implement `get_context_data()` override in `mvp/views/htmx.py`: call `super().get_context_data(**kwargs)`, add `htmx_enabled = True`, and return the updated context; this key allows templates to conditionally render htmx-specific attributes (`hx-post`, `hx-target`, `hx-swap`) without hard-coding them **[REVISED — see Phase 9: this method moves from `HtmxFormMixin` to `HtmxMixin`]**
- [X] T006 Run `python manage.py check` — must report zero errors before user story work begins

**Checkpoint**: `HtmxFormMixin` is importable; test file and helper exist; system check passes.

---

## Phase 3: US1 — Submit a Form Without a Full Page Reload (Priority: P1) 🎯 MVP

**Goal**: On a valid htmx POST return a Cotton partial via `render_component()`; on an invalid htmx POST return the form Cotton partial at HTTP 200; non-htmx requests delegate unchanged to the base view; Django success messages are drained on htmx success paths.

**Independent Test**: A `HtmxFormMixin` + `MVPCreateView` subclass with `htmx_success_component` and `htmx_form_component` configured, submitted via htmx with valid data, returns an `HttpResponse` containing only the success partial content (no full-page layout markup). The same view submitted without htmx headers redirects normally.

### Tests for US1 ⚠️ Write FIRST, confirm failing before T011

- [X] T007 [US1] Write test `test_form_valid_htmx_returns_success_partial`: htmx POST with valid data returns `HttpResponse` whose body is the `render_component()` output for `htmx_success_component`, not a redirect in `tests/test_views/test_htmx_form_mixin.py`
- [X] T008 [US1] Write test `test_form_invalid_htmx_returns_form_partial_at_200`: htmx POST with invalid data returns `HttpResponse(status=200)` whose body is the `render_component()` output for `htmx_form_component` in `tests/test_views/test_htmx_form_mixin.py`
- [X] T009 [US1] Write tests `test_form_valid_non_htmx_redirects` and `test_form_invalid_non_htmx_full_page`: non-htmx POST delegates entirely to base view (standard redirect on success; full-page re-render on error; no partial body) in `tests/test_views/test_htmx_form_mixin.py`
- [X] T010 [US1] Write test `test_messages_drained_on_htmx_success_path`: after a valid htmx POST the Django message queue is empty (call `list(get_messages(request))` after the response and assert length is 0) in `tests/test_views/test_htmx_form_mixin.py`
- [X] T010a [US1] Run `pytest tests/test_views/test_htmx_form_mixin.py` — confirm all US1 tests FAIL before implementation proceeds

### Implementation for US1

- [X] T011 [US1] Implement `form_valid()` htmx branch in `mvp/views/htmx.py`: when `request.htmx`, call `super().form_valid(form)`, drain messages via `list(get_messages(request))`, build context from `self.get_context_data(form=form)`, and return `HttpResponse(render_component(request, self.get_htmx_success_component(), context))`
- [X] T012 [US1] Implement `form_invalid()` htmx branch in `mvp/views/htmx.py`: when `request.htmx`, build context from `self.get_context_data(form=form)` and return `HttpResponse(render_component(request, self.get_htmx_form_component(), context), status=200)`
- [X] T013 [P] [US1] Create demo Cotton form-error component `demo/templates/cotton/demo/htmx-product-form.html` with `<form hx-post="{{ request.path }}" hx-target="#htmx-demo-form" hx-swap="outerHTML">`, CSRF token, `{{ form.as_div }}`, and a submit button — `Product.name` is a required `CharField`; leaving it blank will produce a visible validation error for the T018(c) error scenario
- [X] T014 [P] [US1] Create demo Cotton success component `demo/templates/cotton/demo/htmx-product-created.html` with success feedback referencing `{{ object.name }}`
- [X] T014b [US1] Create demo page template `demo/templates/htmx_demo.html` that extends the base layout, wraps `<c-demo.htmx-product-form :form="form" />` in `<div id="htmx-demo-form">...</div>`, and includes `<script src="https://unpkg.com/htmx.org@2" defer></script>` in the `{% block extra_js %}` section — this is the swap target and outer page served on non-htmx GET requests
- [X] T015 [US1] Add `HtmxProductCreateView` (subclass of `HtmxFormMixin` + `MVPCreateView` with `Product` model, `htmx_success_component` and optionally `htmx_form_component` configured, `template_name="htmx_demo.html"`, `success_url="list"`) to `demo/views.py` and register URL `htmx-demo/` with `name="htmx_demo"` in `demo/urls.py`
- [X] T016 [US1] Add sidebar menu entry for `htmx_demo` view in `demo/menus.py`
- [X] T017 [US1] Run `pytest tests/test_views/test_htmx_form_mixin.py -x` — all US1 tests must pass; then run `python manage.py check`
- [X] T018 [US1] Playwright verification using playwright-cli skill in a real browser: (a) navigate to the htmx demo view, submit the form via htmx with valid data → assert success partial replaces the form container without any page navigation (URL unchanged); (b) submit the form with JS/htmx disabled → assert standard redirect occurs; (c) submit invalid data via htmx → assert validation errors appear inside the form partial

**Checkpoint**: US1 fully functional. Partials served on htmx paths. Full-page fallback unchanged. Messages drained.

---

## Phase 4: US2 — Wire Up with Minimal Configuration (Priority: P1)

**Goal**: Raise `ImproperlyConfigured` with a clear developer-facing message when `htmx_success_component` is not configured (and `htmx_redirect_on_success` is False) and an htmx POST results in a valid form; or when `htmx_form_component` is explicitly cleared to falsy and an htmx POST results in an invalid form. Support overriding `get_htmx_success_component()` and `get_htmx_form_component()` for per-request dynamic resolution.

**Independent Test**: A mixin-enhanced view missing `htmx_success_component` (with `htmx_redirect_on_success=False`) raises `ImproperlyConfigured` on a valid htmx POST. A view with `htmx_form_component` explicitly set to `None` raises `ImproperlyConfigured` on an invalid htmx POST. Under normal usage (default `htmx_form_component="form"`), neither guard is triggered.

### Tests for US2 ⚠️ Write FIRST, confirm failing before T023

- [X] T019 [US2] Write test `test_missing_success_component_raises_improperly_configured`: htmx POST with valid data on a view where `htmx_success_component` is `None` and `htmx_redirect_on_success=False` raises `ImproperlyConfigured` in `tests/test_views/test_htmx_form_mixin.py`
- [X] T020 [US2] Write test `test_missing_form_component_raises_improperly_configured`: htmx POST with invalid data on a view where `htmx_form_component` is explicitly set to `None` (overriding the default `"form"`) raises `ImproperlyConfigured` in `tests/test_views/test_htmx_form_mixin.py`
- [X] T021 [US2] Write tests `test_get_htmx_success_component_override_used` and `test_get_htmx_form_component_override_used`: subclasses that override `get_htmx_success_component()` / `get_htmx_form_component()` to return a different component name have that name used by `render_component()` in `tests/test_views/test_htmx_form_mixin.py`
- [X] T021a [US2] Run `pytest tests/test_views/test_htmx_form_mixin.py -k "improperly or component_override"` — confirm US2 tests FAIL

### Implementation for US2

- [X] T022 [US2] Implement `get_htmx_success_component()` in `mvp/views/htmx.py`: return `self.htmx_success_component` if truthy; raise `ImproperlyConfigured("HtmxFormMixin requires 'htmx_success_component' or 'htmx_redirect_on_success = True'.")` otherwise
- [X] T023 [US2] Implement `get_htmx_form_component()` in `mvp/views/htmx.py`: return `self.htmx_form_component` if truthy; raise `ImproperlyConfigured("HtmxFormMixin requires 'htmx_form_component' to be set.")` otherwise
- [X] T024 [US2] Update `form_valid()` to call `self.get_htmx_success_component()` only when `htmx_redirect_on_success` is falsy; update `form_invalid()` to call `self.get_htmx_form_component()` unconditionally when on the htmx path in `mvp/views/htmx.py`
- [X] T025 [US2] Run `pytest tests/test_views/test_htmx_form_mixin.py` — all US1 + US2 tests pass; run `python manage.py check`
- [X] T026 [US2] Playwright verification: (a) temporarily set `htmx_form_component = None` on the demo view class and restart the server; submit an invalid htmx POST → assert Django DEBUG error page contains `ImproperlyConfigured` and the text `htmx_form_component`; (b) restore `htmx_form_component` to its original value (or remove the override to restore the default `"form"`) and immediately run `pytest tests/test_views/test_htmx_form_mixin.py -x` to confirm the restoration — do not proceed until pytest is green; (c) reload the browser and submit a valid htmx POST → assert the success partial is returned normally; also verify a non-htmx GET renders the full page without errors

**Checkpoint**: US2 complete. Misconfiguration caught early with clear messages. Override hooks work.

---

## Phase 5: US3 — Return an HX-Redirect Header on Success (Priority: P2)

**Goal**: When `htmx_redirect_on_success = True`, return `HttpResponseClientRedirect(success_url)` on a valid htmx POST. When both `htmx_redirect_on_success` and `htmx_success_component` are set, redirect takes precedence.

**Independent Test**: A mixin-enhanced view with `htmx_redirect_on_success = True` receiving a valid htmx POST returns a response with `HX-Redirect` header set to the resolved `success_url`; no partial body is rendered.

### Tests for US3 ⚠️ Write FIRST, confirm failing before T030

- [X] T027 [US3] Write test `test_htmx_redirect_on_success_returns_client_redirect`: valid htmx POST on a view with `htmx_redirect_on_success=True` returns `HttpResponseClientRedirect` with `HX-Redirect` header equal to `get_success_url()` in `tests/test_views/test_htmx_form_mixin.py`
- [X] T028 [US3] Write test `test_redirect_takes_precedence_over_success_component`: view with both `htmx_redirect_on_success=True` and `htmx_success_component` set returns `HttpResponseClientRedirect`, not the partial in `tests/test_views/test_htmx_form_mixin.py`
- [X] T028a [US3] Run `pytest tests/test_views/test_htmx_form_mixin.py -k "redirect"` — confirm US3 tests FAIL

### Implementation for US3

- [X] T029 [US3] Update `form_valid()` htmx branch in `mvp/views/htmx.py`: before the `render_component()` path, add `if self.htmx_redirect_on_success: return HttpResponseClientRedirect(self.get_success_url())`; import `HttpResponseClientRedirect` from `django_htmx.http` at top of file
- [X] T030 [US3] Run `pytest tests/test_views/test_htmx_form_mixin.py` — all US1 + US2 + US3 tests pass; run `python manage.py check`
- [X] T031 [US3] Playwright verification: configure the demo view with `htmx_redirect_on_success = True`; submit valid data via htmx → assert browser navigates to the success URL (full navigation, no partial swap); restore demo view to partial-swap mode after verification

**Checkpoint**: US3 complete. `HX-Redirect` path working; redirect takes precedence over partial.

---

## Phase 6: US4 — Emit HTMX Response Triggers on Success (Priority: P3)

**Goal**: When `htmx_trigger` is a string or dict, call `trigger_client_event()` on the success response (both partial and redirect paths) using the timing from `htmx_trigger_after`.

**Independent Test**: A mixin-enhanced view with `htmx_trigger = "itemCreated"` returns a success response bearing the `HX-Trigger: itemCreated` header (applied by `trigger_client_event(response, "itemCreated", after="receive")`).

### Tests for US4 ⚠️ Write FIRST, confirm failing before T036

- [X] T032 [US4] Write test `test_htmx_trigger_string_adds_hx_trigger_header`: valid htmx POST with `htmx_trigger="itemCreated"` returns a response with `HX-Trigger` header containing `"itemCreated"` in `tests/test_views/test_htmx_form_mixin.py`
- [X] T033 [US4] Write test `test_htmx_trigger_dict_adds_events_for_each_key`: `htmx_trigger={"eventA": None, "eventB": {"id": 1}}` results in both events present in the trigger header in `tests/test_views/test_htmx_form_mixin.py`
- [X] T034 [US4] Write tests `test_htmx_trigger_after_settle_uses_correct_header` (response has `HX-Trigger-After-Settle`, not `HX-Trigger`) and `test_htmx_trigger_after_swap_uses_correct_header` in `tests/test_views/test_htmx_form_mixin.py`
- [X] T035 [US4] Write test `test_htmx_trigger_none_adds_no_trigger_header`: when `htmx_trigger` is `None` no `HX-Trigger` family header is added to the response in `tests/test_views/test_htmx_form_mixin.py`
- [X] T035a [US4] Run `pytest tests/test_views/test_htmx_form_mixin.py -k "trigger"` — confirm US4 tests FAIL

### Implementation for US4

- [X] T036 [US4] Add `_apply_htmx_triggers(self, response)` private method to `HtmxFormMixin` in `mvp/views/htmx.py`: no-op when `htmx_trigger` is falsy; calls `trigger_client_event(response, self.htmx_trigger, after=self.htmx_trigger_after)` for a string; iterates `self.htmx_trigger.items()` and calls `trigger_client_event(response, name, params, after=self.htmx_trigger_after)` for each entry when a dict; import `trigger_client_event` from `django_htmx.http`
- [X] T037 [US4] Call `self._apply_htmx_triggers(response)` at the end of both the partial and redirect branches in `form_valid()` in `mvp/views/htmx.py`
- [X] T038 [US4] Run `pytest tests/test_views/test_htmx_form_mixin.py` — all US1 + US2 + US3 + US4 tests pass; run `python manage.py check`
- [X] T039 [US4] Playwright verification: (a) add `htmx_trigger = "productCreated"` to `HtmxProductCreateView` in `demo/views.py`; (b) update `demo/templates/htmx_demo.html` to add a `<div hx-get="{{ request.path }}" hx-trigger="productCreated from:body" hx-target="this">product count</div>` panel below the form container; (c) submit a valid htmx POST → assert the listening panel refreshes without a full-page reload; (d) revert both changes (htmx_trigger and the template panel) after verification — trigger emission is not a permanent feature of the demo view

**Checkpoint**: US4 complete. All four user stories fully functional.

---

## Phase 8: US5 — Select the Success Component from the Client Side (Priority: P3)

**Goal**: When `htmx_success_components` is configured, allow the requesting htmx element to select the success component via the `X-Success-Component` request header. The view's allowlist controls which components are reachable. Unknown aliases fall through to the server default silently. The feature is fully opt-in (empty tuple = header always ignored).

**Independent Test**: A view configured with `htmx_success_components = (("list", "product.list-item"), ("detail", "product.detail-card"))` and `htmx_success_component = "product.detail-card"` receives a valid htmx POST with `X-Success-Component: list` → `render_component` is called with `"product.list-item"`. The same view with an unknown alias or no header uses the fallback. A view with no `htmx_success_components` ignores the header.

### Tests for US5

- [X] T045 [US5] Write test `test_x_success_component_header_resolves_via_allowlist`: valid alias in `X-Success-Component` header → `render_component` called with the paired component, not the default `htmx_success_component` in `tests/test_views/test_htmx_form_mixin.py`
- [X] T046 [US5] Write test `test_x_success_component_unknown_alias_falls_through_to_default`: unknown alias in `X-Success-Component` header → silently falls through; `render_component` called with `htmx_success_component` in `tests/test_views/test_htmx_form_mixin.py`
- [X] T047 [US5] Write test `test_x_success_component_header_ignored_when_allowlist_empty`: `X-Success-Component` header present but `htmx_success_components` is empty → header is ignored, server default used in `tests/test_views/test_htmx_form_mixin.py`

### Implementation for US5

- [X] T048 [US5] Add `htmx_success_components: tuple = ()` class attribute to `HtmxFormMixin` in `mvp/views/htmx.py`
- [X] T049 [US5] Update `get_htmx_success_component()` in `mvp/views/htmx.py`: before the server-default check, if `htmx_success_components` is non-empty, read `self.request.headers.get("X-Success-Component", "").strip()`, look up the alias in `dict(self.htmx_success_components)`, and return the component if found; unknown aliases fall through silently to the existing server-default path
- [X] T050 [US5] Run `pytest tests/test_views/test_htmx_form_mixin.py -q --tb=short` — all 21 tests pass; run `poetry run ruff check mvp/views/htmx.py` — zero violations

**Checkpoint**: US5 complete. Client-driven component selection works. Unknown aliases and opt-out (empty allowlist) both behave correctly.

---

## Phase 9: Architectural Refactor — HtmxMixin Base Class

**Purpose**: Extract `get_context_data()` / `htmx_enabled` injection from `HtmxFormMixin` into a new `HtmxMixin` base class so that future htmx view types (e.g., `HtmxListMixin`) can inherit context injection without depending on form-specific logic. `HtmxFormMixin` continues to work identically — this is a backward-compatible internal refactor.

**Independent Test**: A plain CBV enhanced with only `HtmxMixin` (no `HtmxFormMixin`) has `htmx_enabled = True` in its rendered context. A CBV using `HtmxFormMixin` also has `htmx_enabled = True` via inheritance from `HtmxMixin`. All 22 existing tests still pass.

### Tests for Phase 9 ⚠️ Write FIRST

- [X] T051 [P] Write test `test_htmx_mixin_standalone_injects_htmx_enabled`: build a minimal `TemplateView` subclass using only `HtmxMixin` (not `HtmxFormMixin`), call `get_context_data()`, and assert `htmx_enabled` is `True` in the returned context — in `tests/test_views/test_htmx_form_mixin.py`

### Implementation for Phase 9

- [X] T052 Create `HtmxMixin` class in `mvp/views/htmx.py` (above `HtmxFormMixin`) with a single method: `get_context_data(self, **kwargs)` that calls `super().get_context_data(**kwargs)`, sets `context["htmx_enabled"] = True`, and returns the context. Add a class docstring describing its purpose and future extensibility.
- [X] T053 Update `HtmxFormMixin` in `mvp/views/htmx.py`: (a) add `HtmxMixin` as its first base class — `class HtmxFormMixin(HtmxMixin):`, (b) remove the `get_context_data()` method body from `HtmxFormMixin` (it is now inherited), (c) update the class docstring to note inheritance from `HtmxMixin`.
- [X] T054 Run `pytest tests/test_views/test_htmx_form_mixin.py --cov=mvp.views.htmx --cov-branch -q` — all 23 tests pass (22 existing + T051), 100% branch coverage maintained on `mvp/views/htmx.py`.
- [X] T055 Run `poetry run ruff check mvp/views/htmx.py tests/test_views/test_htmx_form_mixin.py` and `poetry run python manage.py check` — zero violations.

**Checkpoint**: `HtmxMixin` is importable standalone. `HtmxFormMixin` inherits from it. All existing behaviour unchanged. Class hierarchy is extensible for future htmx mixins.

---

## Phase 10: Expand HtmxMixin — Trigger Subsystem + Resolve Helper (FR-027, FR-028)

**Purpose**: Move the trigger subsystem (`htmx_trigger`, `htmx_trigger_after`, `_apply_htmx_triggers()`) from `HtmxFormMixin` to `HtmxMixin` so that any future htmx view type can emit client-side events without form-specific inheritance. Add `_resolve_component(attr, allowlist_attr, header_name)` as a shared helper on `HtmxMixin` for client-driven component selection. Update `HtmxFormMixin.get_htmx_success_component()` to delegate to `_resolve_component()` rather than containing the lookup logic inline. This is a backward-compatible internal refactor — the public API of `HtmxFormMixin` is unchanged.

**Independent Test**: A plain `HtmxMixin` subclass (no `HtmxFormMixin`) can call `_apply_htmx_triggers(response)` and `_resolve_component(attr, allowlist_attr, header_name)` directly. All 23 existing tests continue to pass.

### Tests for Phase 10 ⚠️ Write FIRST

- [X] T056 [P] Write test `test_htmx_mixin_apply_triggers_standalone`: build a minimal `HtmxMixin + TemplateView` stub with `htmx_trigger = "ping"`; create a plain `HttpResponse()`; call `view._apply_htmx_triggers(response)` on it; assert the `HX-Trigger` response header contains `"ping"` — in `tests/test_views/test_htmx_form_mixin.py`
- [X] T057 [P] Write test `test_resolve_component_client_header_priority`: build a minimal `HtmxMixin + TemplateView` stub with attributes `my_comp = "default.comp"` and `my_comps = (("list", "list.item"),)`; attach a GET request bearing `HTTP_X_SUCCESS_COMPONENT=list`; call `view._resolve_component("my_comp", "my_comps", "X-Success-Component")`; assert `"list.item"` is returned — in `tests/test_views/test_htmx_form_mixin.py`
- [X] T058 [P] Write test `test_resolve_component_empty_allowlist_ignores_header`: same setup with `my_comps = ()`; assert `"default.comp"` is returned even when header is present — in `tests/test_views/test_htmx_form_mixin.py`
- [X] T059 [P] Write test `test_resolve_component_unknown_alias_falls_through`: allowlist is `(("detail", "detail.card"),)` but header sends `X-Success-Component: list`; assert `"default.comp"` is returned — in `tests/test_views/test_htmx_form_mixin.py`

### Implementation for Phase 10

- [X] T060 Move `htmx_trigger = None` and `htmx_trigger_after = "receive"` class attributes from `HtmxFormMixin` to `HtmxMixin` in `mvp/views/htmx.py`
- [X] T061 Move `_apply_htmx_triggers(self, response)` method body from `HtmxFormMixin` to `HtmxMixin` in `mvp/views/htmx.py`; verify `HtmxFormMixin.form_valid()` still calls `self._apply_htmx_triggers(response)` (inherited, no change needed)
- [X] T062 Add `_resolve_component(self, attr, allowlist_attr, header_name)` to `HtmxMixin` in `mvp/views/htmx.py`: (a) read `allowlist = getattr(self, allowlist_attr, ())`; (b) if non-empty, look up `self.request.headers.get(header_name, "").strip()` in `dict(allowlist)`; return the component if found; (c) fall through to `return getattr(self, attr, None)`
- [X] T063 Refactor `HtmxFormMixin.get_htmx_success_component()` in `mvp/views/htmx.py` to delegate: call `self._resolve_component("htmx_success_component", "htmx_success_components", "X-Success-Component")`; if the result is truthy return it; otherwise raise `ImproperlyConfigured(...)` (guard stays in `HtmxFormMixin`); remove the inline allowlist lookup logic
- [X] T064 Run `pytest tests/test_views/test_htmx_form_mixin.py --cov=mvp.views.htmx --cov-branch -q` — all 27 tests pass (23 existing + T056–T059), 100% branch coverage maintained
- [X] T065 Run `poetry run ruff check mvp/views/htmx.py tests/test_views/test_htmx_form_mixin.py` and `poetry run python manage.py check` — zero violations

**Checkpoint**: `HtmxMixin` owns all non-form htmx concerns. `HtmxFormMixin` holds only form-specific logic. `HtmxListViewMixin` (future) can inherit trigger handling and component resolution from `HtmxMixin` without any code duplication.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Docstrings, export verification, coverage gate, full regression suite.

- [X] T040 [P] Write class and method docstrings for `HtmxFormMixin` in `mvp/views/htmx.py` (class-level attribute table, `form_valid()` / `form_invalid()` contracts, and a minimal usage example matching `specs/020-htmx-form-mixin/quickstart.md`)
- [X] T041 [P] Verify `from mvp.views import HtmxFormMixin` raises `ImportError` or `AttributeError` (it MUST NOT be exported from `__init__.py`); verify `from mvp.views.htmx import HtmxFormMixin` resolves correctly in a Python shell; confirm NO entry for `HtmxFormMixin` in `__all__` in `mvp/views/__init__.py`
- [X] T042 Run `pytest tests/test_views/test_htmx_form_mixin.py --cov=mvp/views/htmx --cov-report=term-missing` — confirm 100% branch coverage on `mvp/views/htmx.py` (SC-006)
- [X] T043 Run full test suite `poetry run pytest tests/` — all pre-existing tests pass; zero regressions on non-htmx paths (SC-002)
- [X] T044 Run `python manage.py check` and `ruff check mvp/views/htmx.py` — zero errors and zero linting violations

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)
    └─→ Phase 2 (Foundational) [BLOCKS all US phases]
            ├─→ Phase 3 (US1, P1) 🎯 MVP — start here
            │       └─→ Phase 4 (US2, P1) — completes P1 scope
            ├─→ Phase 5 (US3, P2) — independent of US2
            ├─→ Phase 6 (US4, P3) — independent of US2/US3
            └─→ Phase 8 (US5, P3) — independent of US2/US3/US4
                        └─→ Phase 7 (Polish)
                                └→ Phase 9 (HtmxMixin base class)
                                        └→ Phase 10 (Expand HtmxMixin: trigger + resolve)
```

### User Story Dependencies

| Story | Priority | Depends On | Can Overlap With |
|---|---|---|---|
| US1 | P1 | Phase 2 | — |
| US2 | P1 | US1 (fills in guards on existing logic) | US3, US4, US5 |
| US3 | P2 | Phase 2 | US2, US4, US5 |
| US4 | P3 | Phase 2 | US2, US3, US5 |
| US5 | P3 | Phase 2 | US2, US3, US4 |

### Parallel Opportunities Within Phases

| Phase | Parallel Tasks |
|---|---|
| Phase 1 | T001 and T002 (independent files) |
| Phase 2 | T005/T005a (test scaffold + context test) run in parallel with T003 and T004; T005b after T003 |
| Phase 3 | T013 (form component) and T014 (success component) run in parallel with T011/T012 |
| Phase 7 | T040 (docstrings) and T041 (export verify) run in parallel |

### Implementation Strategy (MVP-First Delivery)

1. **MVP** — Complete Phases 1–3 (US1 only). Delivers the core no-reload form submission value. Verify in browser.
2. **Increment 1** — Add Phase 4 (US2 guards). Completes all P1 scope.
3. **Increment 2** — Add Phase 5 (US3 redirect). Completes P2 scope.
4. **Increment 3** — Add Phase 6 (US4 triggers). Completes P3 scope.
5. **Increment 4** — Add Phase 8 (US5 client component selection). Completes extended P3 scope.
6. **Final** — Phase 7 polish, coverage gate, full regression.
7. **Refactor** — Phase 9 HtmxMixin base class extraction. Backward-compatible architectural cleanup.
