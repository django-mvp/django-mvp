# Feature Specification: MVPCreateView — Zero-Config Model Create View

**Feature Branch**: `011-mvp-create-view`
**Created**: 2026-05-05
**Status**: Draft
**Input**: User description: "The create view is one of the most frequently written views in any Django project. This spec defines a version that is immediately usable from a model declaration alone — with a sensible default title, icon, CSS modifier, and success message built in — while remaining fully customisable for cases that need different behaviour. A developer should be able to ship a working create page with two lines of code that fits into the wider MVP framework and UI."

## User Scenarios & Testing *(mandatory)*

### User Story 1 [Developer] — Zero-Config Create Page (Priority: P1)

A developer registers a create view for their `Product` model using only the two required class attributes (`model` and `fields`). The resulting page has a model-aware title ("Create Product"), a pre-wired success message, a link back to the list view in the breadcrumb, and the correct icon and CSS modifier — all without any additional configuration.

**Why this priority**: This is the core value proposition. Every other story depends on the zero-config path working correctly before customisation is layered on top.

**Independent Test**: Create `class ProductCreateView(MVPCreateView): model = Product; fields = ["name"]` in a test project. Navigate to the create URL. Verify title, breadcrumb, icon, form rendering, and post-save redirect all work correctly.

**Acceptance Scenarios**:

1. **Given** a `MVPCreateView` subclass with only `model` and `fields` set, **When** the page is rendered, **Then** the page title reads "Create {verbose\_name.title()}" (e.g., "Create Product").
2. **Given** a `MVPCreateView` subclass, **When** the page is rendered, **Then** the breadcrumb shows "{verbose\_name\_plural.title()}" linking to the list URL, followed by the current page title without a link.
3. **Given** a `MVPCreateView` subclass, **When** the page is rendered, **Then** the page icon is "add" and the page CSS classes include "mvp-form-page" and "mvp-create-page".
4. **Given** a valid form submission, **When** the object is saved, **Then** a success message "{verbose\_name.title()} successfully created." is displayed on the next page.
5. **Given** a valid form submission and no explicit `success_url`, **When** the object is saved, **Then** the user is redirected to the new object's detail URL (via `object.get_absolute_url()`); if `get_absolute_url()` is not defined, `ImproperlyConfigured` is raised guiding the developer to set `success_url`.

---

### User Story 2 [Developer] — Customised Title and Message (Priority: P2)

A developer overrides the default title and success message to match their application's language and branding, without touching any other behaviour.

**Why this priority**: Customisation is the second-most-critical requirement. Developers must be able to escape the defaults without subclassing multiple levels.

**Independent Test**: Set `page_title = "Add a new product"` and `success_message = "%(name)s was added."` on the view class. Verify the page renders the custom title and the success flash shows the custom message.

**Acceptance Scenarios**:

1. **Given** `page_title` is explicitly set on the subclass, **When** the page is rendered, **Then** the explicit title is displayed instead of the auto-derived one.
2. **Given** `success_message` is explicitly set on the subclass, **When** a valid form is submitted, **Then** the custom message (with `cleaned_data` interpolation) is displayed instead of the default.
3. **Given** `page_icon` is set to a different value, **When** the page is rendered, **Then** the overridden icon is used.
4. **Given** `success_url` is set to a CRUD shorthand (e.g., `"list"`) or a literal path, **When** a valid form is submitted, **Then** the user is redirected to that destination.

---

### User Story 3 [Developer] — Breadcrumb When No List View Exists (Priority: P3)

A developer uses `MVPCreateView` for a standalone model that has no list view registered in the CRUD directory. The breadcrumb degrades gracefully: the list title appears as plain text rather than a broken link.

**Why this priority**: Edge-case resilience. The primary flows already cover the happy path; this story protects against the most common misconfiguration.

**Independent Test**: Configure `MVPCreateView` with `has_list_permission = False` (or omit a list URL entirely). Verify the breadcrumb first item renders as non-linked text, not a 404-generating anchor.

**Acceptance Scenarios**:

1. **Given** no list URL can be resolved, **When** the page is rendered, **Then** the breadcrumb list item appears as plain text (no `href`).
2. **Given** `has_list_permission` is falsy, **When** the page is rendered, **Then** the breadcrumb list item appears as plain text.

---

### User Story 4 [End User] — Model-Aware Page Title and Success Feedback (Priority: P1)

A site visitor navigates to a create page built on `MVPCreateView`. The page heading names the record type being created (e.g., "Create Product"), providing clear context. After a valid form submission, a success flash confirms the action in plain language (e.g., "Product successfully created.").

**Audience**: End user — the visitor interacting with the live application.

**Why this priority**: The end-user experience of a correct title and confirmatory message is delivered by the same code change as US1. Both ship together.

**Independent Test**: Using a live test server, navigate to a create page and verify the page-title element contains "Create {verbose\_name.title()}". Submit a valid form and verify the flash message is title-cased and grammatically correct.

**Acceptance Scenarios**:

1. **Given** I visit a create page, **When** the page loads, **Then** I see a title naming the record type I am creating (e.g., "Create Product") — not a generic placeholder such as "Create Entry".
2. **Given** I submit a valid form, **When** the save succeeds, **Then** I see a success message confirming what was created in title-cased, human-readable language (e.g., "Product successfully created.").

---

### Edge Cases

- What happens when the model has a multi-word verbose name (e.g., "order line")? The title should capitalise correctly: "Create Order Line".
- What happens when the form is invalid? The page re-renders with the same title, breadcrumb, and icon — no redirect.
- What happens when neither `object.get_absolute_url()` nor `success_url` is defined? `ImproperlyConfigured` is raised with a message that guides the developer to set `success_url`.
- What happens when `success_message` contains `%(verbose_name)s` and a field key that is absent from `cleaned_data`? The absent key silently substitutes `""` (no `KeyError`).
- What happens when `page_title` is set to `None`, `False`, or `""`? The falsy value is returned as-is — this is treated as a deliberate override. The class default (`_("Create %(verbose_name)s")`) is only used when the subclass does not override `page_title` at all.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `MVPCreateView` MUST produce a page title of "Create {verbose\_name.title()}" by default, via a class-level `page_title` attribute set to the translatable interpolation template `_("Create %(verbose_name)s")`. `get_page_title()` interpolates this template with `{"verbose_name": verbose_name.title()}` at request time. When a subclass sets `page_title` to a truthy string, that string is interpolated instead. When `page_title` is explicitly set to a falsy value (`None`, `False`, `""`), that value is returned directly as the caller's deliberate intent.
- **FR-002**: `MVPCreateView` MUST display "add" as the default page icon when `page_icon` is not overridden.
- **FR-003**: `MVPCreateView` MUST apply "mvp-form-page" and "mvp-create-page" CSS classes to the page container when `page_class` is not overridden.
- **FR-004**: `MVPCreateView` MUST display a default success message of "{verbose\_name.title()} successfully created." when `success_message` is not overridden.
- **FR-005**: `MVPCreateView` MUST render a breadcrumb with a list link labelled `{verbose_name_plural.title()}` as the first item and the current page title as the final (non-linked) item.
- **FR-006**: When the list URL cannot be resolved (no permission, no URL registered), the breadcrumb list item MUST appear as non-linked text rather than an empty or broken anchor.
- **FR-007**: After a valid form submission, `MVPCreateView` MUST redirect using the 4-step priority chain: `?next=` parameter → `success_url` (CRUD shorthand or literal) → `object.get_absolute_url()` → `ImproperlyConfigured`.
- **FR-008**: All defaults (title, icon, CSS classes, success message, success URL) MUST be overridable by setting the corresponding class attribute or overriding the corresponding `get_*()` method on the subclass.
- **FR-009**: A minimal subclass with only `model` and `fields` set MUST pass Django's `manage.py check` without errors or warnings.
- **FR-010**: `MVPCreateView` MUST NOT change the behaviour of `MVPUpdateView`, `MVPDeleteView`, `MVPFormView`, or any base mixin class.

### Key Entities

- **MVPCreateView**: A concrete view class combining `MVPModelFormBase` with Django's `generic.CreateView`. Encapsulates all create-specific defaults. Developers subclass it directly and set `model` and `fields`.
- **Model**: The Django model being created. Provides `verbose_name` (singular) and `verbose_name_plural` for title and breadcrumb generation.
- **Form**: Auto-generated from `fields`, or supplied via `form_class`. Rendered by the existing form rendering infrastructure inherited from `MVPFormBase`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can produce a fully functional, correctly styled create page by writing exactly two class attributes (`model` and `fields`) — measurable by a passing test that exercises the full request/response cycle with only those two attributes set.
- **SC-002**: 100% of auto-generated page titles for models with single- and multi-word verbose names render with correct title-case capitalisation (verifiable by at least two named unit tests, one per case).
- **SC-003**: All five default attributes (title, icon, CSS, success message, breadcrumb) can be independently overridden without affecting any other default — verifiable by five independent unit tests, one per attribute; breadcrumb override is verified via `get_breadcrumbs()` in `TestMVPCreateViewBreadcrumb`.
- **SC-004**: The view passes `manage.py check` with zero errors on a project that registers only `model` and `fields` — verifiable by running the system check in CI.
- **SC-005**: No existing tests for `MVPUpdateView`, `MVPDeleteView`, or `MVPFormView` regress — verifiable by running the full test suite before and after the change.

## Assumptions

- The developer's project has already registered a URL for the create view (e.g., via `path("products/create/", ProductCreateView.as_view(), ...)`). This spec does not cover URL auto-registration.
- The breadcrumb list link is suppressed (plain text) when `has_list_permission` is falsy — the same permission model already used by `CRUDDirectoryMixin.resolve_crud_url()`.
- `verbose_name` is assumed to be set correctly on the model's `Meta` class; if absent, Django's default (class name lowercased) is used.
- The form template and card layout are provided by the existing `form_view.html` base template and Cotton components; this feature does not add or change any template file.
- Multi-language support (i18n) is handled by wrapping default string constants in `gettext_lazy`; translators supply the translations.
- The auto-derived title is generated at request time (not at class-definition time), so it correctly reflects any model `verbose_name` overridden at runtime.
- The existing `MVPCreateView` stub (currently with static `page_title = _("Create Entry")`) is the target of this change — no new class is introduced.
