# Feature Specification: Form View Base Classes

**Feature Branch**: `009-form-view-base`
**Created**: 2026-05-04
**Status**: Draft — Prescriptive (planner evaluates whether current code needs changes, additions, or is already complete)
**Input**: User description: "Before concrete form views can exist, the package needs a shared foundation that gives every form view its layout, its success message support, and its redirect logic. This spec defines MVPFormBase and MVPModelFormBase as that foundation — not concrete views themselves, but the layer that all edit views inherit from. Their job is to ensure that the moment a developer subclasses any edit view in this package, they automatically get a consistent layout, safe redirects, and properly interpolated success messages without any additional configuration."

## Clarifications

### Session 2026-05-04

- Q: Should `MVPModelFormBase` raise `ImproperlyConfigured` when its list-view fallback also fails (no list URL resolvable, no `success_url`), symmetrically with FR-005? → A: Yes — raise `ImproperlyConfigured` symmetrically; model views with no list URL and no `success_url` get a named, actionable error at `get_success_url()` time.
- Q: When a delete-view success message contains field-value placeholders (e.g. `%(name)s`) and `cleaned_data` is absent, what should happen? → A: Substitute `""` for missing field placeholders — no error; output silently omits the unresolvable placeholder value.
- Q: What is the canonical term for messages displayed after successful form submission? → A: `success message` — matches Django's `success_message` attribute and `SuccessMessageMixin`; "flash message" is not used in Django's own documentation.
- Q: Should this spec prescribe the exact MRO/mixin composition of `MVPFormBase`, or leave class structure to the planner? → A: Behaviors only — the spec names the two canonical classes and their observable behaviors; internal class composition is left to the planner's discretion.
- Q: Should User Story 1 scenario 1 ("no redirect configuration → predictable destination, no error") be scoped to model form views to stay consistent with FR-005's error requirement for non-model views? → A: Yes — scope scenario 1 to model form views; the list-view fallback ensures a predictable destination for model views, while FR-005's `ImproperlyConfigured` error remains the correct outcome for non-model views with no redirect configured.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Subclass a Form View and Get Layout, Redirects, and Messages for Free (Priority: P1) [Developer]

As a developer building a form view, I want to subclass any edit view from this package and automatically inherit a consistent layout, safe redirect logic, and success message support — without writing any boilerplate in the subclass — so that I can focus entirely on what makes my view unique.

**Audience**: Developer (integrator)

**Why this priority**: This is the core value of the form view foundation. Without it, every developer subclassing a form view must manually assemble the same three concerns (layout, redirect, messages) each time, defeating the purpose of the package.

**Independent Test**: A minimal create view that inherits from `MVPCreateView`, sets only `model`, and is wired to a URL successfully: renders a page using the shared form layout, redirects to the list view after submission, and displays a success message that names the model — all with zero redirect or message configuration on the subclass.

**Acceptance Scenarios**:

1. **Given** a *model* form view class (inheriting from `MVPModelFormBase`) has no `next` parameter and no `success_url` configured, **When** the form is submitted successfully, **Then** the view redirects to the model's list view without raising an error.
2. **Given** a view class inherits from any edit view in this package, **When** the view renders, **Then** the shared form layout template is used as the fallback — no custom template required.
3. **Given** a view class inherits from any edit view and sets `success_message`, **When** the form is submitted successfully, **Then** the message is displayed to the user via Django's messages framework.
4. **Given** a model form view is submitted successfully with the default `success_message`, **When** the success message is displayed, **Then** the message includes the model's human-readable name without any extra configuration.

---

### User Story 2 - Success Messages on Model Forms Automatically Name the Model (Priority: P1) [Developer]

As a developer configuring success messages on model form views, I want to use `%(verbose_name)s` in my `success_message` string and have it automatically filled in with the model's human-readable name — so that messages read naturally without any custom message formatting code.

**Audience**: Developer (integrator)

**Why this priority**: Success messages are a standard UX pattern on every create, update, and delete action. Making model-aware interpolation automatic removes a recurring source of boilerplate and ensures consistent phrasing across all model form views.

**Independent Test**: A create view with `success_message = "%(verbose_name)s was saved."` and `model = Order` displays "Order was saved." after form submission, with no custom `get_success_message()` override on the view class.

**Acceptance Scenarios**:

1. **Given** a model form view has `success_message = "%(verbose_name)s successfully created."` and `model = Order`, **When** the form is submitted successfully, **Then** the success message reads "Order successfully created."
2. **Given** a model with `verbose_name = "purchase order"`, **When** any model form view for that model is submitted, **Then** the success message uses the model's `verbose_name`, not its Python class name.
3. **Given** a `success_message` combines `%(verbose_name)s` with a field value placeholder such as `%(name)s`, **When** the form is submitted with `name = "Widget A"`, **Then** both `%(verbose_name)s` and `%(name)s` are interpolated correctly in the displayed message.
4. **Given** a delete-view success message contains a field placeholder such as `%(name)s` (and `cleaned_data` is absent), **When** the deletion succeeds, **Then** the message is displayed with `%(verbose_name)s` interpolated and the unresolvable `%(name)s` placeholder silently replaced with an empty string — no error is raised.

---

### User Story 3 - Redirect Destination Resolves Through a Predictable Priority Chain (Priority: P2) [Developer]

As a developer wiring form views into larger flows, I want the post-submit redirect destination to be selected from a predictable priority chain — `next` parameter first, then `success_url`, then a built-in default for model views — so that I can override only what I need and always know where the user will land.

**Audience**: Developer (integrator)

**Why this priority**: Predictable redirect behavior eliminates surprises when form views are embedded in multi-step flows. Developers need to reason about the full fallback chain without reading the source code.

**Independent Test**: Three form submissions with different configurations: (a) a `?next=/records/` parameter present, (b) `success_url = "/dashboard/"` set with no `next`, (c) a model form view with neither — each submission results in a redirect to the expected destination.

**Acceptance Scenarios**:

1. **Given** a `?next=/records/` parameter is present, **When** the form is submitted successfully, **Then** the user is redirected to `/records/` regardless of any `success_url` configured on the view.
2. **Given** no `next` parameter is present and `success_url = "/dashboard/"` is set on the view, **When** the form is submitted successfully, **Then** the user is redirected to `/dashboard/`.
3. **Given** a model form view has neither `next` parameter nor `success_url`, **When** the form is submitted successfully, **Then** the user is redirected to the model's list view.
4. **Given** a non-model form view has neither `next` parameter nor `success_url`, **When** the form is submitted successfully, **Then** a clear misconfiguration error is raised rather than a silent redirect to a broken URL.
5. **Given** a new object was just created (no pk was in the URL kwargs before submission), **When** the `next=detail` CRUD shorthand is used, **Then** the redirect resolves correctly using the newly created object's pk.

---

### Edge Cases

- What happens when `success_message` contains `%(verbose_name)s` on a non-model form view? → `%(verbose_name)s` is only injected by `MVPModelFormBase`; using it on a plain `MVPFormBase` subclass without model context raises a `KeyError` at runtime. Developers using non-model form views must not include `%(verbose_name)s`, or must override `get_success_message()`.
- What happens when a delete-view success message contains field-value placeholders (e.g. `%(name)s`) and `cleaned_data` is absent? → Missing field placeholders are substituted with `""` (empty string); the message displays without error. Only `%(verbose_name)s` is guaranteed to resolve in every `MVPModelFormBase` context.
- What happens when `success_url` is set to a falsy value (e.g., empty string)? → A falsy `success_url` is treated as absent; the next step in the priority chain applies.
- How does the chain behave when the `next` parameter is present but fails validation? → The invalid `next` value is silently dropped (per spec 008 — Safe Post-Submit Redirect); the chain falls through to `success_url` or the default.
- What happens for `MVPModelFormBase` subclasses when no list URL is configured and no `success_url` is set? → `ImproperlyConfigured` is raised at `get_success_url()` time with a clear message — symmetric with FR-005. Developers must configure `crud_views` or set `success_url` when using `MVPModelFormBase`.
- What happens if a CRUD shorthand (e.g. `?next=detail`) cannot be resolved because no model identity is configured? → Resolution fails silently; the chain falls through to the next priority step.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `MVPFormBase` MUST apply the shared form layout template (`form_view.html`) as the fallback template for every subclass, without requiring any template configuration on the subclass.
- **FR-002**: `MVPFormBase` MUST integrate Django's success message machinery so that subclasses display success messages by setting `success_message`, without any additional wiring.
- **FR-003**: `MVPFormBase` MUST apply a scoped CSS class (`mvp-form-page`) to the page container, so that all form pages share a consistent styling anchor available without subclass configuration.
- **FR-004**: `MVPFormBase` MUST determine the post-submit redirect destination using the following priority chain: (1) a validated `next` URL from the request (including resolved CRUD action shorthands), (2) the `success_url` attribute on the view.
- **FR-005**: `MVPFormBase` MUST raise a clear misconfiguration error when neither `next` nor `success_url` is configured, rather than silently redirecting to an unexpected destination.
- **FR-006**: `MVPFormBase` MUST resolve CRUD action shorthands (e.g. `?next=list`, `?next=detail`) into real same-origin URLs when the view has model identity available, so that developers can reference related views by name rather than hardcoded paths.
- **FR-007**: `MVPModelFormBase` MUST extend `MVPFormBase` with automatic `%(verbose_name)s` interpolation in `success_message`, sourcing the value from the model's `verbose_name` metadata. When additional field-value placeholders are present but `cleaned_data` is absent or does not contain the key (e.g. on a delete view), those placeholders MUST be substituted with an empty string rather than raising an error.
- **FR-008**: `MVPModelFormBase` MUST extend the redirect priority chain with a built-in fallback to the model's list view, so that model form views can omit `success_url` entirely. When the list view URL cannot be resolved (e.g. `crud_views` is not configured), `ImproperlyConfigured` MUST be raised with a clear message — symmetric with FR-005.
- **FR-009**: `MVPModelFormBase` MUST correctly resolve post-submit redirect destinations that require an object pk (e.g. `?next=detail`) after a create operation, using the pk of the newly created object even though no pk was present in the URL kwargs at request time.
- **FR-010**: Both base classes MUST compose cleanly with Django's generic form views (`FormView`, `CreateView`, `UpdateView`, `DeleteView`) without altering their core form processing or validation behavior.

### Key Entities

- **MVPFormBase**: The shared foundation for all form views in the package. Composes the layout template resolution, Django's success message machinery, and the post-submit redirect priority chain. Not a concrete view — must be combined with a Django generic view class.
- **MVPModelFormBase**: Extends `MVPFormBase` with model-aware success message interpolation and an automatic list-view fallback in the redirect chain. Serves as the base for all model form views (`MVPCreateView`, `MVPUpdateView`, `MVPDeleteView`).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can build a working model create/update/delete view with zero redirect and message configuration — the view renders, processes the form, displays a model-named success message, and redirects to the list view without any explicit wiring.
- **SC-002**: All model form views in the package produce success messages that include the model's human-readable name, with no per-view message formatting code required.
- **SC-003**: All form views inherit the shared form layout template by default; a subclass must explicitly set `template_name` to use a different template.
- **SC-004**: The post-submit redirect priority chain is documentable in three steps — developers can predict the redirect destination from a view's configuration without reading the source code.
- **SC-005**: Misconfiguration on a non-model form view (missing redirect destination) produces an error that names the problem clearly and points to the resolution, not a silent redirect to a broken URL.

## Assumptions

- Both base classes are treated as prescriptive behavioral targets; the planner will evaluate whether the existing `MVPFormBase` and `MVPModelFormBase` code needs changes, additions, or is already complete. Internal class composition and mixin MRO are left to the planner's discretion — this spec constrains only the observable behaviors defined in the FRs.
- Safe `next` parameter validation and CRUD action shorthand resolution are defined by spec 008 (Safe Post-Submit Redirect); this spec assumes that behavior is in place and treats it as a dependency.
- Model identity, CRUD directory resolution, and page header composition are defined by spec 007 (Object Page Foundation); this spec assumes `PageObjectMixin` is in place and treats it as a dependency.
- `SuccessMessageMixin` is Django's built-in; its core behavior (storing the message after `form_valid()`) is not redefined here.
- Concrete view classes (`MVPFormView`, `MVPCreateView`, `MVPUpdateView`, `MVPDeleteView`) are out of scope for this spec; they inherit from these base classes but are defined elsewhere.
- The form layout template (`form_view.html`) is already in place; this spec does not cover its internal structure.
- The delete view uses `MVPModelFormBase` as its base even though `DeleteView` does not process a data entry form; this is an existing architectural decision and is not revisited here.
