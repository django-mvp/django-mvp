# Feature Specification: Object Page Foundation

**Feature Branch**: `007-object-page-foundation`
**Created**: 2026-05-03
**Status**: Draft — Prescriptive (planner evaluates whether current code needs changes, moves, or additions)
**Input**: User description: "Object Page Foundation — All object-level views — detail, create, update, delete — share a common set of concerns: knowing which model they work with, knowing which sibling URLs exist, and presenting a consistent page header and breadcrumb trail. This spec defines the composition that makes all of that available in one place, so that concrete views only need to declare what makes them different. The detail view is the simplest concrete result: a read-only page whose title comes from the object itself."

## Clarifications

### Session 2026-05-03

- Q: Should this spec be treated as prescriptive or descriptive? → A: Prescriptive — spec defines the target state; planner evaluates whether current code needs changes, moves, or additions.
- Q: What is in scope for this spec? → A: Foundation scope — `PageObjectMixin` + `MVPDetailView` only. Concrete create/update/delete views are out of scope and belong in a separate spec.
- Q: Should the model-name CSS class (e.g. `order-page`) come from `PageObjectMixin` or each concrete view? → A: `PageObjectMixin` adds the model-name class; concrete views add only their own action class (e.g. `mvp-detail-page`).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Inherit All Object-View Concerns From a Single Base (Priority: P1) [Developer]

As a developer building object-level views, I want to inherit a single base class (`PageObjectMixin`) that already knows the model, has resolved which sibling URLs are available, and can render a consistent page header and breadcrumb trail — so that concrete views only need to declare what makes them different. This spec delivers `PageObjectMixin` and its first concrete application, `MVPDetailView`; concrete create, update, and delete views are out of scope.

**Audience**: Developer (integrator)
**Why this priority**: Every object-level view in a project built with django-mvp touches the same three shared concerns. Shipping them as a cohesive single base eliminates boilerplate on every concrete view and ensures these concerns are always assembled in the same way.
**Independent Test**: A minimal concrete view class that inherits only the shared base and sets no extra attributes renders a page where `page.title`, `page.breadcrumbs`, and `directory` are all populated correctly, without any additional configuration in the view class itself.

**Acceptance Scenarios**:

1. **Given** a view inherits the shared base and sets `model`, `has_list_permission = True`, and `directory = ["list"]`, **When** the view renders, **Then** the template context contains a populated `page` dict and a `directory` dict with `list_url`.
2. **Given** a view inherits the shared base but does not override `list_view_title`, **When** the view renders, **Then** the breadcrumb link to the list view uses the model's plural verbose name, title-cased.
3. **Given** a view overrides `list_view_title = "All Orders"`, **When** the view renders, **Then** the breadcrumb link to the list view reads "All Orders".
4. **Given** `has_list_permission = False` on the view, **When** the view renders, **Then** `get_crud_url("list")` returns an empty string and the breadcrumb link has no `href`.

---

### User Story 2 - Use MVPDetailView as a Zero-Configuration Read-Only Page (Priority: P1) [Developer]

As a developer who needs a read-only detail page for a model, I want to point a view at a model and immediately get a working page — with the object's string representation as the page title, a breadcrumb trail back to the list, and a model-scoped CSS class — without writing any boilerplate.

**Audience**: Developer (integrator)
**Why this priority**: The detail view is the simplest and most common object-level view. Making it zero-config is the first proof that the shared base works and the most direct path to developer productivity.
**Independent Test**: A view class that inherits `MVPDetailView` and sets only `model` is wired to a URL. Requesting it for a saved object renders a page whose title equals `str(object)`, whose breadcrumbs end with the object's string, and whose page container carries a CSS class derived from the model name.

**Acceptance Scenarios**:

1. **Given** a view inherits `MVPDetailView` and sets only `model = Order`, **When** a request is made for a specific Order, **Then** `page.title` equals `str(order_instance)`.
2. **Given** an `MVPDetailView` subclass, **When** the page renders, **Then** the page container CSS class includes both the model-name class from `PageObjectMixin` (e.g. `order-page`) and the action class from `MVPDetailView` (`mvp-detail-page`).
3. **Given** an `MVPDetailView` subclass with `has_list_permission = True` and a matching list URL, **When** the page renders, **Then** the breadcrumbs are: list view link → current object name (no link).
4. **Given** no custom `template_name` is set, **When** the view renders, **Then** it tries the app-specific template first (e.g. `myapp/order_detail.html`) and falls back to the shared `detail_view.html` base template.

---

### User Story 3 - Customise the Breadcrumb Back-Link Without Overriding Get Breadcrumbs (Priority: P2) [Developer]

As a developer whose list view has a title different from the model's plural verbose name, I want to set a single class attribute on my concrete view to change the breadcrumb back-link text, without overriding the entire breadcrumb method.

**Audience**: Developer (integrator)
**Why this priority**: Breadcrumb text customisation is a near-universal need in real projects. Exposing it as a simple attribute means developers are not forced to override a method and risk losing future enhancements to the breadcrumb logic.
**Independent Test**: A concrete view sets `list_view_title = "Active Orders"`. The rendered breadcrumb trail's first item reads "Active Orders" with the correct list URL. No method override is required.

**Acceptance Scenarios**:

1. **Given** `list_view_title = "Active Orders"` is set on a view, **When** the page renders, **Then** the first breadcrumb reads "Active Orders".
2. **Given** `list_view_title` is not set, **When** the page renders, **Then** the first breadcrumb reads the model's plural verbose name, title-cased.
3. **Given** `list_view_title` is set and `has_list_permission = False`, **When** the page renders, **Then** the first breadcrumb still reads the custom title but carries no `href`.

---

### User Story 4 - See a Consistent, Object-Named Page Heading on Every Detail Page (Priority: P1) [End User]

As an end user viewing a record's detail page, I see the record's own name or description as the page heading, so I always know exactly which record I am looking at — regardless of which model or application I am navigating.

**Audience**: End User
**Why this priority**: Users orient themselves on a detail page by its title. A title drawn from the record itself is the clearest possible signal that the right record is displayed. Inconsistent or missing titles lead to navigation errors and lost confidence.
**Independent Test**: A detail page for a model whose `__str__` returns `"Order #42"` renders a visible heading reading "Order #42". A second model whose `__str__` returns `"Alice Johnson"` renders its heading as "Alice Johnson". No heading is blank or shows a raw identifier.

**Acceptance Scenarios**:

1. **Given** a detail page is requested for a model instance, **When** the page renders, **Then** the visible page heading matches the string representation of that specific instance.
2. **Given** a model's `__str__` returns a localised or unicode string, **When** the page renders, **Then** the heading displays that string without corruption or truncation.
3. **Given** breadcrumbs are enabled with a list back-link, **When** the page renders, **Then** the breadcrumb trail ends with the same text as the page heading.

---

### Edge Cases

- What happens when `str(object)` returns an empty string? The page title and final breadcrumb item are both empty strings — no fallback is substituted; the developer is expected to ensure `__str__` returns a non-empty value.
- What happens when `MVPDetailView` is used without any model configuration? The `ModelInfoMixin` resolution chain raises a clear configuration error before the page renders, identifying the view class by name.
- What happens when both a model-specific template and the base fallback template are absent? Django's template engine raises its standard `TemplateDoesNotExist` error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The framework MUST provide a single composable base (`PageObjectMixin`) that merges model resolution, sibling URL directory, and page header/breadcrumb concerns. Concrete views for create, update, and delete are out of scope for this spec.
- **FR-002**: `PageObjectMixin` MUST expose a `list_view_title` class attribute that controls the text of the breadcrumb back-link to the list view; when not set, the breadcrumb text MUST default to the model's plural verbose name, title-cased.
- **FR-004**: `PageObjectMixin.get_breadcrumbs()` MUST return a two-item trail: a link to the list view (using `get_list_title()` and `resolve_crud_url("list")`) followed by the current page title (no link).
- **FR-005**: `PageObjectMixin.get_page_class()` MUST append a CSS class derived from the model name (e.g. `order-page`) to the page container class string inherited from `PageMixin`. This class is shared by all concrete views that inherit `PageObjectMixin`; each concrete view is responsible only for adding its own action-specific class (see FR-009).
- **FR-006**: The framework MUST provide a concrete `MVPDetailView` class that combines the shared base with Django's built-in single-object retrieval so that a developer only needs to set `model` (or `queryset`) to get a working read-only page.
- **FR-007**: `MVPDetailView.get_page_title()` MUST return the string representation of the resolved object (`str(self.object)`).
- **FR-008**: `MVPDetailView` MUST attempt to load an app-and-model-specific template first and fall back to the shared `detail_view.html` base template when none is found.
- **FR-009**: `MVPDetailView` MUST apply the action-specific CSS class `mvp-detail-page` to the page container. The model-derived class (e.g. `order-page`) is already provided by `PageObjectMixin`; `MVPDetailView` must not duplicate that responsibility.

### Key Entities

- **PageObjectMixin**: The shared composition base for all object-level views. Combines model resolution, CRUD URL directory, and page header/breadcrumb machinery. Concrete views (detail, create, update, delete) inherit from this and declare only what makes them different.
- **MVPDetailView**: The simplest concrete object-level view. Read-only; derives its page title from the displayed object's string representation; uses the shared breadcrumb trail and CSS class conventions from `PageObjectMixin`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can produce a working, titled, breadcrumbed detail page by inheriting `MVPDetailView` and setting a single `model` attribute — verified by the automated test suite: `ProductDetailView` in the demo app sets only `model` and requires no method overrides, confirming the zero-configuration guarantee.
- **SC-002**: `PageObjectMixin` provides `get_breadcrumbs()` and `get_page_class()` as single, non-duplicated implementations that `MVPDetailView` inherits directly — verified by confirming no override of either method appears in `MVPDetailView`.
- **SC-003**: Every detail page rendered by `MVPDetailView` displays a page heading that exactly matches `str(object)` — verified by automated acceptance tests covering at least three distinct models.
- **SC-004**: Replacing the breadcrumb back-link text requires setting one class attribute and zero method overrides — verified by reviewing the minimal code needed for this customisation.
