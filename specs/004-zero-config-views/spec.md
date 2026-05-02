# Feature Specification: Zero-Config Ready-to-Use Views

**Feature Branch**: `004-zero-config-views`
**Created**: 2026-05-02
**Status**: Draft
**Input**: User description: "The package should ship two ready-to-use views that require no model or form configuration. The first is a plain template view that participates in the page layout with zero effort. The second serves a dual purpose: it shows an unauthenticated visitor a marketing landing page and shows a logged-in user their application dashboard — from the same URL, the same view class, with no conditional routing at the URL layer. Both views should demonstrate the package working end-to-end before any model or form complexity is introduced."

## Clarifications

### Session 2026-05-02

- Q: When `HomeView` has only `landing_template_name` set and an authenticated user requests the page, what should happen? → A: Raise `ImproperlyConfigured` — not having both templates declared is a configuration error.
- Q: What HTTP methods should `PageView` and `HomeView` support? → A: GET only — both views are read-only display views.
- Q: Should `HomeView` inject `request.user` into the template context, or is the context determined entirely by Django's standard context processors? → A: Rely on Django's standard context processors — `request.user` is available via the standard auth context processor, no custom injection needed.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Register a Plain Page View in Minutes (Priority: P1) [Developer]

A developer installs django-mvp and wants to add a simple informational page (About, FAQ, Terms, etc.) that sits inside the application's standard layout shell — with sidebar, navbar, and all layout chrome — without writing any Python view class, form, or model. They point a URL at the package's ready-made `PageView`, name a template, and the page renders inside the layout immediately.

**Audience**: Developer (integrator)
**Why this priority**: This is the simplest possible on-ramp to the package. If this fails, every other use case is blocked. Proving that a plain template renders in the layout with a single URL entry validates the full layout pipeline before any business logic is involved.
**Independent Test**: A URL can be wired to `PageView` (or a subclass) with only `template_name` set, a template file created, and the rendered HTML must include both the layout shell and the template's custom content.

**Acceptance Scenarios**:

1. **Given** django-mvp is installed and a URL entry maps to `PageView` with `template_name = "myapp/about.html"`, **When** a user visits that URL, **Then** the response renders the template inside the standard layout shell with the full sidebar and navbar present.
2. **Given** no model, form, or queryset is defined, **When** the view is rendered, **Then** no errors or warnings are raised and the page loads successfully.
3. **Given** a developer subclasses `PageView` and sets only `template_name`, **When** the view is wired via `as_view()`, **Then** it behaves identically to using `PageView` directly with `template_name` as a class attribute.

---

### User Story 2 - Register a Home View That Switches Between Guest and Dashboard (Priority: P1) [Developer]

A developer wants a single URL (e.g., `/`) to serve a public marketing landing page to anonymous visitors and an authenticated user's application dashboard to logged-in users — all within the same view class, without any URL-layer conditional routing or middleware tricks. They point the URL at the package's `HomeView`, supply a landing template and a dashboard template, and the view dispatches to the correct template automatically based on authentication state.

**Audience**: Developer (integrator)
**Why this priority**: This is the canonical "hello world" for the package's dual-audience design pattern. It demonstrates layout participation, authentication awareness, and template selection in one self-contained unit — the most compelling early proof-of-value for a developer evaluating the package.
**Independent Test**: A single URL entry wired to `HomeView`, two template files (one for guests, one for authenticated users), and the rendered output differs based on whether the request is authenticated — with no URL changes, redirects, or middleware involved.

**Acceptance Scenarios**:

1. **Given** a URL mapped to `HomeView` with `landing_template_name` and `dashboard_template_name` configured, **When** an unauthenticated visitor requests the URL, **Then** the landing page template is rendered inside the layout.
2. **Given** the same URL and view, **When** a logged-in user requests the URL, **Then** the dashboard template is rendered inside the layout — without any redirect, URL change, or login requirement.
3. **Given** only `landing_template_name` is configured (no `dashboard_template_name`) and an authenticated user requests the URL, **Then** the view raises `ImproperlyConfigured` with a clear message directing the developer to set `dashboard_template_name`.
4. **Given** a developer subclasses `HomeView` and overrides only `landing_template_name`, **When** both authenticated and unauthenticated requests are made, **Then** template selection still works correctly for both cases.

---

### User Story 3 - Visitor Experiences Seamless Guest-to-Dashboard Transition (Priority: P1) [End User]

An end user visits the root URL of an application built with django-mvp. Before logging in, they see a welcoming marketing landing page (hero text, call-to-action, etc.). After logging in, returning to the same URL shows them their personal dashboard. The browser URL does not change and there is no intermediary redirect page between the two states.

**Audience**: End User
**Why this priority**: The seamless URL-invariant template switch is the defining user-facing behaviour of `HomeView`. A noticeable redirect or URL change would undermine the entire value proposition of the dual-purpose view.
**Independent Test**: Using a test client, request the home URL without authentication (assert landing content), then request it with authentication (assert dashboard content) — both responses must be `200 OK` with no redirect chain.

**Acceptance Scenarios**:

1. **Given** an unauthenticated request to the home URL, **When** the page loads, **Then** the landing page content is displayed, the response status is `200 OK`, and no login redirect occurs.
2. **Given** an authenticated request to the home URL, **When** the page loads, **Then** the dashboard content is displayed at the same URL with a `200 OK` response and no redirect.
3. **Given** the layout shell (navbar, sidebar, content wrapper) is present on the dashboard view, **When** the user interacts with navigation elements, **Then** they function without page errors.

---

### User Story 4 - Plain Page View Participates Fully in Layout Configuration (Priority: P2) [Developer]

A developer wants `PageView` to respect layout configuration options available in the package (page title, sidebar state, etc.) so it behaves identically to other layout-aware views. They set options via class attributes without writing custom `get_context_data` methods.

**Audience**: Developer (integrator)
**Why this priority**: Consistency across view types is essential. If `PageView` ignores layout options that model-backed views honour, it creates a confusing and inconsistent developer experience.
**Independent Test**: Set a page title or sidebar option on `PageView` via a class attribute, render the view, and confirm the layout shell reflects the configured values.

**Acceptance Scenarios**:

1. **Given** `PageView` is configured with a `page_title` attribute, **When** the view renders, **Then** the layout shell displays the configured title.
2. **Given** the package supports sidebar configuration options (expressed via the `page_class` attribute, e.g., `page_class="sidebar-collapse"`), **When** `PageView` sets this attribute via a class attribute or `as_view()`, **Then** the layout shell renders with the specified CSS class applied to the page container.

---

### Edge Cases

- What happens when `HomeView` is configured with neither `landing_template_name` nor `dashboard_template_name`? The view must raise a clear configuration error at first request, not a silent failure or misleading traceback.
- What happens when a logged-in user's session expires mid-session and they return to the home URL? The next request must render the landing page, not the dashboard, without raising an error.
- What happens when the template file referenced by `template_name` or `landing_template_name` does not exist? Django's standard `TemplateDoesNotExist` error should surface rather than a generic 500.
- What happens when `HomeView` has no `landing_template_name` set and an anonymous visitor requests the page? The view must raise `ImproperlyConfigured` — `landing_template_name` is always required and the view must not expose dashboard content to unauthenticated users under any fallback path.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The package MUST provide a `PageView` class that renders a named template inside the standard layout with no model, form, or queryset configuration required.
- **FR-002**: `PageView` MUST accept `template_name` as a class attribute and render that template without additional developer-written Python beyond the URL entry.
- **FR-003**: `PageView` MUST participate fully in the package's layout system, respecting the same layout configuration options (page title, sidebar state expressed via the `page_class` attribute, etc.) as all other layout-aware views.
- **FR-004**: The package MUST provide a `HomeView` class that selects between two templates based solely on the authentication state of the incoming request.
- **FR-005**: `HomeView` MUST render `landing_template_name` for unauthenticated visitors and `dashboard_template_name` for authenticated users — from the same URL, same view instance, with no redirect or URL change.
- **FR-006**: `HomeView` MUST NOT require authentication to render; anonymous access must always succeed and display the landing content.
- **FR-007**: Both `PageView` and `HomeView` MUST render their chosen template inside the package's standard layout shell (navbar, sidebar, content area) without extra developer configuration.
- **FR-008**: Both views MUST be importable directly from the package's top-level or views namespace so developers do not need to navigate internal module paths.
- **FR-009**: If `HomeView` is configured with `landing_template_name` but no `dashboard_template_name`, the view MUST raise `ImproperlyConfigured` with a diagnostic message when an authenticated user requests the page. Not having both templates declared is a configuration error, not a recoverable runtime condition.
- **FR-010**: Both views MUST be usable via `as_view()` in a standard Django URL configuration with no additional wiring beyond template name configuration.
- **FR-011**: Both `PageView` and `HomeView` MUST respond to GET requests only. Neither view handles POST, PUT, PATCH, or DELETE — they are read-only display views. Requests with other HTTP methods MUST receive a `405 Method Not Allowed` response.
- **FR-012**: If `HomeView` has `landing_template_name` set to `None`, the view MUST raise `ImproperlyConfigured` with a diagnostic message regardless of the request's authentication state. `landing_template_name` is always required; there is no fallback or default when explicitly set to `None`.

### Key Entities

- **PageView**: A ready-to-use view class that renders a configurable template inside the layout. No model, form, or queryset required. Configured entirely via class attributes.
- **HomeView**: A dual-purpose view class that selects between a landing template (for guests) and a dashboard template (for authenticated users) based on request authentication state. Operates from a single URL with no redirect logic.
- **Layout Shell**: The package's standard page chrome (navbar, sidebar, content wrapper) that both views render their templates inside. Configured at the view or project level, not per-request.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can wire `PageView` to a URL and see a fully layout-rendered page in under 5 minutes from a fresh install, requiring no Python beyond the URL configuration entry. *(Qualitative DX goal; validated by T048 quickstart walkthrough, not by automated assertion.)*
- **SC-002**: A developer can wire `HomeView` to a URL and confirm template switching between guest and authenticated states with fewer than 10 lines of configuration total (URL entry plus two template name attributes).
- **SC-003**: 100% of requests to `PageView` or `HomeView` render inside the layout shell with no bare-template responses, given project-level layout configuration is in place.
- **SC-004**: The guest-to-dashboard template switch produces no redirect; the browser URL remains identical before and after authentication when navigating to the home URL.
- **SC-005**: Both views are covered by automated tests that verify correct template selection and layout participation without requiring a database, model, or form fixture.

## Assumptions

- The package already ships a layout shell (navbar, sidebar, content area) that other views participate in. `PageView` and `HomeView` join that existing system rather than introducing a new layout mechanism.
- "No configuration" means no Python beyond what is required in a Django URL file (`as_view()` with class attributes). Template files themselves are created by the developer.
- The dashboard template for `HomeView` is a plain HTML template; the view does not auto-generate dashboard widgets or pull any model data by default.
- `HomeView` does not enforce login — it is explicitly designed to be accessible to both anonymous and authenticated users from the same URL.
- Both views rely entirely on Django's standard context processors for template context (including `request.user` via `django.contrib.auth.context_processors.auth`). Neither view injects custom per-user context; `request.user` is available to templates through the standard processor, not through any view-level injection.
- Layout configuration options (page title, sidebar state, etc.) are already defined by the package's layout system and both views inherit them via standard class attribute or mixin patterns established in earlier specs.
