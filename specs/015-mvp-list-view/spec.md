# Feature Specification: MVPListView — Item Templates and Composed List Page

**Feature Branch**: `015-mvp-list-view`
**Created**: 2026-05-06
**Status**: Draft
**Input**: User description: "A list view renders a collection, but the way individual items in that collection are rendered varies enormously — cards, table rows, compact summaries, rich previews. This spec defines how a list view communicates to its template which partial should be used for each item, following Django's app/model naming convention by default, while allowing a fully custom template to be declared when needed. Additionally, our basic list view mixin should generate a full list page as a complete, usable thing. MVPListViewMixin brings together search, ordering, CRUD directory (limited to the create action from a list), empty state messaging, grid configuration, and page metadata. The result should be a paginated, searchable, orderable list page that works from a single model declaration. MVPListView is the concrete starting point."

## Clarifications

### Session 2026-05-06

- Q: Should `MVPListView` declare a default `paginate_by` so the zero-config promise covers pagination without developer intervention? → A: Yes — `MVPListView` declares `paginate_by = 24` as the library default (24 is evenly divisible by 1, 2, 3, and 4, making it grid-friendly for any column count). Developers may override to any value.
- Q: Is SC-004 (pagination links preserve `?q=` and `?o=` parameters) a view-level or template-level contract? → A: Template-level. The view's responsibility ends at injecting `search_query` and `current_ordering` into context. Pagination link construction is a template/component concern, verified in component tests, not here.
- Q: When a developer sets `page_title` on their subclass, does it take precedence over the model-derived default? → A: Yes — `page_title` class attribute takes precedence when set (non-falsy). `verbose_name_plural.title()` is used only as the fallback when `page_title` is falsy or not set.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Zero-Config List Page (Priority: P1)

**Audience**: [Developer]

A developer subclasses `MVPListView` and declares only `model = MyModel`. The resulting page is fully functional: it paginates the model's records, displays a page title derived from the model's human-readable plural name, and renders each record using a partial template whose path follows the project's naming convention. No extra attributes are required.

**Why this priority**: This is the library's promise — a single model declaration produces a complete, usable list page. Everything else in this spec is an opt-out or override of this default behaviour. If zero-config fails, all other stories are irrelevant.

**Independent Test**: Create a `MVPListView` subclass with only `model = Product`. Visit the list URL and confirm the page loads, shows a title equivalent to "Products" (the model's verbose name plural in title case), and that the template context contains a `list_item_template` key pointing to `demo/product_list_item.html` (following the convention — in tests, uses the `demo` app's `Product` model; app label = `demo`, model name = `product`).

**Acceptance Scenarios**:

1. **Given** a `MVPListView` subclass with `model = Product` and no other configuration, **When** a user visits the list URL, **Then** the page renders without error.
2. **Given** the same view with no `page_title` set, **When** the page is rendered, **Then** the page title is the model's verbose name plural in title case (e.g. "Products"). **Given** `page_title = "Our Catalogue"` is set, **Then** "Our Catalogue" is used instead.
3. **Given** the same view, **When** the page is rendered, **Then** the template context contains `list_item_template` set to `<app_label>/<model_name>_list_item.html` (e.g. `shop/product_list_item.html`).
4. **Given** the same view with 25 records and a page size of 10, **When** the user visits the first page, **Then** exactly 10 records are shown and pagination controls appear.

---

### User Story 2 — Item Template Convention and Override (Priority: P1)

**Audience**: [Developer]

A developer needs control over which partial template renders each list item. By default the view resolves the template path from the model's app label and name — a convention that mirrors Django's own template discovery — so teams following the convention need no configuration at all. When the default path is wrong (shared apps, custom partials, reusable components), the developer can set `list_item_template` to any explicit path, which takes full precedence.

**Why this priority**: Template resolution is the core subject of this spec. Without a correct, predictable convention developers cannot build list pages without always supplying a custom path, which defeats the zero-config promise.

**Independent Test**: (a) Configure a view with `model = Order` (app label `sales`) and no `list_item_template`. Confirm the context contains `list_item_template = "sales/order_list_item.html"`. (b) Add `list_item_template = "shared/order_card.html"` and confirm that value is used instead.

**Acceptance Scenarios**:

1. **Given** a list view with `model = Order` in app `sales` and no `list_item_template` set, **When** the page is rendered, **Then** `list_item_template` in context equals `"sales/order_list_item.html"`.
2. **Given** the same view with `list_item_template = "shared/order_card.html"` set explicitly, **When** the page is rendered, **Then** `list_item_template` in context equals `"shared/order_card.html"`, overriding the convention.
3. **Given** a list view with no `model` and no `list_item_template`, **When** the view is instantiated, **Then** an informative error is raised indicating that either `model` or `list_item_template` must be provided.

---

### User Story 3 — Empty State Messaging (Priority: P2)

**Audience**: [Developer] · [End User]

When the queryset returns zero records (either because the collection is genuinely empty or because an active search or filter matched nothing), the list page shows a helpful empty state rather than a blank area. A default heading and message are provided by the library; developers can override either with custom text to match their application's tone and content.

**Why this priority**: An empty list with no explanation is confusing for end users. A default empty state ships with the mixin so no developer effort is required for the common case.

**Independent Test**: Render a list view with an empty queryset. Confirm the template context contains `empty_state` with `heading` and `message` keys populated with the library defaults. Then set `empty_state_heading = "No orders yet"` and confirm that value appears in context.

**Acceptance Scenarios**:

1. **Given** a list view with no records in the queryset, **When** the page is rendered, **Then** the template context contains `empty_state.heading` and `empty_state.message` with non-empty default text.
2. **Given** a list view with `empty_state_heading = "No products found"` set, **When** the page is rendered, **Then** `empty_state.heading` in context equals `"No products found"`.
3. **Given** a list view with `empty_state_message = None`, **When** the page is rendered, **Then** `empty_state.message` is `None`, allowing the template to omit the message paragraph.
4. **Given** a list view with an active `?q=` search that matches no records, **When** the page is rendered, **Then** the empty state context is still present (the empty state is not conditional on the reason the list is empty).

---

### User Story 4 — "Create" Action Link from the List Page (Priority: P2)

**Audience**: [Developer] · [End User]

A developer can expose a "Create" link on the list page by setting `has_create_permission = True` (or a callable that checks the current user). The resolved URL is injected into the template context so a "New record" button can be rendered without any custom template logic. No other CRUD actions (detail, update, delete) are exposed from the list view — only create belongs in the list-page context.

**Why this priority**: A list page that cannot navigate to the create form is incomplete for any data-entry workflow. This is distinct from the detail/update/delete actions that belong on object pages.

**Independent Test**: Configure `has_create_permission = True` and a matching URL named `<model>-create` (using the project's naming convention). Confirm that `directory.create_url` is present in context and resolves to the correct URL. Then set `has_create_permission = False` and confirm `directory` does not contain `create_url`.

**Acceptance Scenarios**:

1. **Given** a list view with `has_create_permission = True`, **When** the page is rendered, **Then** `directory.create_url` is present in the template context and resolves to the model's create URL.
2. **Given** a list view with `has_create_permission = False` (the default), **When** the page is rendered, **Then** `directory` does not contain `create_url`.
3. **Given** a list view with `has_create_permission` set to a callable, **When** the callable returns `True` for the current user, **Then** `create_url` is present; **When** it returns `False`, **Then** `create_url` is absent.
4. **Given** a list view on the page, **When** the template renders a "New" button using `directory.create_url`, **Then** only the create URL is available — no detail, update, or delete URLs are injected by the list page.

---

### User Story 5 — Grid Configuration (Priority: P3)

**Audience**: [Developer]

A developer can pass a `grid` configuration dictionary to control how list items are laid out in a responsive grid. The configuration is passed through to the template context unchanged, where the template (or a Cotton component) uses it to apply responsive column classes. When no grid is configured the context still receives an empty dict, so templates can safely check for presence of grid values.

**Why this priority**: Different record types call for different layouts — a product catalogue uses cards in a 3-column grid; an activity feed uses a single-column list. Grid configuration makes this declarative without touching templates.

**Independent Test**: Set `grid = {"sm": 1, "md": 2, "lg": 3}` on a list view. Confirm that the template context contains `grid_config` equal to `{"sm": 1, "md": 2, "lg": 3}`. Confirm that a view with no `grid` attribute set still injects `grid_config` as an empty dict.

**Acceptance Scenarios**:

1. **Given** a list view with `grid = {"sm": 1, "md": 2, "lg": 3}`, **When** the page is rendered, **Then** `grid_config` in context equals `{"sm": 1, "md": 2, "lg": 3}`.
2. **Given** a list view with no `grid` configured, **When** the page is rendered, **Then** `grid_config` in context is an empty dict.

---

### User Story 6 — Search, Ordering, and Pagination Compose Cleanly (Priority: P2)

**Audience**: [Developer] · [End User]

A developer can activate search (`search_fields`) and ordering (`order_by`) on an `MVPListView` using the same attributes defined by `SearchMixin` and `OrderMixin` (spec 014). All three — search, ordering, and pagination — compose cleanly: a user can search for records, order the results, and navigate across pages without losing either the search term or the ordering selection.

**Why this priority**: The list view is only useful in practice if these three features cooperate. A user who searches on page 1 and then goes to page 2 must not lose their search term.

**Independent Test**: Configure a view with `search_fields`, `order_by`, and `paginate_by`. Submit `?q=foo&o=name_asc&page=2` and verify that the second page shows only records matching "foo", ordered by name ascending. Confirm search and ordering parameters are preserved in pagination links.

**Acceptance Scenarios**:

1. **Given** a list view with `search_fields`, `order_by`, and `paginate_by = 10` set, **When** the user visits `?q=foo&o=name_asc&page=2`, **Then** the second page of results filtered by "foo" and ordered by name ascending is shown.
2. **Given** the same view, **When** the page is rendered, **Then** the template context contains `search_query` and `current_ordering` with the active parameter values, enabling the template to construct pagination links that preserve both.
3. **Given** the same view with neither `search_fields` nor `order_by` configured, **When** the user visits with no query parameters, **Then** the page renders correctly with standard pagination.

---

### Edge Cases

- What happens when `model` is not set and `list_item_template` is also not set? An informative configuration error is raised before the view renders, naming the missing attribute.
- What happens when `list_item_template` is set to an empty string `""`? It is treated as falsy; the auto-discovery convention is used instead.
- What happens when the model belongs to an app whose label contains hyphens or uppercase letters? The convention uses `model._meta.app_label` and `model._meta.model_name`, which Django normalises to lowercase underscores — no special handling is required.
- What happens when `has_create_permission` is a callable and it raises an exception? The exception propagates; the view does not silently swallow it.
- What happens when `paginate_by` is not set? No pagination controls are shown; all records are returned on one page (standard Django `ListView` behaviour).
- What happens when `get_list_item_template()` is overridden in a subclass? The override takes full precedence; neither `list_item_template` nor the auto-discovery logic runs.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `MVPListViewMixin` MUST resolve a list item template path using the convention `<app_label>/<model_name>_list_item.html` when `list_item_template` is not set.
- **FR-002**: When `list_item_template` is set to a non-empty string, that value MUST be used as the item template path, bypassing the convention.
- **FR-003**: The resolved item template path MUST be injected into the template context under the key `list_item_template`.
- **FR-004**: When neither `model` nor `list_item_template` is configured, the view MUST raise an informative error before rendering.
- **FR-005**: `MVPListViewMixin` MUST inject `empty_state` into the template context as a dict with keys `heading` and `message`, populated from `empty_state_heading` and `empty_state_message` class attributes.
- **FR-006**: The default `empty_state_heading` MUST be a non-empty translated string; the default `empty_state_message` MUST be a non-empty translated string.
- **FR-007**: Either `empty_state_heading` or `empty_state_message` MAY be set to `None` to suppress that element; the template is responsible for conditional rendering.
- **FR-008**: `MVPListViewMixin` MUST inject `grid_config` into the template context, set to the value of the `grid` attribute (default: empty dict).
- **FR-009**: The `directory` on `MVPListViewMixin` MUST be limited to `["create"]` — no detail, update, or delete URLs are provided from the list page context.
- **FR-010**: `get_page_title()` MUST return the `page_title` class attribute when it is set to a non-falsy value. When `page_title` is falsy or not set, it MUST fall back to the model's `verbose_name_plural` in title case.
- **FR-011**: The default breadcrumb trail MUST consist of a Home link followed by the current page title as the active (non-linked) item.
- **FR-012**: `MVPListViewMixin` MUST compose with `SearchMixin` and `OrderMixin` (spec 014) so that `search_fields` and `order_by` can be declared directly on the view class.
- **FR-013**: `MVPListView` MUST be the concrete class combining `MVPListViewMixin` with Django's built-in `ListView`, requiring no additional configuration to instantiate beyond those inherited from `MVPListViewMixin`. It MUST declare `paginate_by = 24` as the library default (grid-friendly: divisible by 1, 2, 3, and 4); subclasses may override this value.
- **FR-014**: `get_list_item_template()` MUST be an overrideable hook that subclasses can replace to implement any custom resolution logic.
- **FR-015**: The `list_item_template` context key MUST always be present in the rendered context, even when the referenced partial template does not exist on disk — template existence is the template engine's responsibility, not the view's.

### Key Entities

- **MVPListViewMixin**: The composable mixin that wires together item template resolution, empty state, grid configuration, create-action directory, page title, and breadcrumbs. Not used standalone — always combined with a Django view base class.
- **MVPListView**: The concrete, ready-to-use list view class. Combines `MVPListViewMixin` with Django's `ListView`. Declares `paginate_by = 24`. The developer's default starting point.
- **list_item_template**: A class attribute (string or `None`) that overrides item template auto-discovery. When set, it is used as-is. When falsy, the `<app_label>/<model_name>_list_item.html` convention applies.
- **empty_state**: A context dict with `heading` (str or `None`) and `message` (str or `None`) that the template uses to render the no-records state. Always present in context.
- **grid_config**: A context dict passed through from the `grid` class attribute. Content and structure are defined by the consuming template/component. Always present in context (may be empty dict).
- **directory**: A context dict (from `CRUDDirectoryMixin`) containing resolved CRUD URLs. For list views, only `create_url` is eligible; other actions are not included.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can produce a functional, paginated list page (with a 24-record default page size) by writing a view subclass with a single `model` attribute — no other configuration required. Verified by zero-extra-attribute test cases.
- **SC-002**: The item template convention (`<app_label>/<model_name>_list_item.html`) is derived entirely from the model's metadata — no string construction is left to the developer. Verified by unit tests with multiple model/app combinations.
- **SC-003**: All context keys injected by `MVPListViewMixin` (`list_item_template`, `empty_state`, `grid_config`, `directory`) are present in every rendered response, regardless of which optional attributes are configured. Verified by a "defaults-only" test case.
- **SC-004**: The view injects `search_query` (always present, `""` when search is unconfigured) and `current_ordering` (present only when `order_by` is configured, `""` when the `?o=` value is absent or unrecognised) into context so that templates can construct pagination links that preserve active `?q=` and `?o=` parameters. Verified by unit tests confirming context key presence and correct values; link construction is verified in template/component tests, not here.
- **SC-005**: An attempt to instantiate the view without `model` or `list_item_template` produces a clear, actionable error message that names the missing configuration and the class where it must be set.

## Assumptions

- The `SearchMixin` and `OrderMixin` (spec 014) are implemented and stable. `MVPListViewMixin` inherits from both via `SearchOrderMixin` without re-specifying their behaviour.
- `CRUDDirectoryMixin` is already implemented and supports the `directory` attribute controlling which CRUD actions are included in context. The list view sets `directory = ["create"]`.
- `PageMixin` is already implemented and provides `page_title`, `get_page_title()`, `get_breadcrumbs()`, and related page metadata. `MVPListViewMixin` overrides `get_page_title()` to default to the model's verbose name plural.
- The `grid` dictionary's schema (which keys map to which column widths) is defined by the consuming Cotton component, not by this mixin. This spec only requires that the dict is passed through unchanged.
- Django's built-in `ListView` handles all pagination mechanics (`paginate_by`, `page_kwarg`, `paginator_class`). `MVPListView` inherits this behaviour without reimplementing it.
- `MVPFilteredListView` (the `django-filter` variant) is out of scope for this spec. Its composition with `MVPListViewMixin` is an existing concern and is not changed by this feature.
- Access control (authentication, permissions) is the application developer's responsibility. The view does not enforce who can visit the list page.
- Preservation of `?q=` and `?o=` parameters in pagination links is a template/component responsibility. The view guarantees `search_query` and `current_ordering` are injected into context (via `SearchMixin` and `OrderMixin` respectively); link construction is not the view's concern.
