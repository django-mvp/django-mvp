# Feature Specification: List View Inline Create

**Feature Branch**: `021-list-inline-create`
**Created**: 2026-06-02
**Status**: Draft
**Input**: User description: "Sometimes it is cumbersome to, when on a list view, navigate to a new view to create an object. I would like to create a list view mixin that allows a list view to accept a form_class attribute. If present, the form_class should be provided to the template context for rendering (for example in a modal). The form and toggle should be conditionally displayed depending on whether the user has the appropriate create permission. In the template, if the user can create, but no form is present, we must still show the normal link to the create page. I've already created a very basic mockup with this on the ProductListView in the demo app."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Inline Create via Modal (Priority: P1)

A developer adds `create_form_class = MyForm` to their list view subclass. When a user with create permission visits the list page, a button appears in the toolbar that opens a modal containing the form. Submitting the form POSTs to the standard create view; on success the user is redirected to the success URL defined by that view.

**Why this priority**: This is the core feature. It enables a fast-access create workflow without navigating away from the list page first.

**Independent Test**: Can be fully tested by subclassing `MVPListViewMixin` with a `create_form_class`, visiting the list page as a user with create permission, and verifying the modal button and form appear in the toolbar. Delivers the complete inline create UX.

**Acceptance Scenarios**:

1. **Given** a list view with `create_form_class` set and `has_create_permission = True`, **When** the page is rendered, **Then** `create_form` is present in the template context and a modal-trigger button appears in the toolbar.
2. **Given** the modal is open and the user fills in and submits the form, **When** the form is valid, **Then** the object is created and the browser is redirected back to the list page (the modal form action includes `?next=<list_url>`, which the create view honours).
3. **Given** the modal is open and the user submits an invalid form, **When** the form has validation errors, **Then** the browser navigates to the create page which displays the errors (in-modal error re-render via HTMX is deferred to a later feature).

---

### User Story 2 - Fallback to Create Page Link (Priority: P2)

A developer configures a list view with create permission enabled but without setting `create_form_class`. When a user with create permission visits the list page, a regular link button appears in the toolbar pointing to the standard create page URL.

**Why this priority**: Ensures backward compatibility and graceful degradation — developers who don't opt into the inline form still get the expected create-page link.

**Independent Test**: Can be fully tested by verifying that when `create_form_class` is absent and `has_create_permission = True`, the toolbar shows a link button to `directory.create_url` rather than a modal trigger.

**Acceptance Scenarios**:

1. **Given** a list view with `has_create_permission = True` and no `create_form_class`, **When** the page is rendered, **Then** the toolbar shows a button that navigates to the create page URL (not a modal trigger).
2. **Given** a list view with `has_create_permission = False` and no `create_form_class`, **When** the page is rendered, **Then** no create button appears in the toolbar at all.

---

### User Story 3 - Permission Gate Hides Form (Priority: P3)

A developer configures a list view with `create_form_class` set but `has_create_permission = False` (or a callable that returns `False` for the current user). The form is not injected into the template context and no create button appears in the toolbar.

**Why this priority**: Security requirement — the form must not be accessible to users without the appropriate permission, even if `create_form_class` is configured.

**Independent Test**: Can be fully tested by verifying that `create_form` is absent from the template context and no create-related UI element appears when permission is denied.

**Acceptance Scenarios**:

1. **Given** a list view with `create_form_class` set and `has_create_permission = False`, **When** the page is rendered, **Then** `create_form` is absent from the template context and no create button appears.
2. **Given** `has_create_permission` is a callable that returns `False` for the current user, **When** the page is rendered, **Then** the behavior is identical to `has_create_permission = False`.

---

### Edge Cases

- What happens when `create_form_class` is set but `create_url` cannot be resolved (no CRUD URL configured)? `create_form` is still injected into context (permission permitting), but the toolbar modal-trigger button does not appear because it requires `directory.create_url`. No error is raised.
- How does the system handle a `create_form_class` that requires request-bound initialization (e.g., `__init__` taking extra args)? An override hook `get_create_form()` should allow developers to customize form instantiation.
- What happens if form submission results in a server error? Standard Django form error handling applies on the create page; the list view does not process POST and does not re-render errors in the modal.
- What if both `create_form_class` and the existing `get_context_data` override in the demo are present? The mixin's logic supersedes the manual override once migrated.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The mixin MUST provide a `create_form_class` class attribute (default `None`) that accepts a Django form class.
- **FR-002**: When `create_form_class` is set AND the user has create permission, the mixin MUST inject an instantiated form into the template context under the key `create_form`.
- **FR-003**: When `create_form_class` is not set (or `None`), `create_form` MUST NOT be added to the template context.
- **FR-004**: The `create_form` context variable MUST only be injected when `has_create_permission` resolves to `True` for the current user (supporting both boolean and callable forms consistent with `CRUDDirectoryMixin`).
- **FR-005**: The mixin MUST provide a `get_create_form()` override hook that developers can use to customize form instantiation (e.g., pass request data, user, or additional kwargs).
- **FR-006**: The list view toolbar template MUST conditionally render: a modal-trigger button when **both** `directory.create_url` **and** `create_form` are present in context; a link button to `directory.create_url` when only `directory.create_url` is present (no `create_form`); no create UI when neither is present.
- **FR-007**: The create modal title MUST default to `"Add <verbose_name>"` (capitalised, derived from `model._meta.verbose_name`). Developers MUST be able to override it via a `create_modal_title` class attribute on the view without subclassing or template changes. The submit button label is always `"Add"`. No other modal strings are hardcoded to a specific model name.
- **FR-008**: `create_form_class` and `get_create_form()` MUST be added directly to `MVPListViewMixin`; existing subclasses that do not set `create_form_class` MUST require no changes and exhibit no behavioral difference.
- **FR-009**: The demo app's `ListViewDemo` MUST be updated to use the new mixin attribute and remove the manual `get_context_data` override that currently injects `create_form`.
- **FR-010**: The create modal form action URL MUST include a `?next={{ request.path }}` query parameter so that after a successful create the user is redirected back to the list page. The create view (`MVPCreateView`) MUST honour the `next` parameter when present (verifying or adding this support is in scope for this feature).

### Key Entities *(include if feature involves data)*

- **`MVPListViewMixin` (extended)**: Gains `create_form_class = None`, `create_modal_title = None`, and a `get_create_form()` hook; when `create_form_class` is set and permission is granted, `create_form` and `create_modal_title` are injected into context automatically.
- **create_form**: The instantiated form object injected into the template context when inline create is enabled and permitted.
- **Toolbar template** (`list/toolbar.html`): The Cotton component that conditionally renders the create button as a modal trigger or a link based on the presence of `create_form`.
- **List view template** (`list_view.html`): The base list page template that conditionally renders the create modal when `create_form` is present in context.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can enable inline object creation on any list view by adding a single attribute (`create_form_class`) without overriding any methods.
- **SC-002**: All three toolbar states (modal button / link button / no button) are covered by automated tests and produce no regressions against the existing list view test suite.
- **SC-003**: The demo app's product list page demonstrates the complete inline create workflow: modal opens, form is submitted, user is redirected back to the list page, and the new object appears. The manual `get_context_data` override is removed from `ListViewDemo`.
- **SC-004**: List views that do not set `create_form_class` continue to function identically to their pre-feature behavior — no behavioral change introduced for existing views.
- **SC-005**: The create modal title and labels are derived generically from the model, so no hardcoded model-specific strings remain in the base list view template.

## Clarifications

### Session 2026-06-02

- Q: How should invalid form submission errors be handled? → A: Standard redirect — POST goes to the create view; on error the user lands on the create page. In-modal HTMX error re-render is deferred to a later spec.
- Q: Should inline-create support be a separate mixin or folded into `MVPListViewMixin`? → A: Fold directly into `MVPListViewMixin` — `create_form_class = None` by default, zero impact on existing views.
- Q: Is `create_url` required for the modal button to appear? → A: Yes — the modal trigger button only renders when both `directory.create_url` and `create_form` are present in context; `create_form` is still injected into context independently of `create_url`.
- Q: Should there be an explicit `create_modal_title` override attribute, or always auto-derive from model? → A: Auto-derive default (`"Add <verbose_name>"`) with an explicit `create_modal_title` class attribute for overrides.
- Q: After a successful create, should the user be redirected back to the list page? → A: Yes — the modal form action must include `?next=<list_url>` so the create view redirects back to the list on success.

## Assumptions

- The existing `has_create_permission` mechanism (boolean or callable, resolved by `CRUDDirectoryMixin`) will be reused for permission gating — no new permission API is introduced.
- Form submission from the modal uses a standard HTTP POST to `create_url?next=<list_url>`; the list view does not handle POST at all. On successful create the user is redirected back to the list page via the `next` parameter. On validation error the browser lands on the create page. HTMX-based modal error re-render is explicitly deferred to a later spec and should not be architecturally blocked by this implementation.
- The modal structure follows the existing Bootstrap 5 modal pattern already present in the codebase.
- The `create_form_class` form is instantiated without request data by default (i.e., as an unbound form for initial rendering); binding the form with POST data for submission is handled by the separate create view.
- `create_form_class` support is folded directly into `MVPListViewMixin`; `MVPTableViewMixin` (which inherits from it) gains the behavior automatically without additional changes.
- The existing demo mockup (manual `get_context_data` override on `ListViewDemo`) will be replaced by the mixin implementation as part of this feature.
