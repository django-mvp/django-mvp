# Feature Specification: Safe Post-Submit Redirect

**Feature Branch**: `008-safe-post-submit-redirect`
**Created**: 2026-05-03
**Status**: Refined
**Refined**: 2026-05-04 — Added FR-001a: `get_next_candidate()` override point in `NextURLMixin` (planner evaluates whether existing `NextURLMixin` code needs changes, additions, or is already complete)
**Input**: User description: "Form views are frequently used as steps inside larger flows — opening a form from a list, creating a record and returning to where you came from, chaining a create directly into an edit. The next parameter is the standard mechanism for this, but blindly redirecting to any URL in a query string is an open-redirect vulnerability. This spec defines how the package handles next safely: validating the destination before using it, distinguishing between a full URL and a shorthand CRUD action name, and falling back gracefully when neither is present."

## Clarifications

### Session 2026-05-03

- Q: Should this spec be treated as prescriptive or descriptive? → A: Prescriptive — spec defines target state; planner evaluates whether existing `NextURLMixin` code needs changes, additions, or is already complete.
- Q: Which view classes support CRUD action shorthand resolution for `next`? → A: All form views (`MVPFormView` included) — shorthand resolution is attempted on every form view; it is silently skipped when no model identity is available.
- Q: Should HTTPS be required for `next` URL validation, or should it match the current request scheme? → A: Dynamic — `require_https` mirrors `request.is_secure()`; same-host absolute URLs are allowed on HTTP sites (preserves dev-environment compatibility).
- Q: Should rejected `next` values be logged to help developers diagnose misconfigured links? → A: Yes, at `DEBUG` level only — a `logger.warning` is emitted when `DEBUG=True`; no log entry in production unless the project opts in to DEBUG logging.
- Q: What is the canonical term for the mechanism that carries the post-submit redirect destination? → A: "`next` parameter" — matches Django's own convention; all loose synonyms ("redirect target", "fallback destination") normalized to "`next` parameter" and "fallback" respectively.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Chain Form Views in Multi-Step Flows Using a URL Destination (Priority: P1) [Developer]

As a developer, I want to specify a `next` URL in the query string when linking to a form view, so that after the form is submitted successfully the user is returned to exactly the page I specified — without configuring a fixed success URL per view.

**Audience**: Developer (integrator)
**Why this priority**: This is the foundational use case. Multi-step flows such as "open form from list → submit → return to list" are ubiquitous. Developers need a mechanism that works without custom redirect logic on every view.
**Independent Test**: A form URL is constructed as `/records/create/?next=/records/`. After successful submission, the response redirects to `/records/`. Verified by asserting the `next` parameter destination matches exactly.

**Acceptance Scenarios**:

1. **Given** a form URL includes `?next=/records/`, **When** the form is submitted successfully, **Then** the response redirects to `/records/`.
2. **Given** a form URL includes `?next=/records/`, **When** the form page is rendered (GET), **Then** the `next` value is accessible in the template context so the form can carry it through the POST round-trip.
3. **Given** a form is submitted with `next` in the POST data, **When** the submission succeeds, **Then** the view uses the POST `next` parameter value (not the query string) as the post-submit destination.

---

### User Story 2 - Be Redirected Back to the Right Place After Form Submission (Priority: P1) [End User]

As an end user navigating a multi-step flow — clicking "Create" on a list page, filling in a form, pressing Save — I want to be automatically returned to the page I started from after the form is submitted, so that my workflow continues without me having to navigate back manually.

**Audience**: End User
**Why this priority**: Without post-submit redirection, users are dropped to a default destination that breaks their workflow context, causing disorientation and extra navigation.
**Independent Test**: A user follows a "Create" link that embeds `?next=/orders/`, submits the form, and is redirected back to `/orders/`.

**Acceptance Scenarios**:

1. **Given** a user follows a "Create" link that includes `?next=/orders/`, **When** they submit the form successfully, **Then** they are redirected to `/orders/`.
2. **Given** no `next` parameter is present, **When** a user submits the form successfully, **Then** they are redirected to the view's configured default destination — not left on a blank page or an error page.
3. **Given** a form submission fails validation, **When** the form is re-rendered, **Then** the `next` value is still present so the redirect will work when the user corrects and resubmits.

---

### User Story 3 - Use CRUD Action Names as Shorthand Redirect Destinations (Priority: P2) [Developer]

As a developer, I want to specify a CRUD action shorthand (e.g., `next=list`, `next=detail`, `next=update`) instead of a hardcoded URL, so that redirect targets remain correct if URL patterns change and multi-step flows can be expressed declaratively (e.g., "create, then immediately edit the new record").

**Audience**: Developer (integrator)
**Why this priority**: Hardcoding URLs in `next` parameters couples form links to URL patterns. Shorthand names decouple the intent from the route, making flows portable and maintainable.
**Independent Test**: A create-form link uses `?next=list`. After successful creation, the response redirects to the list URL for the current model. A separate test uses `?next=detail` and verifies the redirect goes to the newly created object's detail page.

**Acceptance Scenarios**:

1. **Given** `next=list` is present, **When** the form is submitted successfully, **Then** the redirect goes to the list URL for the current model.
2. **Given** `next=detail` is present on a create form, **When** the form is submitted successfully, **Then** the redirect goes to the detail URL for the newly created object.
3. **Given** `next=update` is present on a create form, **When** the form is submitted successfully, **Then** the redirect goes to the update URL for the newly created object.
4. **Given** `next` contains a shorthand name that has no resolvable URL (e.g., the corresponding URL pattern does not exist), **When** the form is submitted, **Then** the view falls back to its configured default destination without raising an error.

---

### User Story 4 - Protected From Open-Redirect Attacks Automatically (Priority: P1) [Developer]

As a developer integrating form views, I want the package to automatically reject redirect targets that point to external domains or unsafe schemes, so that my application is not vulnerable to open-redirect attacks without any opt-in validation on my part.

**Audience**: Developer (integrator)
**Why this priority**: Open-redirect is a well-documented vulnerability. Blindly redirecting to any query-string value is insecure. This protection must be on by default — requiring developers to opt in to safety is not acceptable.
**Independent Test**: A form is submitted with `next=https://evil.com/phishing` in POST data. The response does NOT redirect to `evil.com`; it redirects to the view's fallback.

**Acceptance Scenarios**:

1. **Given** the `next` parameter contains an absolute URL pointing to a different domain, **When** the form is submitted successfully, **Then** the redirect ignores the `next` parameter and uses the fallback.
2. **Given** the `next` parameter contains a protocol-relative URL (e.g., `//evil.com/path`), **When** the form is submitted, **Then** it is treated as unsafe and rejected in the same way as an absolute external URL.
3. **Given** the `next` parameter contains a `javascript:` URL, **When** the form is submitted, **Then** it is rejected and the fallback is used.
4. **Given** `next` is present in the query string on the initial form render, **When** the page is displayed, **Then** only same-origin paths are reflected into the template context as `next_url`; external values are discarded at render time, not only at submit time.

---

### User Story 5 - Fall Back Gracefully When No Valid Redirect Destination Exists (Priority: P2) [Developer]

As a developer, I want form views to always reach a valid destination after successful submission — regardless of whether `next` is absent, invalid, or an unresolvable shorthand — so that users are never left in a broken state.

**Audience**: Developer (integrator)
**Why this priority**: Fallback safety guarantees a predictable result across all flows, including malformed links, misconfigured forms, and edge-case inputs.
**Independent Test**: A form is submitted with no `next` parameter; the response redirects to the view's configured success URL. A second test submits with `next=garbage_value` and verifies the same fallback behaviour.

**Acceptance Scenarios**:

1. **Given** no `next` parameter is present, **When** the form is submitted successfully, **Then** the redirect goes to the view's configured success URL.
2. **Given** `next` contains a value that is neither a safe URL nor a recognized CRUD action shorthand, **When** the form is submitted, **Then** the redirect goes to the view's configured success URL.
3. **Given** the view has no configured success URL and `next` is absent, **When** the form is submitted, **Then** the view uses its built-in fallback (e.g., the list URL for model-based forms).

---

### Edge Cases

- What happens when the `next` parameter is an empty string? → It must be treated as absent; the fallback is used.
- What happens when the `next` parameter contains a `javascript:` URI? → Rejected as unsafe; fallback used.
- What if `next=detail` or `next=update` is provided on a create view before the object has been saved? → The shorthand must be resolved using the identity of the object just created by the current submission — the resolution happens after the save.
- What if a CRUD shorthand resolves correctly but permission checks deny access? → The shorthand is treated as unresolvable; the fallback is used.
- What if the form submission fails validation? → No redirect occurs; the form is re-rendered with errors, and the `next_url` context variable must retain its value.
- What if `next` appears both in the query string and as a POST field? → POST data takes precedence on submission.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Form views MUST read the `next` parameter from POST data on form submission, and from the query string on initial form display (GET).
- **FR-001a**: The logic for reading the raw `next` value from the request MUST be encapsulated in a single override point, `get_next_candidate()`, on `NextURLMixin` — returning `request.POST.get("next")` on POST and `request.GET.get("next")` on GET. This eliminates duplicated request-reading logic and gives subclasses a clean hook to customise the candidate source without reimplementing validation.
- **FR-002**: Any `next` value that is a relative, same-origin path MUST be accepted as a safe redirect destination.
- **FR-003**: Any `next` parameter value that contains an absolute URL pointing to a different origin MUST be silently rejected; the fallback is used instead.
- **FR-004**: Any `next` parameter value that is a protocol-relative URL (e.g., `//external.com/path`) MUST be rejected in the same way as an absolute external URL.
- **FR-005**: Any `next` parameter value that contains an unsafe scheme (e.g., `javascript:`) MUST be rejected; the fallback is used.
- **FR-005a**: The HTTPS requirement for `next` URL validation MUST mirror the current request: when the request is served over HTTPS, `http://` absolute URLs MUST be rejected; when the request is served over HTTP, same-host `http://` URLs MUST be accepted. This preserves compatibility with development environments and HTTP-only deployments.
- **FR-005b**: When the `next` parameter is rejected (external URL, unsafe scheme, or unresolvable shorthand), the view MUST emit a `logger.warning` message when `settings.DEBUG` is `True`. No log entry MUST be produced in non-DEBUG environments unless the project explicitly configures the logger.
- **FR-006**: If `next` is a recognized CRUD action shorthand — at minimum: `"list"`, `"create"`, `"detail"`, `"update"`, `"delete"` — any form view MUST attempt to resolve it using the CRUD directory resolution mechanism (see spec 006). If no model identity is available (e.g., `MVPFormView` with no model), the shorthand attempt MUST be silently skipped and resolution falls through to the next priority destination.
- **FR-007**: CRUD action shorthands that resolve to object-level URLs (`"detail"`, `"update"`, `"delete"`) MUST use the identity of the object that was just submitted, including objects newly created by the current submission.
- **FR-008**: When a CRUD action shorthand cannot be resolved (no matching URL, permission denied, or no object available), the form view MUST silently fall back to the next priority destination — not raise an error.
- **FR-009**: The post-submit destination priority order MUST be: (1) validated same-origin `next` parameter URL, (2) resolved CRUD action shorthand from the `next` parameter, (3) the view's configured success URL, (4) built-in fallback (e.g., list URL for model-based views).
- **FR-010**: The validated `next` parameter value MUST be injected into the template context under the key `next_url` on GET requests, so that form templates can embed it as a hidden field to survive the POST round-trip.
- **FR-011**: When the `next` parameter is absent, empty, or unsafe, `next_url` in the template context MUST be `None` — not an empty string and not omitted.
- **FR-012**: On a failed form submission (validation errors), the `next_url` template context variable MUST retain its value so the destination is preserved for the user's corrected resubmission.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Form views with a valid same-origin `next` parameter always redirect to the correct destination — verified across all five standard CRUD action shorthands and at least three distinct relative URL values.
- **SC-002**: No form view in the package is susceptible to open-redirect via the `next` parameter — verified by security test cases covering external URLs, protocol-relative URLs, and `javascript:` schemes.
- **SC-003**: Developers can build a complete "list → create → back to list" flow by adding `?next=list` to a create link, with no custom view code required.
- **SC-004**: Form submissions with an absent, empty, or invalid `next` always reach a valid destination — no 404, no unhandled exception, no blank page.
- **SC-005**: The `next_url` context variable is correctly populated (or `None`) on both initial GET render and failed POST re-render with validation errors.

## Assumptions

- CRUD action shorthand resolution is attempted on all form views, including `MVPFormView`. When no model identity is available on the view, the shorthand attempt is silently skipped and resolution falls through to the configured success URL.
- The form template is responsible for embedding `next_url` as a hidden `<input>` field so the value is present in POST data. The package provides the value via template context but does not automatically inject hidden fields into form output.
- "Same-origin" means matching the host and scheme of the current request; port matching follows standard same-origin rules.
- CRUD action shorthand matching is case-sensitive (e.g., `"List"` is not recognised; only lowercase `"list"` is).
- Custom CRUD action names registered via `crud_views` (spec 006) are also valid shorthands.
