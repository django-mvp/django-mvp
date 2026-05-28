# Feature Specification: HTMX Form Mixin

**Feature Branch**: `020-htmx-form-mixin`
**Created**: 2026-05-28
**Status**: Draft
**Input**: User description: "In modern django apps, progressive enhancement using libraries such as htmx can greatly enhance the user experience. One of the most common patterns is to submit a form via htmx and, on success, return a partial component or, on error, return the form itself. I would like to create a form mixin that optionally enhances our standard form views with htmx functionality."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Submit a Form Without a Full Page Reload (Priority: P1)

As a user filling in a form on a page that uses htmx, I want the form to submit and receive feedback (success or validation errors) without the entire page reloading — so that the interaction feels fluid and the rest of the page state is preserved.

**Audience**: End user interacting with an htmx-enhanced form.

**Why this priority**: This is the core value proposition of the feature. Without it, the mixin provides no benefit.

**Independent Test**: A view enhanced with the mixin is submitted via an htmx POST. On success, only the designated success partial is returned in the response; on validation failure, only the form partial is returned with errors — neither response triggers a full page navigation.

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

**Independent Test**: An existing `MVPCreateView` subclass gains htmx behaviour by adding the mixin to its inheritance chain and setting `htmx_success_template`. No other changes are required — the view continues to work normally for non-htmx requests.

**Acceptance Scenarios**:

1. **Given** a developer adds the mixin to an existing form view class and sets `htmx_success_template`, **When** the view receives a normal (non-htmx) request, **Then** the view behaves exactly as before — no regression.
2. **Given** `htmx_success_template` is not set on a mixin-enhanced view, **When** the view receives an htmx POST with valid data, **Then** a clear, actionable error is raised (e.g., `ImproperlyConfigured`) directing the developer to configure the template.
3. **Given** a developer adds the mixin without specifying `htmx_form_template`, **When** the view receives an htmx POST with invalid data, **Then** the response defaults to re-rendering the form using the same partial template the form would use in the full-page render (no extra config required for the error case).

---

### User Story 3 — Return an HX-Redirect Header on Success Instead of a Partial (Priority: P2)

As a developer building a form that should navigate the user to a new page after htmx submission (rather than swapping a partial), I want to configure the mixin to respond with an `HX-Redirect` header on success — so that htmx triggers a client-side navigation without me writing a custom `form_valid()` override.

**Audience**: Developer (integrator).

**Why this priority**: The partial-swap pattern covers inline forms, but many forms (create/update) naturally conclude with navigation. A redirect-via-htmx response pattern is the idiomatic way to handle this.

**Independent Test**: A mixin-enhanced view configured with `htmx_redirect_on_success = True` responds to a valid htmx POST with a 200-or-204 response that includes an `HX-Redirect` header pointing to the resolved `success_url`. No partial template is rendered.

**Acceptance Scenarios**:

1. **Given** `htmx_redirect_on_success = True` is set and a valid htmx POST is received, **When** the form is valid, **Then** the response has an `HX-Redirect` header set to the resolved success URL and no page body is returned.
2. **Given** `htmx_redirect_on_success = True` is set and an invalid htmx POST is received, **When** the form is invalid, **Then** the form partial is returned with errors as normal (the redirect setting only applies to the success path).
3. **Given** neither `htmx_success_template` nor `htmx_redirect_on_success` is set and an htmx POST is submitted, **When** the form is valid, **Then** a clear error is raised directing the developer to configure one of the two options.

---

### User Story 4 — Emit HTMX Response Triggers on Success (Priority: P3)

As a developer building a page where other components need to react to a successful form submission (e.g., refreshing a list), I want to configure the mixin to emit an `HX-Trigger` header on success — so that other htmx-powered elements on the page update automatically without writing JavaScript.

**Audience**: Developer (integrator).

**Why this priority**: Trigger headers are a common htmx pattern for coordinating page components. Supporting them declaratively avoids developers having to override `form_valid()` solely to add a response header.

**Independent Test**: A mixin-enhanced view configured with `htmx_trigger = "itemCreated"` responds to a valid htmx POST with a response that contains an `HX-Trigger: itemCreated` header, regardless of whether `htmx_success_template` or `htmx_redirect_on_success` is used.

**Acceptance Scenarios**:

1. **Given** `htmx_trigger = "itemCreated"` is set, **When** a valid htmx POST is received, **Then** the response includes `HX-Trigger: itemCreated` as a response header.
2. **Given** `htmx_trigger` is not set, **When** a valid htmx POST is received, **Then** no `HX-Trigger` header is added to the response.
3. **Given** `htmx_trigger` is set to a dict (for multi-event triggers), **When** a valid htmx POST is received, **Then** the `HX-Trigger` header is set to the JSON-serialised representation of the dict.

---

### Edge Cases

- What happens when a form view enhanced with the mixin is accessed by a client that sends no htmx request headers? → The mixin is transparent; the view behaves exactly as its unenhanced base class would.
- What happens when `htmx_success_template` references a template that does not exist? → Django's standard `TemplateDoesNotExist` exception is raised — no special handling needed.
- What happens if the developer sets both `htmx_success_template` and `htmx_redirect_on_success`? → The redirect takes precedence; `htmx_success_template` is ignored on the success path (document this clearly).
- What happens on a multi-step form or wizard step where `success_url` is not defined? → Same behaviour as the base view — `ImproperlyConfigured` is raised if the base class cannot determine a redirect URL (htmx redirect mode) or the mixin raises if `htmx_success_template` is also absent.
- What happens when the view is used in a context where htmx is not loaded on the client? → Htmx request headers are never sent; the mixin is never activated; the view behaves as a standard Django form view.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The mixin MUST detect whether a request was initiated by htmx by inspecting request headers, without depending on any third-party htmx integration library (i.e., raw header inspection is acceptable).
- **FR-002**: The mixin MUST be composable with any of the package's existing form view classes (`MVPFormView`, `MVPCreateView`, `MVPUpdateView`, `MVPDeleteView`) without requiring changes to those base classes.
- **FR-003**: When an htmx POST results in a valid form, the mixin MUST return a partial response rendered from `htmx_success_template` if `htmx_redirect_on_success` is falsy.
- **FR-004**: When an htmx POST results in a valid form and `htmx_redirect_on_success` is truthy, the mixin MUST return a response with an `HX-Redirect` header set to the resolved success URL and no rendered body.
- **FR-005**: When an htmx POST results in an invalid form, the mixin MUST return a partial response rendered from `htmx_form_template` (when set) or fall back to a sensible default that renders the form with errors.
- **FR-006**: The mixin MUST pass the form instance and the full view context to the partial template rendered on validation failure, so that form errors are visible and the template has access to all context variables.
- **FR-007**: When `htmx_trigger` is set to a non-empty string, the mixin MUST add an `HX-Trigger` response header to all successful htmx responses.
- **FR-008**: When `htmx_trigger` is set to a dict, the mixin MUST JSON-serialise it and set it as the `HX-Trigger` header value.
- **FR-009**: The mixin MUST NOT alter the behaviour of the base view for any non-htmx request (GET or POST).
- **FR-010**: When `htmx_success_template` is not set and `htmx_redirect_on_success` is falsy, and the view receives a valid htmx POST, the mixin MUST raise `ImproperlyConfigured` with a clear error message.
- **FR-011**: The mixin MUST support overriding `get_htmx_success_template()` and `get_htmx_form_template()` for dynamic template resolution per request.
- **FR-012**: When both `htmx_success_template` and `htmx_redirect_on_success` are set, the redirect MUST take precedence on the success path; the success template is ignored.

### Key Entities

- **HtmxFormMixin**: The mixin class. Attributes: `htmx_success_template` (str | None), `htmx_form_template` (str | None), `htmx_redirect_on_success` (bool, default False), `htmx_trigger` (str | dict | None). Methods: `is_htmx_request()`, `get_htmx_success_template()`, `get_htmx_form_template()`, `form_valid()` (override), `form_invalid()` (override).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer adds htmx enhancement to any existing package form view by adding the mixin to the class definition and setting at most two attributes — verified by the integration examples in the package's demo app.
- **SC-002**: All existing form view tests continue to pass without modification after the mixin is introduced — confirming zero regression on non-htmx paths.
- **SC-003**: An htmx POST to a valid form returns a response in which no full page layout markup is present — only the content of the configured partial template.
- **SC-004**: An htmx POST to an invalid form returns a response in which form validation errors are present and the response contains no full page layout markup.
- **SC-005**: The `HX-Redirect` header, when set, contains the exact same URL that a non-htmx submission would redirect to — ensuring redirect logic is not duplicated.
- **SC-006**: The mixin ships with unit tests achieving 100% branch coverage on the htmx detection and response-branching logic.

## Assumptions

- The package's target audience already uses or intends to use htmx in their projects; the mixin does not install or configure htmx itself.
- The htmx request detection relies on the `HX-Request` header sent by htmx on all requests it initiates; this is standard htmx behaviour and requires no server-side library.
- The `django-htmx` third-party library is **not** a dependency; header inspection is done directly so that projects without `django-htmx` can use the mixin.
- Partial templates (success and form partials) are authored by the developer using the mixin — the package does not provide default partial templates, though the demo app will include examples.
- The mixin targets htmx-initiated POSTs only; htmx GET requests (e.g., lazy loading) are outside the scope of this feature.
- Response status codes for partial renders follow htmx conventions: 200 for success partials and form-error partials. The `HX-Redirect` response uses 200 with the redirect header (not an HTTP 3xx).
- Progressive enhancement is guaranteed: if a user submits the form without JavaScript or without htmx loaded, the base view's standard behaviour (redirect or full-page re-render) takes over seamlessly.
- Out of scope: WebSocket responses, server-sent events, htmx polling, and any htmx OOB (out-of-band) swap support beyond what the `HX-Trigger` header enables.
