# Feature Specification: MVPUpdateView — Zero-Config Model Update View

**Feature Branch**: `012-mvp-update-view`
**Created**: 2026-05-05
**Status**: Draft
**Input**: User description: "The update view differs from the create view in ways that matter to users: the breadcrumb trail is deeper (it includes a link to the record itself, sitting between the list and the form), the page signals that something already exists is being changed rather than created, and the form can offer a direct path to the delete view from within the edit page itself. This spec defines all of those distinctions and what the view should do when the delete destination is not configured."

## User Scenarios & Testing *(mandatory)*

### User Story 1 [Developer] — Zero-Config Update Page (Priority: P1)

A developer registers an update view for their `Product` model using only the two required class attributes (`model` and `fields`). The resulting page has a model-aware title ("Update Product"), a pre-wired success message, a three-level breadcrumb (list → object → form), and the correct icon and CSS modifier — all without any additional configuration.

**Why this priority**: This is the core value proposition. Every other story depends on the zero-config path working correctly before customisation is layered on top, and it mirrors the P1 story for `MVPCreateView` that the team can already verify works.

**Independent Test**: Create `class ProductUpdateView(MVPUpdateView): model = Product; fields = ["name"]` in a test project. Navigate to the update URL for an existing `Product`. Verify title, breadcrumb depth, icon, form rendering, and post-save redirect all work correctly.

**Acceptance Scenarios**:

1. **Given** a `MVPUpdateView` subclass with only `model` and `fields` set, **When** the page is rendered, **Then** the page title reads "Update {verbose_name.title()}" (e.g., "Update Product").
2. **Given** a `MVPUpdateView` subclass, **When** the page is rendered, **Then** the breadcrumb shows three items: "{verbose_name_plural.title()}" linking to the list URL, "{str(object)}" linking to the object's detail URL, and the current page title with no link.
3. **Given** a `MVPUpdateView` subclass, **When** the page is rendered, **Then** the page icon is "edit" and the page CSS classes include "mvp-form-page" and "mvp-update-page".
4. **Given** a valid form submission, **When** the object is saved, **Then** a success message "{verbose_name.title()} successfully updated." is displayed on the next page.
5. **Given** a valid form submission and no explicit `success_url`, **When** the object is saved, **Then** the user is redirected to the updated object's detail URL (via `object.get_absolute_url()`); if `get_absolute_url()` is not defined, `ImproperlyConfigured` is raised guiding the developer to set `success_url`.

---

### User Story 2 [Developer] — Customised Title and Message (Priority: P2)

A developer overrides the default title and success message to match their application's language and branding, without touching any other behaviour.

**Why this priority**: Customisation is essential for real-world adoption. Developers must be able to escape the defaults with a single class attribute.

**Independent Test**: Set `page_title = "Edit product details"` and `success_message = "%(name)s was saved."` on the view class. Verify the page renders the custom title and the success flash shows the custom message after a valid submission.

**Acceptance Scenarios**:

1. **Given** `page_title` is explicitly set on the subclass, **When** the page is rendered, **Then** the explicit title is displayed instead of the auto-derived one.
2. **Given** `success_message` is explicitly set on the subclass, **When** a valid form is submitted, **Then** the custom message (with `cleaned_data` interpolation) is displayed instead of the default.
3. **Given** `page_icon` is set to a different value, **When** the page is rendered, **Then** the overridden icon is used.
4. **Given** `success_url` is set to a CRUD shorthand (e.g., `"list"`) or a literal path, **When** a valid form is submitted, **Then** the user is redirected to that destination.

---

### User Story 3 [Developer] — Delete Link Within the Edit Page (Priority: P2)

A developer's update view shows a direct "Delete" action link or button in the edit page header. When the user follows that link, they land on the delete confirmation page; if they confirm deletion, they are redirected to the list view. If they cancel, the back-link returns them to the edit page they came from.

**Why this priority**: The delete-from-edit path is a defining difference between the update and create views. It must work end-to-end, but its failure does not block the zero-config title and breadcrumb (US1).

**Independent Test**: Register a `MVPDeleteView` alongside `MVPUpdateView` in the CRUD directory. Load the update page and verify the delete link is present and points to the delete URL. Confirm that `?back=<update_url>&next=<list_url>` query parameters are appended.

**Acceptance Scenarios**:

1. **Given** a `MVPDeleteView` is registered in the CRUD directory for the same model, **When** the update page is rendered, **Then** a delete link or button is visible in the page header.
2. **Given** the delete link is present, **When** the developer inspects the link href, **Then** it targets the delete view URL with `?back=<update_url>&next=<list_url>` query parameters appended.
3. **Given** the user follows the delete link, completes deletion, and the delete view redirects via `?next=`, **Then** the user lands on the list page (not the update page for the now-deleted object).
4. **Given** the user follows the delete link and then cancels deletion (via `?back=`), **Then** the user is returned to the update page for the same object.

---

### User Story 4 [Developer] — Delete Link Hidden When Delete View Is Not Configured (Priority: P3)

A developer uses `MVPUpdateView` for a model that has no delete view registered (or the current user lacks delete permission). The edit page renders without any delete link or button — no broken link, no 404, no error.

**Why this priority**: Graceful degradation is a safety requirement. The edit page must remain fully functional even when no delete route exists.

**Independent Test**: Omit `MVPDeleteView` from the CRUD directory (or set `has_delete_permission = False`). Load the update page and verify no delete link is rendered anywhere on the page.

**Acceptance Scenarios**:

1. **Given** no delete URL is registered for the model, **When** the update page is rendered, **Then** no delete link or button is visible.
2. **Given** `has_delete_permission` is falsy on the view, **When** the update page is rendered, **Then** no delete link or button is visible.
3. **Given** the delete URL resolves but returns an empty string from `resolve_crud_url`, **When** the update page is rendered, **Then** no delete link or button is visible.

---

### User Story 5 [Developer] — Three-Level Breadcrumb Degrades When Detail or List Is Missing (Priority: P3)

A developer uses `MVPUpdateView` for a model that has no detail URL or no list URL registered. The breadcrumb degrades gracefully: each missing link renders as plain text rather than a broken anchor.

**Why this priority**: Edge-case resilience mirrors the equivalent story in the create view spec. The breadcrumb must never generate an empty `href` or a 404-triggering link.

**Independent Test**: Configure `MVPUpdateView` with `has_list_permission = False` (or omit a list URL). Verify the breadcrumb list item renders as non-linked text. Separately, configure a model whose `get_absolute_url()` is not defined and verify the object-level breadcrumb item also renders as plain text.

**Acceptance Scenarios**:

1. **Given** no list URL can be resolved, **When** the page is rendered, **Then** the breadcrumb list item appears as plain text (no `href`).
2. **Given** `has_list_permission` is falsy, **When** the page is rendered, **Then** the breadcrumb list item appears as plain text.
3. **Given** the object's `get_absolute_url()` is not defined, **When** the page is rendered, **Then** the breadcrumb object item appears as plain text (no `href`).

---

### User Story 6 [End User] — Contextual Update Page Title and Confirmation (Priority: P1)

A site visitor navigates to an update page built on `MVPUpdateView`. The page heading names the record type being edited (e.g., "Update Product"), providing immediate context that they are editing an existing record — not creating a new one. After a valid form submission, a success flash confirms what changed in plain language (e.g., "Product successfully updated.").

**Audience**: End user — the visitor interacting with the live application.

**Why this priority**: The end-user experience of a correct, contextual title and confirmatory message is delivered by the same code change as US1. Both ship together.

**Independent Test**: Using a live test server, navigate to an update page and verify the page-title element contains "Update {verbose_name.title()}". Submit a valid form and verify the flash message is title-cased and grammatically correct.

**Acceptance Scenarios**:

1. **Given** I visit an update page, **When** the page loads, **Then** I see a title naming the record type I am editing (e.g., "Update Product") — not a generic placeholder such as "Update Entry".
2. **Given** I visit an update page, **When** the page loads, **Then** the breadcrumb shows me where I am: the list, then the record I am editing, then the current form — giving me clear navigation context.
3. **Given** I submit a valid form, **When** the save succeeds, **Then** I see a success message confirming what was updated in title-cased, human-readable language (e.g., "Product successfully updated.").

---

### Edge Cases

- What happens when the model has a multi-word verbose name (e.g., "order line")? The title must capitalise correctly: "Update Order Line".
- What happens when the form is invalid? The page re-renders with the same title, breadcrumb, and icon — no redirect, no change to the delete link.
- What happens when neither `object.get_absolute_url()` nor `success_url` is defined? `ImproperlyConfigured` is raised with a message that guides the developer to set `success_url`.
- What happens when `page_title` is set to `None`, `False`, or `""`? The falsy value is returned as-is — this is treated as a deliberate override. The class default (`_("Update %(verbose_name)s")`) is only used when the subclass does not override `page_title` at all.
- What happens when `get_delete_url()` raises an exception internally (e.g., URL reverse failure)? The exception must be caught and an empty string returned — no server error rendered to the user.
- What happens when the object's `__str__()` returns an empty string? The breadcrumb object item renders as an empty plain-text item — no crash, no omission of the breadcrumb level.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `MVPUpdateView` MUST produce a page title of "Update {verbose_name.title()}" by default, via a class-level `page_title` attribute set to the translatable interpolation template `_("Update %(verbose_name)s")`. `get_page_title()` interpolates this template with `{"verbose_name": verbose_name.title()}` at request time. When a subclass sets `page_title` to a truthy string, that string is interpolated instead (if it contains `%(verbose_name)s`) or returned as-is. When `page_title` is explicitly set to a falsy value (`None`, `False`, `""`), that value is returned directly as the caller's deliberate intent.
- **FR-002**: `MVPUpdateView` MUST display "edit" as the default page icon when `page_icon` is not overridden.
- **FR-003**: `MVPUpdateView` MUST apply "mvp-form-page" and "mvp-update-page" CSS classes to the page container when `page_class` is not overridden.
- **FR-004**: `MVPUpdateView` MUST display a default success message of "{verbose_name.title()} successfully updated." when `success_message` is not overridden.
- **FR-005**: `MVPUpdateView` MUST render a three-level breadcrumb: (1) `{verbose_name_plural.title()}` linking to the list URL, (2) `{str(object)}` linking to the object's detail URL, (3) the current page title with no link.
- **FR-006**: When the list URL cannot be resolved (no permission or no URL registered), the breadcrumb list item MUST appear as non-linked text rather than an empty or broken anchor.
- **FR-007**: When the object's detail URL cannot be resolved (e.g., `get_absolute_url()` not defined), the breadcrumb object item MUST appear as non-linked text rather than an empty or broken anchor.
- **FR-008**: `MVPUpdateView` MUST expose a `delete_url` variable in the template context, produced by `get_delete_url()`. When a delete view is accessible, `delete_url` is a URL string with `?back=<update_url>&next=<list_url>` query parameters appended. When no delete view is accessible, `delete_url` is an empty string.
- **FR-009**: The `form_view.html` template (or its Cotton card component) MUST render a visible delete link or button when `delete_url` is truthy, and MUST NOT render any delete control when `delete_url` is falsy or absent.
- **FR-010**: After a valid form submission, `MVPUpdateView` MUST redirect using the same 4-step priority chain as `MVPCreateView`: `?next=` parameter → `success_url` (CRUD shorthand or literal) → `object.get_absolute_url()` → `ImproperlyConfigured`.
- **FR-011**: All defaults (title, icon, CSS classes, success message, breadcrumb, delete URL) MUST be overridable by setting the corresponding class attribute or overriding the corresponding `get_*()` method on the subclass.
- **FR-012**: A minimal subclass with only `model` and `fields` set MUST pass Django's `manage.py check` without errors or warnings.
- **FR-013**: `MVPUpdateView` MUST NOT change the behaviour of `MVPCreateView`, `MVPDeleteView`, `MVPFormView`, or any base mixin class.

### Key Entities

- **MVPUpdateView**: A concrete view class combining `MVPModelFormBase` with Django's `generic.UpdateView`. Encapsulates all update-specific defaults. Developers subclass it directly and set `model` and `fields`.
- **Model**: The Django model being updated. Provides `verbose_name` (singular) and `verbose_name_plural` for title, breadcrumb, and success message generation.
- **Object**: The specific model instance being edited. Its `__str__()` result appears as the middle breadcrumb item; its detail URL (from `get_absolute_url()`) becomes the middle breadcrumb link.
- **Form**: Auto-generated from `fields`, or supplied via `form_class`. Rendered by the existing form rendering infrastructure inherited from `MVPFormBase`.
- **Delete URL**: A computed URL string (or empty string) surfaced to the template via the `delete_url` context variable. Built from the delete view URL plus `?back` and `?next` query parameters.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can produce a fully functional, correctly styled update page by writing exactly two class attributes (`model` and `fields`) — measurable by a passing test that exercises the full request/response cycle with only those two attributes set.
- **SC-002**: 100% of auto-generated page titles for models with single- and multi-word verbose names render with correct title-case capitalisation — verifiable by at least two named unit tests, one per case.
- **SC-003**: The breadcrumb always contains exactly three items for `MVPUpdateView` — verifiable by unit tests that count breadcrumb entries and check text and href values for each item.
- **SC-004**: The delete link is present in the rendered page when a delete view is accessible, and absent when it is not — verifiable by two contrasting unit tests (one with delete view registered, one without).
- **SC-005**: All six default attributes (title, icon, CSS, success message, breadcrumb, delete URL) can be independently overridden without affecting any other default — verifiable by six independent unit tests, one per attribute.
- **SC-006**: The view passes `manage.py check` with zero errors on a project that registers only `model` and `fields` — verifiable by running the system check in CI.
- **SC-007**: No existing tests for `MVPCreateView`, `MVPDeleteView`, or `MVPFormView` regress — verifiable by running the full test suite before and after the change.

## Assumptions

- The developer's project has already registered a URL for the update view (e.g., via `path("products/<pk>/update/", ProductUpdateView.as_view(), ...)`). This spec does not cover URL auto-registration.
- The breadcrumb list link is suppressed (plain text) when `has_list_permission` is falsy — the same permission model already used by `CRUDDirectoryMixin.resolve_crud_url()`.
- The breadcrumb object link is suppressed (plain text) when `object.get_absolute_url()` raises `AttributeError` or any other exception — no crash, no broken anchor.
- `verbose_name` and `verbose_name_plural` are assumed to be set correctly on the model's `Meta` class; if absent, Django's defaults (class name lowercased, pluralised) are used.
- The form template and card layout are provided by the existing `form_view.html` base template and Cotton components. The delete link rendering is gated by the `delete_url` context variable — `truthy → show link`, `falsy → hide link`.
- Multi-language support (i18n) is handled by wrapping default string constants in `gettext_lazy`; translators supply the translations.
- The auto-derived title is generated at request time (not at class-definition time), so it correctly reflects any model `verbose_name` overridden at runtime.
- The existing `MVPUpdateView` stub (currently with static `page_title = _("Update Entry")` and the full `get_breadcrumbs()` and `get_delete_url()` implementations) is the target of this change — the breadcrumb structure and delete URL logic already exist and only the model-aware title and title-cased success message need to be added.
- `get_delete_url()` already appends `?back` and `?next` query parameters; this spec does not change that behaviour, only documents and validates it.
