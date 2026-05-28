# Feature Specification: HTMX Form Mixin

**Feature Branch**: `020-htmx-form-mixin`
**Created**: 2026-05-28
**Status**: Draft
**Input**: User description: "In modern django apps, progressive enhancement using libraries such as htmx can greatly enhance the user experience. One of the most common patterns is to submit a form via htmx and, on success, return a partial component or, on error, return the form itself. I would like to create a form mixin that optionally enhances our standard form views with htmx functionality."

## Clarifications

### Session 2026-05-28

- Q: Should the mixin depend on `django-htmx` and `django-cotton`? → A: Yes — the mixin is tightly coupled to both libraries; `django-htmx` (for `request.htmx`, `HttpResponseClientRedirect`, `trigger_client_event`) and `django-cotton` (for `render_component`) are required dependencies, not optional.
- Q: What HTTP status code should the form-error partial return? → A: 200 — matches django-htmx's own `retarget()` pattern and works with htmx's default response handling without any additional client-side configuration.
- Q: What is the correct response type for `htmx_redirect_on_success`? → A: `HttpResponseClientRedirect` from `django_htmx.http` (triggers a full client-side navigation via `HX-Redirect`); `HttpResponseLocation` (SPA-style) is out of scope.
- Q: Should `htmx_trigger` support timing variants (HX-Trigger-After-Settle, HX-Trigger-After-Swap)? → A: Yes — via a `htmx_trigger_after` attribute accepting `'receive'` (default, maps to `HX-Trigger`), `'settle'` (maps to `HX-Trigger-After-Settle`), or `'swap'` (maps to `HX-Trigger-After-Swap`), delegating to `trigger_client_event()` from django-htmx.
- Q: Should `htmx_form_template` have a default fallback when not set? → A: No — `render_component()` requires an explicit Cotton component name; raise `ImproperlyConfigured` if `htmx_form_template` is not set and an htmx POST results in an invalid form.
- Q: What happens to Django success messages (SuccessMessageMixin) when the mixin returns an htmx partial instead of a full page? → A: Consume and discard — after calling `super().form_valid()`, the mixin drains the session message queue via `get_messages(request)` so no stale toast appears on the next full-page navigation. Developers use `htmx_trigger` for htmx-appropriate success feedback instead.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Submit a Form Without a Full Page Reload (Priority: P1)

As a user filling in a form on a page that uses htmx, I want the form to submit and receive feedback (success or validation errors) without the entire page reloading — so that the interaction feels fluid and the rest of the page state is preserved.

**Audience**: End user interacting with an htmx-enhanced form.

**Why this priority**: This is the core value proposition of the feature. Without it, the mixin provides no benefit.

**Independent Test**: A view enhanced with the mixin is submitted via an htmx POST. On success, an `HttpResponse` whose body is the output of `render_component()` for `htmx_success_template` is returned; on validation failure, an `HttpResponse` (status 200) whose body is the output of `render_component()` for `htmx_form_template` is returned — neither response triggers a full page navigation.

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

**Independent Test**: An existing `MVPCreateView` subclass gains htmx behaviour by adding the mixin to its inheritance chain and setting `htmx_success_template` (a Cotton component name) and `htmx_form_template`. No other changes are required — the view continues to work normally for non-htmx requests.

**Acceptance Scenarios**:

1. **Given** a developer adds the mixin to an existing form view class and sets `htmx_success_template` and `htmx_form_template`, **When** the view receives a normal (non-htmx) request, **Then** the view behaves exactly as before — no regression.
2. **Given** `htmx_success_template` is not set on a mixin-enhanced view and `htmx_redirect_on_success` is False, **When** the view receives an htmx POST with valid data, **Then** `ImproperlyConfigured` is raised directing the developer to configure `htmx_success_template` or enable `htmx_redirect_on_success`.
3. **Given** `htmx_form_template` is not set on a mixin-enhanced view, **When** the view receives an htmx POST with invalid data, **Then** `ImproperlyConfigured` is raised directing the developer to configure `htmx_form_template`.

---

### User Story 3 — Return an HX-Redirect Header on Success Instead of a Partial (Priority: P2)

As a developer building a form that should navigate the user to a new page after htmx submission (rather than swapping a partial), I want to configure the mixin to respond with an `HX-Redirect` header on success — so that htmx triggers a client-side navigation without me writing a custom `form_valid()` override.

**Audience**: Developer (integrator).

**Why this priority**: The partial-swap pattern covers inline forms, but many forms (create/update) naturally conclude with navigation. A redirect-via-htmx response pattern is the idiomatic way to handle this.

**Independent Test**: A mixin-enhanced view configured with `htmx_redirect_on_success = True` responds to a valid htmx POST with an `HttpResponseClientRedirect` containing an `HX-Redirect` header pointing to the resolved `success_url`. No partial component is rendered.

**Acceptance Scenarios**:

1. **Given** `htmx_redirect_on_success = True` is set and a valid htmx POST is received, **When** the form is valid, **Then** the response has an `HX-Redirect` header set to the resolved success URL and no page body is returned.
2. **Given** `htmx_redirect_on_success = True` is set and an invalid htmx POST is received, **When** the form is invalid, **Then** the form partial is returned with errors as normal (the redirect setting only applies to the success path).
3. **Given** neither `htmx_success_template` nor `htmx_redirect_on_success` is set and an htmx POST is submitted, **When** the form is valid, **Then** a clear error is raised directing the developer to configure one of the two options.

---

### User Story 4 — Emit HTMX Response Triggers on Success (Priority: P3)

As a developer building a page where other components need to react to a successful form submission (e.g., refreshing a list), I want to configure the mixin to emit an `HX-Trigger` header on success — so that other htmx-powered elements on the page update automatically without writing JavaScript.

**Audience**: Developer (integrator).

**Why this priority**: Trigger headers are a common htmx pattern for coordinating page components. Supporting them declaratively avoids developers having to override `form_valid()` solely to add a response header.

**Independent Test**: A mixin-enhanced view configured with `htmx_trigger = "itemCreated"` responds to a valid htmx POST with a response where `trigger_client_event(response, "itemCreated", after='receive')` has been applied, regardless of whether `htmx_success_template` or `htmx_redirect_on_success` is used.

**Acceptance Scenarios**:

1. **Given** `htmx_trigger = "itemCreated"` is set, **When** a valid htmx POST is received, **Then** the response includes an `HX-Trigger: itemCreated` header (applied via `trigger_client_event` with `after='receive'`).
2. **Given** `htmx_trigger` is not set, **When** a valid htmx POST is received, **Then** no `HX-Trigger` header is added to the response.
3. **Given** `htmx_trigger` is set to a dict `{"itemCreated": {"id": 1}}`, **When** a valid htmx POST is received, **Then** `trigger_client_event` is called once per entry, with each event name and its params dict.
4. **Given** `htmx_trigger_after = "settle"` is set alongside `htmx_trigger`, **When** a valid htmx POST is received, **Then** the response includes `HX-Trigger-After-Settle` (not `HX-Trigger`) for the configured event.

---

### Edge Cases

- What happens when a form view enhanced with the mixin is accessed by a client that sends no htmx request headers? → `request.htmx` evaluates to `False`; the mixin is transparent and the view behaves exactly as its unenhanced base class would.
- What happens when `htmx_success_template` or `htmx_form_template` references a Cotton component that does not exist? → Django's standard `TemplateDoesNotExist` exception is raised by the template engine — no special handling needed.
- What happens if the developer sets both `htmx_success_template` and `htmx_redirect_on_success`? → `htmx_redirect_on_success` takes precedence; `htmx_success_template` is ignored on the success path (document this in FR-013 and class docstring).
- What happens on a multi-step form or wizard step where `success_url` is not defined and `htmx_redirect_on_success = True`? → Same behaviour as the base view — `ImproperlyConfigured` is raised if the base class cannot determine a redirect URL.
- What happens when the view is used in a context where htmx is not loaded on the client? → `request.htmx` evaluates to `False`; the mixin is never activated; the view behaves as a standard Django form view.
- What happens to Django success messages when the mixin returns an htmx partial? → Messages queued by `SuccessMessageMixin.form_valid()` are consumed and discarded by calling `get_messages(request)` immediately after; they will not appear as stale toasts on the next full-page navigation. Use `htmx_trigger` to deliver equivalent feedback over htmx.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The mixin MUST detect whether a request was initiated by htmx via `request.htmx` provided by `django-htmx`'s `HtmxMiddleware`; raw header inspection is not used.
- **FR-002**: The mixin MUST be composable with any of the package's existing form view classes (`MVPFormView`, `MVPCreateView`, `MVPUpdateView`, `MVPDeleteView`) without requiring changes to those base classes.
- **FR-003**: When an htmx POST results in a valid form, the mixin MUST return an `HttpResponse` whose body is the output of `render_component(request, htmx_success_template, context)` from `django_cotton`, if `htmx_redirect_on_success` is falsy.
- **FR-004**: When an htmx POST results in a valid form and `htmx_redirect_on_success` is truthy, the mixin MUST return `HttpResponseClientRedirect(success_url)` from `django_htmx.http`, triggering a full client-side navigation via the `HX-Redirect` header.
- **FR-005**: When an htmx POST results in an invalid form, the mixin MUST return an `HttpResponse` (status 200) whose body is the output of `render_component(request, htmx_form_template, context)` from `django_cotton`.
- **FR-006**: The mixin MUST pass the full view context (including the bound form instance with errors) to `render_component()` on validation failure, so that form errors are visible and the Cotton component has access to all context variables.
- **FR-007**: When `htmx_trigger` is set to a non-empty string or dict, the mixin MUST call `trigger_client_event(response, name, params, after=htmx_trigger_after)` from `django_htmx.http` on successful htmx responses.
- **FR-008**: When `htmx_trigger` is a string, it is passed as the event `name` with no `params`; when it is a dict, it is interpreted as `{name: params}` pairs and each entry is added via a separate `trigger_client_event()` call.
- **FR-009**: The mixin MUST NOT alter the behaviour of the base view for any non-htmx request (GET or POST).
- **FR-010**: When `htmx_success_template` is not set and `htmx_redirect_on_success` is falsy, and the view receives a valid htmx POST, the mixin MUST raise `ImproperlyConfigured` with a clear error message.
- **FR-011**: When `htmx_form_template` is not set and the view receives an htmx POST that results in an invalid form, the mixin MUST raise `ImproperlyConfigured` with a clear error message directing the developer to configure the attribute.
- **FR-012**: The mixin MUST support overriding `get_htmx_success_template()` and `get_htmx_form_template()` for dynamic Cotton component name resolution per request.
- **FR-013**: When both `htmx_success_template` and `htmx_redirect_on_success` are set, the redirect MUST take precedence on the success path; the success template is ignored.
- **FR-014**: The `htmx_trigger_after` attribute MUST accept `'receive'` (default, maps to `HX-Trigger`), `'settle'` (maps to `HX-Trigger-After-Settle`), or `'swap'` (maps to `HX-Trigger-After-Swap`).
- **FR-015**: When returning an htmx partial on the success path, the mixin MUST drain Django's session message queue via `get_messages(request)` after `super().form_valid()` returns, so that no queued success message surfaces as a stale toast on the next full-page navigation. This behaviour applies only to htmx paths; non-htmx paths leave message handling entirely to the base class.

### Key Entities

- **HtmxFormMixin**: The mixin class. Attributes: `htmx_success_template` (str | None — Cotton component name in dot notation), `htmx_form_template` (str | None — Cotton component name in dot notation), `htmx_redirect_on_success` (bool, default False), `htmx_trigger` (str | dict | None), `htmx_trigger_after` (Literal['receive', 'settle', 'swap'], default `'receive'`). Methods: `get_htmx_success_template()`, `get_htmx_form_template()`, `form_valid()` (override), `form_invalid()` (override).
- **render_component** (`django_cotton`): Renders a Cotton component to an HTML string given a request, component name, and context dict. Used by the mixin to produce partial responses.
- **HttpResponseClientRedirect** (`django_htmx.http`): Response class that sets `HX-Redirect`, causing htmx to perform a full client-side navigation to the target URL.
- **trigger_client_event** (`django_htmx.http`): Modifies a response to include `HX-Trigger` / `HX-Trigger-After-Settle` / `HX-Trigger-After-Swap` headers for client-side event dispatch.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer adds htmx enhancement to any existing package form view by adding the mixin to the class definition and setting `htmx_success_template` and `htmx_form_template` (plus optionally `htmx_redirect_on_success`) — verified by integration examples in the package's demo app.
- **SC-002**: All existing form view tests continue to pass without modification after the mixin is introduced — confirming zero regression on non-htmx paths.
- **SC-003**: An htmx POST to a valid form returns a response in which no full page layout markup is present — only the content of the configured partial template.
- **SC-004**: An htmx POST to an invalid form returns a response in which form validation errors are present and the response contains no full page layout markup.
- **SC-005**: The `HX-Redirect` header, when set, contains the exact same URL that a non-htmx submission would redirect to — ensuring redirect logic is not duplicated.
- **SC-006**: The mixin ships with unit tests achieving 100% branch coverage on the htmx detection and response-branching logic.

## Assumptions

- The package's target audience already uses or intends to use htmx in their projects; the mixin does not install or configure htmx itself.
- `django-htmx` (≥1.0) and `django-cotton` are **required dependencies** of the mixin. Both must be installed and configured in the developer's project (`HtmxMiddleware` added to `MIDDLEWARE`; `django_cotton` added to `INSTALLED_APPS`).
- Htmx request detection uses `request.htmx` (a boolean-compatible `HtmxDetails` object provided by `HtmxMiddleware`); raw `HX-Request` header inspection is not used.
- Partial content (success and form components) is authored by the developer as Cotton components in `templates/cotton/`; the package does not provide default partial components, though the demo app will include examples.
- Cotton component names use dot-notation (e.g., `"ui.form-success"` resolves to `cotton/ui/form_success.html`), matching the `render_component()` API convention.
- The mixin targets htmx-initiated POSTs only; htmx GET requests (e.g., lazy loading, infinite scroll) are outside the scope of this feature.
- Both success partials and form-error partials return HTTP 200. This matches django-htmx's recommended patterns and works with htmx's default response handling without additional client-side configuration.
- `HttpResponseClientRedirect` causes a full client-side navigation (equivalent to a browser redirect); `HttpResponseLocation` (SPA-style navigation without full reload) is out of scope for this feature.
- Progressive enhancement is guaranteed: if a user submits the form without JavaScript or without htmx loaded, the base view's standard behaviour (redirect or full-page re-render) takes over seamlessly.
- Django's `get_messages(request)` is used to drain the session message queue on htmx paths. This is the standard Django API for consuming queued messages and has the side-effect of clearing them from the session — the intended behaviour.
- Out of scope: WebSocket responses, server-sent events, htmx polling, htmx OOB (out-of-band) swaps, and `HttpResponseLocation`-based SPA navigation.
