# Feature Specification: MVPFormView — Non-Model Form View

**Feature Branch**: `010-mvp-form-view`
**Created**: 2026-05-04
**Status**: Draft
**Input**: User description: "Not every form in an application is backed by a database model. Contact forms, settings pages, search forms, and wizard steps all need a place to live. This spec defines MVPFormView as the package's answer for that case: a form view that slots into the standard AdminLTE card layout and participates in the page context system, without requiring a model to be configured. It should be immediately usable and clearly distinct from the model form views."

## Clarifications

### Session 2026-05-04

- Q: Does `success_message` on `MVPFormView` support `%(field_name)s` substitution from submitted `cleaned_data`? → A: Yes — `cleaned_data` substitution IS supported (same as Django's `SuccessMessageMixin`); `%(verbose_name)s` is NOT injected into the substitution dict — because `defaultdict(str)` is used, it silently substitutes as `""` (empty string) if accidentally present.
- Q: What should `MVPFormView` display as the page title when `title` is not set? → A: The view's Python class name, split from CamelCase using `django.utils.text.camel_case_to_spaces()` and title-cased — e.g. `ContactFormView` → `"Contact Form View"`. This gives a readable, zero-config default with no model dependency.
- Q: What is the authentication posture for `MVPFormView`? → A: No authentication by default — access is unrestricted; developers add `LoginRequiredMixin` (or equivalent) to their subclass when needed. Authentication is an application-level concern, not a library concern.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Wire Up a Non-Model Form in Minutes (Priority: P1) [Developer]

As a developer building a contact form, settings page, or search form that has no backing database model, I want to subclass a single view class, set my form and redirect destination, and immediately have a working, consistently laid-out page — so that I can focus on the form's logic rather than the plumbing.

**Audience**: Developer (integrator)

**Why this priority**: This is the entire reason `MVPFormView` exists. Without it, developers must either subclass Django's raw `FormView` and manually assemble the AdminLTE layout, or incorrectly use a model-based view and leave `model` unset. Both outcomes are error-prone and inconsistent.

**Independent Test**: A view class that inherits from `MVPFormView`, sets only `form_class` and `success_url`, is wired to a URL, and is requested delivers a rendered page that uses the shared form layout — no custom template required. After submission with valid data, the user is redirected to `success_url`.

**Acceptance Scenarios**:

1. **Given** a view class inherits from `MVPFormView` with `form_class` and `success_url` set, **When** the view is requested, **Then** it renders using the shared form layout template with no custom template configured.
2. **Given** a `MVPFormView` subclass has `form_class` and `success_url` set, **When** the form is submitted with valid data, **Then** the user is redirected to `success_url`.
3. **Given** a `MVPFormView` subclass, **When** the form is submitted with invalid data, **Then** the form is re-displayed with validation errors and the page layout is unchanged.
4. **Given** a `MVPFormView` subclass with no `model` attribute, **When** the view is requested or submitted, **Then** no error is raised due to the absence of a model.

---

### User Story 2 — Display a Success Message After Submission (Priority: P1) [Developer]

As a developer wiring up a non-model form, I want to configure a `success_message` on my view and have it automatically displayed to the user after a valid submission — so that the user receives feedback without me writing any message-dispatching code.

**Audience**: Developer (integrator)

**Why this priority**: Success messages are a standard UX requirement on virtually every form. Making them declarative (set an attribute, get the message) removes boilerplate and ensures all forms in the application provide consistent feedback.

**Independent Test**: A `MVPFormView` subclass with `success_message = "Your message was sent."` displays that message via Django's messages framework after a valid form submission, with no custom `form_valid()` override on the subclass.

**Acceptance Scenarios**:

1. **Given** a `MVPFormView` subclass has `success_message = "Your message was sent."`, **When** the form is submitted with valid data, **Then** the message "Your message was sent." is displayed via the messages framework.
2. **Given** a `MVPFormView` subclass has no `success_message` configured, **When** the form is submitted with valid data, **Then** no message is displayed and no error is raised.
3. **Given** a `MVPFormView` subclass has `success_message = "Thanks, %(email)s!"` and the submitted form has `email` in `cleaned_data`, **When** the form is submitted with valid data, **Then** the message is displayed as `"Thanks, user@example.com!"` — `%(field_name)s` tokens are substituted from `cleaned_data`; `%(verbose_name)s` is not injected and silently substitutes as `""` (empty string) if accidentally present.

---

### User Story 3 — Redirect Through a Safe, Predictable Chain (Priority: P2) [Developer]

As a developer building a multi-step form or embedding a form inside a page that controls the next destination, I want `MVPFormView` to respect a validated `?next=` parameter from the request before falling back to `success_url` — so that the redirect destination can be driven by context without requiring per-subclass overrides.

**Audience**: Developer (integrator)

**Why this priority**: The `?next=` pattern is already established across all other form views in the package. Consistency reduces integration friction and allows the same patterns (e.g., embedding a form on a page that passes a return URL) to work uniformly.

**Independent Test**: A `MVPFormView` subclass with `success_url = "/default/"` is submitted with a valid `?next=/return-here/` query parameter; after valid submission the user is redirected to `/return-here/`, not `/default/`.

**Acceptance Scenarios**:

1. **Given** a `MVPFormView` is submitted with a valid, same-origin `?next=/some/path/` parameter, **When** the form is valid, **Then** the user is redirected to `/some/path/`, not to `success_url`.
2. **Given** a `MVPFormView` is submitted with a `?next=` value pointing to a different origin, **When** the form is valid, **Then** the redirect falls back to `success_url` (the unsafe `next` is ignored).
3. **Given** a `MVPFormView` subclass has no `success_url` and no valid `?next=`, **When** the form is submitted with valid data, **Then** `ImproperlyConfigured` is raised with a clear, actionable error message.

---

### User Story 4 — Participate in the Page Context System (Priority: P2) [Developer]

As a developer building a non-model form page, I want to configure `title`, `subtitle`, and breadcrumbs on `MVPFormView` using the same attributes that all other package views support — so that the form page feels like a first-class member of the application rather than an ad-hoc page.

**Audience**: Developer (integrator)

**Why this priority**: Visual consistency between form pages and the rest of the application requires that `MVPFormView` participates in the same page context system. A form view that ignores title, subtitle, and breadcrumb configuration is an incomplete solution.

**Independent Test**: A `MVPFormView` subclass with `title = "Contact Us"` and `subtitle = "Send us a message"` set renders those values in the page layout without any template override.

**Acceptance Scenarios**:

1. **Given** a `MVPFormView` subclass with `title = "Contact Us"` set, **When** the view is rendered, **Then** the page displays "Contact Us" as the page title in the layout.
2. **Given** a `MVPFormView` subclass with no `title` set and class name `ContactFormView`, **When** the view is rendered, **Then** the page title is `"Contact Form View"` (class name split from CamelCase via `django.utils.text.camel_case_to_spaces()` and title-cased).
3. **Given** a `MVPFormView` subclass with breadcrumbs configured, **When** the view is rendered, **Then** the breadcrumbs are rendered in the layout.
4. **Given** a `MVPFormView` subclass with `page_class` set, **When** the view is rendered, **Then** the CSS class is applied to the page wrapper element.

---

### Edge Cases

- What happens when `form_class` is not set? The view should raise `ImproperlyConfigured` (or Django's own equivalent) at dispatch time, matching Django's standard `FormMixin` behaviour.
- What is the default page title when `title` is not set? The class name is split from CamelCase via `django.utils.text.camel_case_to_spaces()` and title-cased — e.g. `ContactFormView` → `"Contact Form View"`.
- What happens when `success_url` is a lazy translation string? It should be coerced to a string before use, matching the behaviour of other views in the package.
- What happens when both `?next=` and `success_url` are absent? `ImproperlyConfigured` is raised with a message that names the view class and describes the fix.
- What if the developer sets `model` on `MVPFormView`? The view processes the form normally; the `model` attribute is ignored (no error, no model-specific behaviour activates).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `MVPFormView` MUST render using the shared package form layout template as a fallback, without any custom template configuration on the subclass.
- **FR-002**: `MVPFormView` MUST process a form specified via `form_class`, following Django's standard form validation lifecycle (GET renders the form; valid POST triggers `form_valid()`; invalid POST triggers `form_invalid()`).
- **FR-003**: `MVPFormView` MUST redirect the user to `success_url` after a valid form submission when no higher-priority redirect source is present.
- **FR-004**: `MVPFormView` MUST honour a validated, same-origin `?next=` (or POST `next`) redirect as the highest-priority redirect destination, consistent with other package form views.
- **FR-005**: `MVPFormView` MUST display a `success_message` via Django's messages framework after a valid submission, when `success_message` is set on the view. `%(field_name)s` tokens in the message MUST be substituted from the submitted form's `cleaned_data` (identical to Django's `SuccessMessageMixin` behaviour); `%(verbose_name)s` MUST NOT be injected — because `defaultdict(str)` is used internally, any key absent from `cleaned_data` (including `verbose_name`) silently substitutes as `""` (empty string).
- **FR-006**: `MVPFormView` MUST raise `ImproperlyConfigured` with an actionable error message when `form_valid()` is called and neither a valid `next` URL nor a `success_url` is available.
- **FR-007**: `MVPFormView` MUST NOT require a `model` attribute; no model-specific logic (CRUD URL resolution, verbose-name interpolation, object list fallback) must activate.
- **FR-008**: `MVPFormView` MUST participate in the package page context system, accepting `title`, `subtitle`, `page_class`, and breadcrumb configuration through the same attributes used by other package views. When `title` is not set, the default title MUST be derived from the view's Python class name by splitting CamelCase words with `django.utils.text.camel_case_to_spaces()` and applying title-case (e.g. `ContactFormView` → `"Contact Form View"`).
- **FR-009**: `MVPFormView` MUST be exported from `mvp.views` as a named, importable symbol so that developers can import it with a single import statement (`from mvp.views import MVPFormView`).
- **FR-010**: `MVPFormView` MUST coerce `success_url` to a plain string before use, supporting lazy translation strings without requiring the developer to call `str()` manually.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can build a working, AdminLTE-styled non-model form page by writing a subclass with two attributes (`form_class`, `success_url`) and zero template overrides.
- **SC-002**: All existing model-form view tests continue to pass unchanged — `MVPFormView` introduction introduces no regressions.
- **SC-003**: A developer reading the package's view class names can immediately determine that `MVPFormView` is for non-model forms and `MVPCreateView`/`MVPUpdateView` are for model forms — no documentation required.
- **SC-004**: A developer can configure title, subtitle, page_class, and breadcrumbs on `MVPFormView` using the same attribute names they use on every other package view.
- **SC-005**: A `MVPFormView` with `success_message` set displays the message after valid submission with no custom `form_valid()` override.

## Assumptions

- The `MVPFormBase` class defined in spec 009 already provides the shared layout integration, `NextURLMixin`, and success message support. `MVPFormView` is built on top of `MVPFormBase`, not independently.
- `MVPFormView` targets the same developer audience as other package views: Django developers building multi-page applications with AdminLTE.
- Django's built-in `FormView` (using `ProcessFormView` and `FormMixin`) is the correct base for `MVPFormView`; the class does not need to support model querysets, object lookup, or save logic.
- A single concrete class (`MVPFormView`) is sufficient for this use case. Developers with more complex needs (wizard steps with state, multi-step flows) are expected to subclass and override.
- The success message on `MVPFormView` does NOT perform model-aware `%(verbose_name)s` interpolation — only `MVPModelFormBase`-derived views do that. Literal strings in `success_message` are used as-is.
- `MVPFormView` applies no authentication by default. Access is unrestricted; developers who need auth add `LoginRequiredMixin` (or the project's equivalent) to their subclass. Authentication policy is an application-level concern.
- Out of scope: form wizard orchestration, multi-step flows, AJAX form submission, file upload handling.
