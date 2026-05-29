# Feature Specification: HTMX Form Mixin

**Feature Branch**: `020-htmx-form-mixin`
**Created**: 2026-05-28
**Status**: Refined
**Refined**: 2026-05-28 — Renamed `htmx_form_template`/`htmx_success_template` to `htmx_form_component`/`htmx_success_component`; defaulted `htmx_form_component` to `"form.card"`; demoted `django-htmx` to optional (not a package dep); removed `HtmxFormMixin` from `__init__.py` exports; added `htmx_enabled` context injection.
**Refined**: 2026-05-29 — Added `htmx_success_components` allowlist attribute and `X-Success-Component` client-driven component selection (User Story 5, FR-020–FR-024).
**Refined**: 2026-05-29 — Introduced `HtmxMixin` base class; moved `get_context_data()` / `htmx_enabled` injection out of `HtmxFormMixin` into `HtmxMixin`; `HtmxFormMixin` now inherits from `HtmxMixin` (FR-018 updated, FR-025–FR-026 added).
**Refined**: 2026-05-29 — Expanded `HtmxMixin` responsibilities: trigger subsystem (`htmx_trigger`, `htmx_trigger_after`, `_apply_htmx_triggers()`) and component resolution helper (`_resolve_component()`) move from `HtmxFormMixin` to `HtmxMixin` to enable reuse by future htmx view types such as `HtmxListViewMixin` (FR-025 updated, FR-027–FR-028 added, FR-026 updated).
**Input**: User description: "In modern django apps, progressive enhancement using libraries such as htmx can greatly enhance the user experience. One of the most common patterns is to submit a form via htmx and, on success, return a partial component or, on error, return the form itself. I would like to create a form mixin that optionally enhances our standard form views with htmx functionality."

## Clarifications

### Session 2026-05-28

- Q: Should the mixin depend on `django-htmx` and `django-cotton`? → A: Yes — the mixin is tightly coupled to both libraries; `django-htmx` (for `request.htmx`, `HttpResponseClientRedirect`, `trigger_client_event`) and `django-cotton` (for `render_component`) are required dependencies, not optional.
- Q: What HTTP status code should the form-error partial return? → A: 200 — matches django-htmx's own `retarget()` pattern and works with htmx's default response handling without any additional client-side configuration.
- Q: What is the correct response type for `htmx_redirect_on_success`? → A: `HttpResponseClientRedirect` from `django_htmx.http` (triggers a full client-side navigation via `HX-Redirect`); `HttpResponseLocation` (SPA-style) is out of scope.
- Q: Should `htmx_trigger` support timing variants (HX-Trigger-After-Settle, HX-Trigger-After-Swap)? → A: Yes — via a `htmx_trigger_after` attribute accepting `'receive'` (default, maps to `HX-Trigger`), `'settle'` (maps to `HX-Trigger-After-Settle`), or `'swap'` (maps to `HX-Trigger-After-Swap`), delegating to `trigger_client_event()` from django-htmx.
- Q: Should `htmx_form_template` have a default fallback when not set? → A: No — `render_component()` requires an explicit Cotton component name; raise `ImproperlyConfigured` if `htmx_form_template` is not set and an htmx POST results in an invalid form.
- Q: What happens to Django success messages (SuccessMessageMixin) when the mixin returns an htmx partial instead of a full page? → A: Consume and discard — after calling `super().form_valid()`, the mixin drains the session message queue via `get_messages(request)` so no stale toast appears on the next full-page navigation. Developers use `htmx_trigger` for htmx-appropriate success feedback instead.

### Refinement 2026-05-28

- Q: Should the attribute names `htmx_form_template` and `htmx_success_template` be renamed? → A: Yes — rename to `htmx_form_component` and `htmx_success_component` to make it explicit these are Cotton component names (dot-notation), not Django template paths. Corresponding accessor methods become `get_htmx_form_component()` and `get_htmx_success_component()`.
- Q: Should `htmx_form_component` have a default value? → A: Yes — default to `"form.card"`, the Cotton component used throughout the package's standard `form_view.html`. This allows the mixin to re-render the form into the standard card layout without requiring any custom component. Developers only override when a non-standard layout is needed.
- Q: Should `django-htmx` be a required package dependency? → A: No — `django-htmx` must be installed by developers who wish to use `HtmxFormMixin`; it is listed only as a dev/optional dependency of the package itself. Projects that do not use htmx should not be forced to include it.
- Q: Should `HtmxFormMixin` be exported from `mvp/views/__init__.py`? → A: No — importing it in `__init__.py` would cause an `ImportError` in projects without `django-htmx` installed. Developers import directly via `from mvp.views.htmx import HtmxFormMixin`.
- Q: Should the mixin inject a context variable to signal htmx-enablement? → A: Yes — inject `htmx_enabled = True` via `get_context_data()` so templates can conditionally render htmx-specific attributes (e.g., `hx-post`, `hx-target`, `hx-swap`) without duplicating configuration logic in templates.

### Refinement 2026-05-29

- Q: Can the requesting htmx element influence which success component is returned, without the view hardcoding every caller scenario? → A: Yes — the view declares an allowlist of `(alias, component)` pairs via `htmx_success_components`. The client sends `X-Success-Component: <alias>` as a request header; if the alias is found in the allowlist the associated component is returned, otherwise the request silently falls through to the server default. This is opt-in: an empty `htmx_success_components` (the default) means the header is always ignored.
- Q: Should an unknown alias raise an error or fall through? → A: Fall through silently to the server default (`htmx_success_component`). Raising would break future compatibility if a new alias is introduced server-side but not yet in the client's header value, and would expose internal component names to error messages.
- Q: What takes priority — the client header or the server default? → A: Client header wins when `htmx_success_components` is non-empty and the alias resolves; this allows different page contexts (e.g., a list page vs. a detail page) to request the component that fits their swap target without server-side knowledge of the caller.
- Q: What data type should `htmx_success_components` use? → A: A tuple of 2-tuples — `tuple[tuple[str, str], ...]` — matching Django's convention for field `choices`. This makes the allowlist hashable, avoids mutable-default pitfalls, and is easy to override per view class.

### Refinement 2026-05-29 (second)

- Q: Should the `htmx_enabled` context injection be pulled out of `HtmxFormMixin` into a dedicated base class? → A: Yes — create `HtmxMixin` as a lightweight base that provides functionality useful to *all* htmx-enhanced views (not only form views). `HtmxFormMixin` inherits from `HtmxMixin` so the context injection is still active without any change to existing usage.
- Q: What other behaviour belongs in `HtmxMixin` at this stage? → A: Only `get_context_data()` (injecting `htmx_enabled = True`) for now. Future functionality (e.g., common request-detection helpers, trigger utilities) can be added to `HtmxMixin` without touching `HtmxFormMixin`.
- Q: Where does `HtmxMixin` live? → A: Same module — `mvp/views/htmx.py` — so that the file remains the single import location for all htmx-related mixins. Import: `from mvp.views.htmx import HtmxMixin`.
- Q: Is this change backward-compatible? → A: Yes — the public API of `HtmxFormMixin` is unchanged; `htmx_enabled` remains in context exactly as before. The only implementation change is where `get_context_data()` is defined in the class hierarchy.

### Refinement 2026-05-29 (third)

- Q: Anticipating a future `HtmxListViewMixin`, which parts of `HtmxFormMixin` are reusable by other htmx view types? → A: Two subsystems have zero form dependency. (1) The **trigger subsystem** (`htmx_trigger`, `htmx_trigger_after`, `_apply_htmx_triggers()`) applies `HX-Trigger` family headers to any htmx response — not just form submissions. (2) The **allowlist resolution logic** (request-header lookup, dict conversion, fallback to server default) is the same pattern any htmx view would need for client-driven component selection. Both belong in `HtmxMixin`. Form-specific concerns (`htmx_success_component`, `htmx_success_components`, `htmx_form_component`, `htmx_redirect_on_success`, `form_valid()`, `form_invalid()`) remain in `HtmxFormMixin`.
- Q: Should `_apply_htmx_triggers()` move to `HtmxMixin` or stay in `HtmxFormMixin`? → A: Move to `HtmxMixin`. Its signature `_apply_htmx_triggers(response)` is purely response-level — it wraps `trigger_client_event()` calls and has no knowledge of form state. `HtmxFormMixin.form_valid()` continues to call `self._apply_htmx_triggers(response)` but inherits the implementation.
- Q: How should the allowlist resolution logic be shared? → A: Introduce `_resolve_component(attr, allowlist_attr, header_name)` as a private helper on `HtmxMixin`. It reads the server-default component from `getattr(self, attr)`, the allowlist from `getattr(self, allowlist_attr)`, and the client alias from `self.request.headers.get(header_name)`. Returns the resolved component name (or `None` if nothing resolves). `HtmxFormMixin.get_htmx_success_component()` delegates to `self._resolve_component("htmx_success_component", "htmx_success_components", "X-Success-Component")`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Submit a Form Without a Full Page Reload (Priority: P1)

As a user filling in a form on a page that uses htmx, I want the form to submit and receive feedback (success or validation errors) without the entire page reloading — so that the interaction feels fluid and the rest of the page state is preserved.

**Audience**: End user interacting with an htmx-enhanced form.

**Why this priority**: This is the core value proposition of the feature. Without it, the mixin provides no benefit.

**Independent Test**: A view enhanced with the mixin is submitted via an htmx POST. On success, an `HttpResponse` whose body is the output of `render_component()` for `htmx_success_component` is returned; on validation failure, an `HttpResponse` (status 200) whose body is the output of `render_component()` for `htmx_form_component` is returned — neither response triggers a full page navigation.

**Acceptance Scenarios**:

1. **Given** a view enhanced with the mixin is requested normally (no htmx headers), **When** a GET request is made, **Then** the full page layout is rendered — no difference from a non-enhanced view.
2. **Given** a view enhanced with the mixin receives an htmx POST with valid data, **When** the form is valid, **Then** the response contains only the configured success partial (no full page layout).
3. **Given** a view enhanced with the mixin receives an htmx POST with invalid data, **When** the form is invalid, **Then** the response contains only the re-rendered form partial with validation errors visible.
4. **Given** a view enhanced with the mixin receives a non-htmx POST (standard browser submit), **When** the form is valid, **Then** the view behaves identically to the unenhanced base view (e.g., performs a redirect to `success_url`).
5. **Given** a view enhanced with the mixin receives a non-htmx POST with invalid data, **When** the form is invalid, **Then** the full page is re-rendered with the form and errors — no partial is returned.

---

### User Story 2 — Wire Up HTMX Enhancement with Minimal Configuration (Priority: P1)

As a developer adding htmx behaviour to an existing form view, I want to mix in a single class and set at most one or two attributes — so that I can progressively enhance any of the package's existing form views without rewriting them or duplicating logic.

**Audience**: Developer (integrator).

**Why this priority**: Ease of adoption is essential. If wiring requires significant boilerplate, developers will write their own ad-hoc solutions, defeating the purpose of a shared mixin.

**Independent Test**: An existing `MVPCreateView` subclass gains htmx behaviour by adding the mixin to its inheritance chain and setting `htmx_success_component` (a Cotton component name). `htmx_form_component` defaults to `"form.card"` and does not need to be set. No other changes are required — the view continues to work normally for non-htmx requests.

**Acceptance Scenarios**:

1. **Given** a developer adds the mixin to an existing form view class and sets `htmx_success_component` (and optionally `htmx_form_component`), **When** the view receives a normal (non-htmx) request, **Then** the view behaves exactly as before — no regression.
2. **Given** `htmx_success_component` is not set on a mixin-enhanced view and `htmx_redirect_on_success` is False, **When** the view receives an htmx POST with valid data, **Then** `ImproperlyConfigured` is raised directing the developer to configure `htmx_success_component` or enable `htmx_redirect_on_success`.
3. **Given** `htmx_form_component` is explicitly cleared (set to `None` or `""`) on a mixin-enhanced view, **When** the view receives an htmx POST with invalid data, **Then** `ImproperlyConfigured` is raised. Under normal usage (default `"form.card"`), this guard is never triggered.

---

### User Story 3 — Return an HX-Redirect Header on Success Instead of a Partial (Priority: P2)

As a developer building a form that should navigate the user to a new page after htmx submission (rather than swapping a partial), I want to configure the mixin to respond with an `HX-Redirect` header on success — so that htmx triggers a client-side navigation without me writing a custom `form_valid()` override.

**Audience**: Developer (integrator).

**Why this priority**: The partial-swap pattern covers inline forms, but many forms (create/update) naturally conclude with navigation. A redirect-via-htmx response pattern is the idiomatic way to handle this.

**Independent Test**: A mixin-enhanced view configured with `htmx_redirect_on_success = True` responds to a valid htmx POST with an `HttpResponseClientRedirect` containing an `HX-Redirect` header pointing to the resolved `success_url`. No partial component is rendered.

**Acceptance Scenarios**:

1. **Given** `htmx_redirect_on_success = True` is set and a valid htmx POST is received, **When** the form is valid, **Then** the response has an `HX-Redirect` header set to the resolved success URL and no page body is returned.
2. **Given** `htmx_redirect_on_success = True` is set and an invalid htmx POST is received, **When** the form is invalid, **Then** the form partial is returned with errors as normal (the redirect setting only applies to the success path).
3. **Given** neither `htmx_success_component` nor `htmx_redirect_on_success` is set and an htmx POST is submitted, **When** the form is valid, **Then** a clear error is raised directing the developer to configure one of the two options.

---

### User Story 4 — Emit HTMX Response Triggers on Success (Priority: P3)

As a developer building a page where other components need to react to a successful form submission (e.g., refreshing a list), I want to configure the mixin to emit an `HX-Trigger` header on success — so that other htmx-powered elements on the page update automatically without writing JavaScript.

**Audience**: Developer (integrator).

**Why this priority**: Trigger headers are a common htmx pattern for coordinating page components. Supporting them declaratively avoids developers having to override `form_valid()` solely to add a response header.

**Independent Test**: A mixin-enhanced view configured with `htmx_trigger = "itemCreated"` responds to a valid htmx POST with a response where `trigger_client_event(response, "itemCreated", after='receive')` has been applied, regardless of whether `htmx_success_component` or `htmx_redirect_on_success` is used.

**Acceptance Scenarios**:

1. **Given** `htmx_trigger = "itemCreated"` is set, **When** a valid htmx POST is received, **Then** the response includes an `HX-Trigger: itemCreated` header (applied via `trigger_client_event` with `after='receive'`).
2. **Given** `htmx_trigger` is not set, **When** a valid htmx POST is received, **Then** no `HX-Trigger` header is added to the response.
3. **Given** `htmx_trigger` is set to a dict `{"itemCreated": {"id": 1}}`, **When** a valid htmx POST is received, **Then** `trigger_client_event` is called once per entry, with each event name and its params dict.
4. **Given** `htmx_trigger_after = "settle"` is set alongside `htmx_trigger`, **When** a valid htmx POST is received, **Then** the response includes `HX-Trigger-After-Settle` (not `HX-Trigger`) for the configured event.

---

### User Story 5 — Select the Success Component from the Client Side (Priority: P3)

As a developer embedding the same form endpoint in multiple page contexts (e.g., a product-list page and a product-detail page), I want each htmx caller to specify which success component should be swapped in after a valid submission — so that a single view endpoint can serve different swap targets without needing separate views or URL parameters.

**Audience**: Developer (integrator).

**Why this priority**: The partial-swap pattern often requires different views to serve different page regions. A client-driven allowlist lets one endpoint remain the single source of truth while callers elect their own swap target.

**Independent Test**: A view is configured with `htmx_success_components = (("list", "product.list-item"), ("detail", "product.detail-card"))` and `htmx_success_component = "product.detail-card"` (fallback). When a valid htmx POST arrives with `X-Success-Component: list`, `render_component` is called with `"product.list-item"`. When the header is absent (or an unknown alias), the fallback `"product.detail-card"` is used. When no `htmx_success_components` is configured, the header is ignored entirely.

**Acceptance Scenarios**:

1. **Given** `htmx_success_components` is configured with valid pairs and the client sends `X-Success-Component` with a known alias, **When** a valid htmx POST is received, **Then** the success partial rendered is the component paired with that alias.
2. **Given** `htmx_success_components` is configured and the client sends `X-Success-Component` with an alias that is **not** in the allowlist, **When** a valid htmx POST is received, **Then** the mixin falls through silently and renders `htmx_success_component` (the server default).
3. **Given** `htmx_success_components` is **not configured** (empty tuple, the default) and the client sends `X-Success-Component`, **When** a valid htmx POST is received, **Then** the header is ignored and the server default `htmx_success_component` is used — the feature is fully opt-in.
4. **Given** `htmx_success_components` is configured and the client sends a known alias, **When** an htmx POST results in an **invalid** form, **Then** the component-selection logic does not apply — the form-error partial (`htmx_form_component`) is rendered as normal.

---

### Edge Cases

- What happens when a form view enhanced with the mixin is accessed by a client that sends no htmx request headers? → `request.htmx` evaluates to `False`; the mixin is transparent and the view behaves exactly as its unenhanced base class would.
- What happens when `htmx_success_component` or `htmx_form_component` references a Cotton component that does not exist? → Django's standard `TemplateDoesNotExist` exception is raised by the template engine — no special handling needed.
- What happens if the developer sets both `htmx_success_component` and `htmx_redirect_on_success`? → `htmx_redirect_on_success` takes precedence; `htmx_success_component` is ignored on the success path (document this in FR-013 and class docstring).
- What happens on a multi-step form or wizard step where `success_url` is not defined and `htmx_redirect_on_success = True`? → Same behaviour as the base view — `ImproperlyConfigured` is raised if the base class cannot determine a redirect URL.
- What happens when the view is used in a context where htmx is not loaded on the client? → `request.htmx` evaluates to `False`; the mixin is never activated; the view behaves as a standard Django form view.
- What happens to Django success messages when the mixin returns an htmx partial? → Messages queued by `SuccessMessageMixin.form_valid()` are consumed and discarded by calling `get_messages(request)` immediately after; they will not appear as stale toasts on the next full-page navigation. Use `htmx_trigger` to deliver equivalent feedback over htmx.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The mixin MUST detect whether a request was initiated by htmx via `request.htmx` provided by `django-htmx`'s `HtmxMiddleware`; raw header inspection is not used.
- **FR-002**: The mixin MUST be composable with any of the package's existing form view classes (`MVPFormView`, `MVPCreateView`, `MVPUpdateView`, `MVPDeleteView`) without requiring changes to those base classes.
- **FR-003**: When an htmx POST results in a valid form, the mixin MUST return an `HttpResponse` whose body is the output of `render_component(request, htmx_success_component, context)` from `django_cotton`, if `htmx_redirect_on_success` is falsy.
- **FR-004**: When an htmx POST results in a valid form and `htmx_redirect_on_success` is truthy, the mixin MUST return `HttpResponseClientRedirect(success_url)` from `django_htmx.http`, triggering a full client-side navigation via the `HX-Redirect` header.
- **FR-005**: When an htmx POST results in an invalid form, the mixin MUST return an `HttpResponse` (status 200) whose body is the output of `render_component(request, htmx_form_component, context)` from `django_cotton`.
- **FR-006**: The mixin MUST pass the full view context (including the bound form instance with errors) to `render_component()` on validation failure, so that form errors are visible and the Cotton component has access to all context variables.
- **FR-007**: When `htmx_trigger` is set to a non-empty string or dict, the mixin MUST call `trigger_client_event(response, name, params, after=htmx_trigger_after)` from `django_htmx.http` on successful htmx responses.
- **FR-008**: When `htmx_trigger` is a string, it is passed as the event `name` with no `params`; when it is a dict, it is interpreted as `{name: params}` pairs and each entry is added via a separate `trigger_client_event()` call.
- **FR-009**: The mixin MUST NOT alter the behaviour of the base view for any non-htmx request (GET or POST).
- **FR-010**: When `htmx_success_component` is not set and `htmx_redirect_on_success` is falsy, and the view receives a valid htmx POST, the mixin MUST raise `ImproperlyConfigured` with a clear error message directing the developer to set `htmx_success_component` or enable `htmx_redirect_on_success`.
- **FR-011**: When `htmx_form_component` is falsy (explicitly cleared) and the view receives an htmx POST that results in an invalid form, the mixin MUST raise `ImproperlyConfigured`. Under default usage (`htmx_form_component = "form.card"`) this guard is never reached.
- **FR-012**: The mixin MUST support overriding `get_htmx_success_component()` and `get_htmx_form_component()` for dynamic Cotton component name resolution per request.
- **FR-013**: When both `htmx_success_component` and `htmx_redirect_on_success` are set, the redirect MUST take precedence on the success path; the success component is ignored.
- **FR-014**: The `htmx_trigger_after` attribute MUST accept `'receive'` (default, maps to `HX-Trigger`), `'settle'` (maps to `HX-Trigger-After-Settle`), or `'swap'` (maps to `HX-Trigger-After-Swap`).
- **FR-015**: When returning an htmx partial on the success path, the mixin MUST drain Django's session message queue via `get_messages(request)` after `super().form_valid()` returns, so that no queued success message surfaces as a stale toast on the next full-page navigation. This behaviour applies only to htmx paths; non-htmx paths leave message handling entirely to the base class.
- **FR-016**: `django-htmx` MUST NOT be declared as a required package dependency in `pyproject.toml`. It is a dev dependency of the package itself. Developers who wish to use `HtmxFormMixin` in their own projects must install `django-htmx` themselves and add `HtmxMiddleware` to their `MIDDLEWARE` setting.
- **FR-017**: `HtmxFormMixin` MUST NOT be exported from `mvp/views/__init__.py` or included in `__all__`. Developers import it directly via `from mvp.views.htmx import HtmxFormMixin`. This prevents `ImportError` in projects that do not have `django-htmx` installed.
- **FR-018**: `HtmxMixin` MUST inject `htmx_enabled = True` into the view context by overriding `get_context_data()`. This allows templates to conditionally render htmx-specific element attributes (e.g., `hx-post`, `hx-target`, `hx-swap`) based on whether the mixin is active. Non-htmx views do not have this variable in context (evaluates as falsy). Because `HtmxFormMixin` inherits from `HtmxMixin`, no change to existing `HtmxFormMixin` usage is required.
- **FR-019**: The default value of `htmx_form_component` MUST be `"form.card"` — the Cotton component used by the package's standard `form_view.html` template. This default enables immediate form error re-rendering without any additional component authoring. Developers only need to override it when the page uses a non-standard card layout.
- **FR-020**: The mixin MUST support an `htmx_success_components` class attribute — a tuple of `(alias, component)` 2-tuples — that defines an allowlist of Cotton components the requesting htmx element may select via the `X-Success-Component` request header. The default value MUST be an empty tuple (opt-in; the header is ignored unless the allowlist is configured).
- **FR-021**: When `htmx_success_components` is non-empty and the `X-Success-Component` request header is present and matches a known alias, `get_htmx_success_component()` MUST return the component name paired with that alias (client choice takes priority over the server default).
- **FR-022**: When the `X-Success-Component` header value is not found in the allowlist, the mixin MUST fall through silently to the server default (`htmx_success_component`). No error or warning is raised for unknown aliases.
- **FR-023**: When `htmx_success_components` is empty (the default), the `X-Success-Component` header MUST be ignored entirely, even if present in the request. The feature is strictly opt-in.
- **FR-024**: The component-selection logic defined in FR-020–FR-023 MUST apply only to the success path (`form_valid()`). The `X-Success-Component` header MUST have no effect on the form-error path (`form_invalid()`).
- **FR-025**: `HtmxMixin` MUST be defined in `mvp/views/htmx.py` as a lightweight base class for all htmx-enhanced views. It MUST contain: (a) `get_context_data()` (FR-018), (b) `htmx_trigger` and `htmx_trigger_after` class attributes (moved from `HtmxFormMixin`), (c) `_apply_htmx_triggers(response)` private method (moved from `HtmxFormMixin`), and (d) `_resolve_component(attr, allowlist_attr, header_name)` private helper method (new). It MUST NOT contain form-specific logic. Import path: `from mvp.views.htmx import HtmxMixin`.
- **FR-026**: `HtmxFormMixin` MUST inherit from `HtmxMixin`. The following MUST be removed from `HtmxFormMixin` and inherited instead: `get_context_data()`, `htmx_trigger`, `htmx_trigger_after`, `_apply_htmx_triggers()`. `HtmxFormMixin.get_htmx_success_component()` MUST delegate to `self._resolve_component("htmx_success_component", "htmx_success_components", "X-Success-Component")` (inherited from `HtmxMixin`) rather than containing the lookup logic inline. The MRO must ensure the cooperative `super()` chain is preserved.
- **FR-027**: `HtmxMixin` MUST declare `htmx_trigger = None` and `htmx_trigger_after = "receive"` as class-level defaults, and MUST implement `_apply_htmx_triggers(response)` — the same logic previously in `HtmxFormMixin`. Any future htmx mixin subclass (e.g., `HtmxListViewMixin`) inherits this subsystem without duplication.
- **FR-028**: `HtmxMixin` MUST implement `_resolve_component(self, attr, allowlist_attr, header_name)` as a private helper. Given: (a) `allowlist = getattr(self, allowlist_attr, ())` — if non-empty, look up `self.request.headers.get(header_name, "").strip()` in `dict(allowlist)`; return the component if found. (b) Fall through to `getattr(self, attr, None)` as the server default. Returns the resolved component name string or `None`.

### Key Entities

- **HtmxMixin**: Lightweight base class for all htmx-enhanced views. Attributes: `htmx_trigger` (str | dict | None, default `None`), `htmx_trigger_after` (Literal['receive', 'settle', 'swap'], default `'receive'`). Methods: `get_context_data()` (override — injects `htmx_enabled = True`), `_apply_htmx_triggers(response)` (applies `HX-Trigger` family headers to any htmx response), `_resolve_component(attr, allowlist_attr, header_name)` (shared allowlist resolution helper — looks up request header against the allowlist attribute, falls back to the server-default attribute). No form-specific attributes or methods. Import path: `from mvp.views.htmx import HtmxMixin` (not exported from `mvp/views/__init__.py`).
- **HtmxFormMixin** (`HtmxMixin` subclass): Form-specific htmx mixin. Inherits from `HtmxMixin`: `get_context_data()`, `htmx_trigger`, `htmx_trigger_after`, `_apply_htmx_triggers()`, `_resolve_component()`. Own attributes: `htmx_success_component` (str | None — Cotton component name in dot notation, no default), `htmx_success_components` (tuple[tuple[str, str], ...], default `()` — allowlist of `(alias, component)` pairs enabling client-driven component selection via the `X-Success-Component` request header), `htmx_form_component` (str, default `"form.card"` — Cotton component name in dot notation), `htmx_redirect_on_success` (bool, default False). Own methods: `get_htmx_success_component()` (delegates to `_resolve_component()`), `get_htmx_form_component()`, `form_valid()` (override), `form_invalid()` (override). Import path: `from mvp.views.htmx import HtmxFormMixin` (not exported from `mvp/views/__init__.py`).
- **render_component** (`django_cotton`): Renders a Cotton component to an HTML string given a request, component name, and context dict. Used by the mixin to produce partial responses.
- **HttpResponseClientRedirect** (`django_htmx.http`): Response class that sets `HX-Redirect`, causing htmx to perform a full client-side navigation to the target URL.
- **trigger_client_event** (`django_htmx.http`): Modifies a response to include `HX-Trigger` / `HX-Trigger-After-Settle` / `HX-Trigger-After-Swap` headers for client-side event dispatch.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer adds htmx enhancement to any existing package form view by adding the mixin to the class definition and setting `htmx_success_component` (plus optionally `htmx_redirect_on_success` and `htmx_form_component` to override the default `"form.card"`) — verified by integration examples in the package's demo app.
- **SC-002**: All existing form view tests continue to pass without modification after the mixin is introduced — confirming zero regression on non-htmx paths.
- **SC-003**: An htmx POST to a valid form returns a response in which no full page layout markup is present — only the content of the configured partial template.
- **SC-004**: An htmx POST to an invalid form returns a response in which form validation errors are present and the response contains no full page layout markup.
- **SC-005**: The `HX-Redirect` header, when set, contains the exact same URL that a non-htmx submission would redirect to — ensuring redirect logic is not duplicated.
- **SC-006**: The mixin ships with unit tests achieving 100% branch coverage on the htmx detection and response-branching logic.

## Assumptions

- The package's target audience already uses or intends to use htmx in their projects; the mixin does not install or configure htmx itself.
- `django-cotton` is a required package dependency. `django-htmx` (≥1.0) is an **optional dependency** — it is included as a dev dependency of this package only. Developers who wish to use `HtmxFormMixin` must install `django-htmx` themselves and configure `HtmxMiddleware` in their project's `MIDDLEWARE` setting.
- Htmx request detection uses `request.htmx` (a boolean-compatible `HtmxDetails` object provided by `HtmxMiddleware`); raw `HX-Request` header inspection is not used.
- Partial content (success and form components) is authored by the developer as Cotton components in `templates/cotton/`; the package does not provide default partial components, though the demo app will include examples.
- Cotton component names use dot-notation (e.g., `"ui.form-success"` resolves to `cotton/ui/form_success.html`), matching the `render_component()` API convention. The `form.card` default for `htmx_form_component` maps to `cotton/form/card.html` in the package's template directory.
- The mixin targets htmx-initiated POSTs only; htmx GET requests (e.g., lazy loading, infinite scroll) are outside the scope of this feature.
- Both success partials and form-error partials return HTTP 200. This matches django-htmx's recommended patterns and works with htmx's default response handling without additional client-side configuration.
- `HttpResponseClientRedirect` causes a full client-side navigation (equivalent to a browser redirect); `HttpResponseLocation` (SPA-style navigation without full reload) is out of scope for this feature.
- Progressive enhancement is guaranteed: if a user submits the form without JavaScript or without htmx loaded, the base view's standard behaviour (redirect or full-page re-render) takes over seamlessly.
- Django's `get_messages(request)` is used to drain the session message queue on htmx paths. This is the standard Django API for consuming queued messages and has the side-effect of clearing them from the session — the intended behaviour.
- Out of scope: WebSocket responses, server-sent events, htmx polling, htmx OOB (out-of-band) swaps, and `HttpResponseLocation`-based SPA navigation.
- The `X-Success-Component` header is a developer-to-developer contract between the htmx caller markup and the view's allowlist. It is not a security boundary — the view controls which components are reachable via the allowlist (`htmx_success_components`); unknown aliases are silently ignored. Arbitrary component names sent by the client are never honoured.
- The two-level class hierarchy (`HtmxMixin` → `HtmxFormMixin`) is designed for future extensibility: additional htmx view types (e.g., `HtmxListViewMixin`) will inherit from `HtmxMixin` directly and automatically gain `htmx_enabled` context injection, trigger handling (`htmx_trigger`, `htmx_trigger_after`, `_apply_htmx_triggers()`), and allowlist-based component resolution (`_resolve_component()`) — all without any form-specific logic. Only concerns genuinely specific to form validation live in `HtmxFormMixin`.
