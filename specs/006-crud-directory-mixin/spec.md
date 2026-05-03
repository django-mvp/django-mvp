# Feature Specification: CRUD Directory Mixin

**Feature Branch**: `006-crud-directory-mixin`
**Created**: 2026-05-03
**Status**: Draft
**Input**: User description: "Remembering CRUD view names, resolving them and providing the correct kwargs can quickly become a nightmare in django projects that often delegate to templates for such requirements. The CRUDDirectoryMixin aims to resolve this by assuming a standard set of view names, correctly identifying the current model class, gathering provided url kwargs and detecting user permissions. With these things, the view is able to perform permission-based url resolution for the current model automatically and inject it into the context dict via a 'directory' variable. The intent is that developers can rely on the presence/absence of a particular url inside the template in order to generate links/button to related CRUD pages."

## Clarifications

### Session 2026-05-03

- Q: Should the URL kwargs API use a single method or two dedicated methods? → A: Single method `get_url_kwargs(action: str) -> dict | None`. Default implementation: returns `{}` for `"list"` and `"create"` (collection-level); returns `dict(self.kwargs) or None` for all other actions (object-level and custom). Returning `None` suppresses the action silently. No `_OBJECT_ACTIONS` or `_COLLECTION_ACTIONS` frozensets needed — the logic lives in the default implementation and subclasses override the whole method.
- Q: Should custom actions (beyond the 5 standard ones) be treated as object-level or collection-level by default? → A: Object-level. Custom actions are not `"list"` or `"create"`, so they fall into the `dict(self.kwargs) or None` branch of the default `get_url_kwargs()` — suppressed when no URL kwargs are present.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Declare Which CRUD Links to Surface Without Manually Reversing URLs (Priority: P1) [Developer]

As a developer building a detail or form view, I want to declare which CRUD actions should have links available in the template — by listing action names such as `list`, `detail`, `update`, `delete`, and `create` — without writing any URL reversal code myself. The framework should derive the correct URL from the current model and the declared action name, and make it available in the template context under a predictable key.

**Audience**: Developer (integrator)
**Why this priority**: This is the foundational contract of the mixin. Every downstream use — rendering action buttons, generating breadcrumbs, building toolbars — depends on developers being able to express their intent declaratively with no URL wiring boilerplate.
**Independent Test**: A view that sets `directory = ["list", "detail", "update", "delete"]` and satisfies the permission checks produces a `directory` context key containing exactly the declared URLs resolved to the correct paths. Verified with a minimal view and a URL configuration matching the project's naming convention.

**Acceptance Scenarios**:

1. **Given** a view sets `directory = ["list"]` and the corresponding list URL exists, **When** the view renders, **Then** the template context contains `directory["list_url"]` pointing to the correct list URL for the current model.
2. **Given** a view sets `directory = ["detail", "update", "delete"]` and an object-level URL is in scope, **When** the view renders, **Then** the context contains `detail_url`, `update_url`, and `delete_url` correctly resolved with the object's URL kwargs.
3. **Given** a view sets `directory = []` (empty), **When** the view renders, **Then** the context contains `directory` as an empty dict.
4. **Given** a URL pattern for an action does not exist, **When** a request is handled, **Then** a URL reversal error is raised that identifies the failing URL name, making the misconfiguration traceable.

---

### User Story 2 - Gate Directory URLs on User Permissions (Priority: P1) [Developer]

As a developer, I want to control which URLs appear in the directory based on whether the current user has the appropriate permission, so I can declare permission rules on the view rather than duplicating permission logic inside templates.

**Audience**: Developer (integrator)
**Why this priority**: Security-critical. Without permission gating, templates would need to duplicate authorization logic, creating risk of inconsistent enforcement. Centralizing it on the view ensures that URLs only appear when the user is authorized.
**Independent Test**: A view with `has_delete_permission = False` and `directory = ["delete"]` must produce an empty `directory` context dict. A view where `has_delete_permission` is a callable that returns `True` for the current user must include `delete_url` in the context.

**Acceptance Scenarios**:

1. **Given** a view sets `has_update_permission = False`, **When** `update` is in `directory`, **Then** `update_url` is absent from the `directory` context dict.
2. **Given** a view sets `has_detail_permission = True`, **When** `detail` is in `directory`, **Then** `detail_url` is present in the `directory` context dict.
3. **Given** `has_create_permission` is a callable that returns `True` for admin users and `False` for others, **When** an admin user requests the view, **Then** `create_url` appears in `directory`; when a non-admin user requests the same view, `create_url` is absent.
4. **Given** a permission attribute is absent entirely from the view class, **When** the corresponding action is in `directory`, **Then** the URL is excluded from the `directory` context (absent permission treated as denied).

---

### User Story 3 - Override URL Kwargs for Nested Resource URLs (Priority: P2) [Developer]

As a developer working with nested URL patterns (e.g. `/projects/<project_pk>/tasks/<pk>/`), I want to override a single method to control which URL kwargs are passed when reversing CRUD URLs, so that sibling views that do not require all parent resource identifiers are still correctly resolved.

**Audience**: Developer (integrator)
**Why this priority**: Nested resource routing is a common pattern in real-world projects. Without an override point, the default kwargs forwarding would inject unexpected parameters into sibling URLs, causing reversal failures.
**Independent Test**: A view with nested URL kwargs (e.g. `project_pk` and `pk`) overrides `get_url_kwargs(action)` to return only `{"project_pk": ..., "pk": ...}` for object-level actions and `{"project_pk": ...}` for collection-level actions. All URLs resolve correctly with no `NoReverseMatch` errors.

**Acceptance Scenarios**:

1. **Given** a view captures `project_pk` and `pk` from the URL, **When** `get_url_kwargs(action)` is overridden to return the appropriate subset per action, **Then** all directory URLs resolve without reversal errors.
2. **Given** `get_url_kwargs(action)` returns `None`, **When** any action is in `directory`, **Then** that action's URL is excluded from the context silently (no error raised).

---

### User Story 4 - Customize the View Name Convention for Non-Standard Projects (Priority: P2) [Developer]

As a developer whose project does not follow the default `{app_name}_{model_name}_{action}` URL naming convention, I want to override the view name mapping so the directory resolves correctly without requiring me to rename all my URL patterns.

**Audience**: Developer (integrator)
**Why this priority**: Projects acquired, migrated, or using custom naming conventions cannot adopt the mixin without this escape hatch. The override must be clean enough not to require subclassing just to change a naming pattern.
**Independent Test**: A view sets `crud_views = {"list": "my_app:my-{model_name}-index", "detail": "my_app:my-{model_name}-view"}`. URLs for `list` and `detail` actions are resolved using the custom names, not the defaults.

**Acceptance Scenarios**:

1. **Given** a view sets `crud_views` to a dict with custom name patterns, **When** the view renders with the appropriate permissions, **Then** the directory URLs are resolved using the custom patterns.
2. **Given** a custom `crud_views` entry references an action name not in the standard set, **When** the action is not in `directory`, **Then** no error is raised.

---

### User Story 5 - Render Navigation Links Only for Available Actions (Priority: P1) [End User]

As an end user browsing a model-driven page — a detail page, an edit form, or a delete confirmation — I see action buttons and navigation links only for the operations I am permitted to perform. I do not see broken links, unauthorized action buttons, or missing navigation options that I should have access to.

**Audience**: End User
**Why this priority**: Direct impact on usability and security perception. Showing buttons for actions a user cannot perform creates confusion and erodes trust. Hiding permitted actions creates frustration.
**Independent Test**: Two user roles (admin and read-only) request the same detail page. The admin's rendered page contains edit and delete buttons. The read-only user's rendered page omits those buttons. Neither page contains broken links.

**Acceptance Scenarios**:

1. **Given** a user has read-only access, **When** they view a detail page, **Then** no edit or delete action buttons are visible.
2. **Given** a user has full CRUD access, **When** they view a detail page, **Then** all permitted action buttons are visible and their links navigate to the correct pages.
3. **Given** a user navigates from a list page to a detail page, **When** a `list_url` is in the directory, **Then** a link back to the list is present and navigates to the correct list view.

---

### Edge Cases

- An action is listed in `directory` but there is no permission attribute defined for it — the URL must be excluded, not raise an `AttributeError`.
- A callable permission attribute raises an exception — the exception must propagate; it must not be silently swallowed and treated as a denial.
- Object-level actions (`detail`, `update`, `delete`) are in `directory` but the view has no URL kwargs (e.g. a list view) — those URLs must be excluded silently via `get_url_kwargs(action)` returning `None`, not raise a reversal error.
- `directory` contains an action name not present in `crud_views` — an informative error must identify the unknown action name.
- `get_url_kwargs(action)` returns a dict with keys that do not match the target URL’s signature — a reversal error is raised; it must propagate with a message traceable to the action name.
- All permissions are denied — the context must contain `directory` as an empty dict, not as `None` or missing entirely.
- Two actions in `directory` resolve to the same URL (e.g. due to view name collision) — both entries must be included independently; deduplication is not performed.
- A custom action is added to `crud_views` and `directory` — it is treated as object-level by default and is suppressed silently when `get_url_kwargs(action)` returns `None`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The mixin MUST accept a `directory` attribute on the view class — a list of action names (e.g. `["list", "detail", "update", "delete", "create"]`) — that declares which CRUD URLs to resolve for the current request.
- **FR-002**: The mixin MUST resolve each declared action to a URL by combining the action's configured view name pattern with the current model's name and application label.
- **FR-003**: The mixin MUST inject the resolved URLs into the template context under the key `directory` as a dict, with each entry keyed as `{action}_url` (e.g. `list_url`, `update_url`).
- **FR-004**: The mixin MUST exclude an action's URL from the context when the corresponding `has_{action}_permission` attribute is `False`, absent, or a callable that returns `False` for the current user.
- **FR-005**: The mixin MUST include an action's URL in the context when the corresponding `has_{action}_permission` attribute is `True` or a callable that returns `True` for the current user.
- **FR-006**: The mixin MUST use all URL kwargs captured from the current request (via `self.kwargs`) as the default set of kwargs when reversing object-level URLs.
- **FR-007**: The mixin MUST provide a single override point `get_url_kwargs(action: str) -> dict | None` that developers can override to control which URL kwargs are forwarded per action. The default implementation MUST return `{}` for `"list"` and `"create"`, and `dict(self.kwargs) or None` for all other actions (including custom actions). Returning `None` suppresses the action silently.
- **FR-008**: Any action MUST be excluded from the context when `get_url_kwargs(action)` returns `None`, without raising a reversal error.
- **FR-009**: The mixin MUST provide a configurable `crud_views` attribute — a dict mapping action names to URL name patterns — so developers can substitute the default naming convention for their project's conventions. Patterns MUST support `{model_name}` and `{app_name}` substitution tokens.
- **FR-010**: When an action listed in `directory` is not present in `crud_views`, the mixin MUST raise an informative error identifying the unknown action name.
- **FR-011**: The `directory` context key MUST always be present in the template context (as an empty dict when no URLs are resolved), never absent or `None`.
- **FR-012**: The mixin MUST be composable with `ModelInfoMixin` so that model name and application label are always available for URL name resolution without additional configuration.
- **FR-013**: Custom actions — action names not among the 5 standard ones (`list`, `create`, `detail`, `update`, `delete`) — MUST be treated as object-level by default. This is a natural consequence of the `get_url_kwargs()` default implementation: custom actions are not `"list"` or `"create"`, so they use `dict(self.kwargs) or None` and are suppressed silently when no URL kwargs are present.

### Assumptions

- This specification is prescriptive. The plan phase is responsible for evaluating whether the current `CRUDDirectoryMixin` implementation fully satisfies all requirements.
- The default `crud_views` naming convention follows the project's established `{app_name}_{model_name}_{action}` pattern as already defined in `MVP_DEFAULT_VIEW_NAMES`.
- Permission attribute names follow the pattern `has_{action}_permission` for the five standard CRUD actions: `create`, `detail`, `update`, `delete`, and `list`. Non-standard action names follow the same pattern.
- Callable permission attributes receive `request.user` as their sole argument and return a boolean.
- The mixin is designed for use in class-based views. Function-based views are out of scope.
- URL reversal errors (e.g. `NoReverseMatch`) are not suppressed — they are genuine misconfiguration signals that should surface during development.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of acceptance scenarios across all user stories pass in automated testing with no template-level URL construction required.
- **SC-002**: A developer can enable the full CRUD directory on a new view by adding the mixin and setting `directory` and permission attributes — zero URL reversal code in the view or template.
- **SC-003**: Permitted action URLs are present and non-permitted action URLs are absent in 100% of tested permission combinations (all granted, all denied, mixed).
- **SC-004**: Object-level action URLs are absent in 100% of cases where the view has no URL kwargs, with no reversal errors raised.
- **SC-005**: The `directory` context key is present in 100% of rendered responses from views that include the mixin, including responses where all permissions are denied.
