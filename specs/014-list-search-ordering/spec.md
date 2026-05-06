# Feature Specification: List Search and Ordering Mixins

**Feature Branch**: `014-list-search-ordering`  
**Created**: 2026-05-06  
**Status**: Draft  
**Input**: User description: "Any list view in this package should be able to offer ?q= text search across a set of declared fields with a single attribute. The search should behave the way users expect from Django admin: multi-word queries match records that contain any of the words in any of the configured fields. When no search fields are configured, the mixin should be a complete no-op — it should not filter anything or add unnecessary context. Additionally, any list view should be able to offer ?o= column ordering from a declared list of permitted options. The permitted-options design is intentional — it prevents users from passing arbitrary database field names as query parameters, which can expose column names or allow exploitation of database-level quirks. This spec defines how ordering is applied, how it is communicated back to the template, and what happens when an unrecognised ordering value is submitted. Finally, this spec defines a combined mixin for easily adding both search and ordering functionality to any views. Both functionalities MUST integrate with django_filters if present."

## Clarifications

### Session 2026-05-06

- Q: When search (with `distinct()`) and ordering are both active, which is applied first? → A: Ordering is applied first on the base queryset; search filtering and `distinct()` are applied on top. The MRO chain must guarantee this order.
- Q: Should `is_searchable` and `search_query` be injected into context even when `search_fields` is unconfigured? → A: Yes — always inject `is_searchable = False` and `search_query = ""` as safe defaults so templates never need presence guards.
- Q: When composing with `django_filters`, what MRO order is required? → A: `SearchMixin`/`OrderMixin` must appear left of `FilterView` in the class definition so that `super().get_queryset()` resolves to `FilterView.get_queryset()`, returning the already-filtered queryset. The spec documents this as the required convention.
- Q: Should `order_by` whitelist entries support multi-column ORM expressions? → A: No — single-string ORM field expressions only. Multi-column ordering is out of scope and deferred to a future spec.
- Q: Should developers be able to declare ordering options using keys that do not expose database column names in the `?o=` query parameter? → A: Yes — `OrderMixin` MUST support opaque key aliases so that the URL parameter value never leaks internal field names. The planning agent determines the appropriate data structure.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Text Search on a List View (Priority: P1)

A developer adds `search_fields = ['name', 'description']` to their list view. Users visiting the page can type into a search box that submits `?q=…` in the URL. Results are filtered so that any record containing at least one of the search words in at least one of the declared fields is shown. The search is case-insensitive. When the search box is cleared (or never filled in), the full unfiltered list is shown.

**Why this priority**: Search is the most fundamental discovery tool on a list page. Without it, every other capability depends on users scrolling through potentially large result sets.

**Independent Test**: Configure a view with `search_fields = ['name']` and populate the model with three records. Verify that `?q=foo` returns only records whose `name` contains "foo", and that a blank query returns all three.

**Acceptance Scenarios**:

1. **Given** a list view with `search_fields = ['name', 'description']` and several records, **When** the user visits `?q=hello`, **Then** only records where `name` or `description` contains "hello" (case-insensitive) are shown.
2. **Given** the same view, **When** the user visits `?q=hello world`, **Then** records matching "hello" OR "world" in any configured field are shown.
3. **Given** the same view, **When** the user visits with no `q` parameter, **Then** all records are returned unfiltered.
4. **Given** a list view with `search_fields = None` (or not set), **When** the user visits `?q=hello`, **Then** no filtering is applied and all records are returned.
5. **Given** a search result page, **When** the page is rendered, **Then** the current search term is available in the template context so the search input can be pre-populated.

---

### User Story 2 — Safe Column Ordering on a List View (Priority: P1)

A developer declares a permitted list of orderings: `order_by = [('name', 'Name A–Z'), ('-name', 'Name Z–A'), ('-created', 'Newest First')]`. Users can select an ordering from a UI control that submits `?o=…`. Only values from the declared list are accepted; any unrecognised value is silently ignored and the default queryset ordering is preserved. The template receives enough context to render the active ordering state and a list of available options.

**Why this priority**: Ordering is equally fundamental to search for long lists, and the security constraint (whitelist-only) is a hard requirement that must be specified before implementation.

**Independent Test**: Configure a view with three ordering options and visit each valid `?o=` value. Verify each changes the displayed record order. Then visit with an invalid `?o=hack` value and verify the order is the model's default.

**Acceptance Scenarios**:

1. **Given** a list view with `order_by` configured, **When** the user visits `?o=name`, **Then** results are ordered ascending by name.
2. **Given** the same view, **When** the user visits `?o=-name`, **Then** results are ordered descending by name.
3. **Given** the same view, **When** the user visits `?o=arbitrary_field` (not in the whitelist), **Then** no ordering override is applied; the queryset uses its default ordering.
4. **Given** a list view with `order_by = None` (or not set), **When** the user visits `?o=name`, **Then** no ordering override is applied and no ordering-related context is added.
5. **Given** a list view with valid ordering configured, **When** the page is rendered, **Then** the template receives the list of ordering choices and the currently active ordering value so a UI control can show the selected state.

---

### User Story 3 — Combined Search and Ordering (Priority: P2)

A developer uses a single `SearchOrderMixin` to enable both `?q=` search and `?o=` ordering on one view. Both features work independently and together: a user can search and then order the filtered results.

**Why this priority**: The combined mixin removes boilerplate for the common case but is a composition of the two P1 stories. It delivers value only once P1 is stable.

**Independent Test**: Configure a view with both `search_fields` and `order_by`. Submit `?q=foo&o=-name` and verify that results are both filtered to "foo" matches and ordered newest-to-oldest.

**Acceptance Scenarios**:

1. **Given** a view using `SearchOrderMixin` with both attributes set, **When** the user visits `?q=foo&o=-name`, **Then** results are filtered to those matching "foo" and are ordered by name descending.
2. **Given** the same view, **When** only `?q=foo` is supplied, **Then** results are filtered but retain default ordering.
3. **Given** the same view, **When** only `?o=name` is supplied, **Then** all results are shown in ascending name order.

---

### User Story 4 — django_filters Integration (Priority: P2)

When a list view already uses `django_filters` (via `FilterView` or a `filterset_class`), the `SearchMixin` and `OrderMixin` must compose cleanly with the filtered queryset. Search and ordering are applied on top of whatever queryset the `django_filters` filterset produces — they do not bypass or reset it.

**Why this priority**: Projects that adopt `django_filters` for complex filtering must be able to layer search and ordering on top without conflict or double-application.

**Independent Test**: Configure a view as `class MyView(SearchOrderMixin, FilterView)` with a `filterset_class` that filters by category, and add `search_fields` and `order_by`. Verify that `?category=books&q=python&o=name` returns records in the "books" category whose name or description contains "python", ordered by name. Also verify that reversing the MRO (placing `FilterView` before `SearchOrderMixin`) is documented as unsupported.

**Acceptance Scenarios**:

1. **Given** a view using `django_filters` and `SearchOrderMixin`, **When** both `?q=` and a filterset parameter are present, **Then** only records matching both the filterset and the search term are returned.
2. **Given** the same view with an active filterset filter, **When** `?o=` is also supplied, **Then** the filtered results are ordered without losing the filterset constraint.
3. **Given** a view using `django_filters` but with no `search_fields` configured, **When** `?q=` is present, **Then** only the filterset is applied and search is a no-op.

---

### Edge Cases

- What happens when `?q=` is present but contains only whitespace? The query should be treated as empty (stripped to nothing) and no filtering applied.
- What happens when a declared `search_fields` entry references a related model field (e.g., `'category__name'`)? The search should traverse the relationship using standard ORM lookups.
- What happens when the same word matches multiple fields for the same record? The record should appear exactly once in results (deduplication via `distinct()`).
- What happens when `?o=` is present but `order_by` is an empty list (`[]`)? No ordering is applied (treated the same as `None`).
- What happens when both `?q=` and `?o=` are submitted with invalid values? Both are silently ignored; the full unfiltered, default-ordered queryset is returned.
- When both search and ordering are active simultaneously, ordering is applied to the base queryset first, and search filtering (including `distinct()`) is applied on top. This order is required to avoid database errors on PostgreSQL when a JOIN-based search field conflicts with the ORDER BY clause.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `SearchMixin` MUST read the `?q` query parameter and apply case-insensitive substring matching across all fields declared in `search_fields`.
- **FR-002**: Multi-word `?q` values MUST be split on whitespace; a record matches if it contains ANY of the words in ANY of the declared fields (OR semantics across both words and fields).
- **FR-003**: When `search_fields` is `None` or empty, `SearchMixin` MUST NOT modify the queryset, but MUST still inject `is_searchable = False` and `search_query = ""` into the template context as safe defaults.
- **FR-004**: `SearchMixin` MUST always inject `is_searchable` (a boolean reflecting whether `search_fields` is configured) and `search_query` (the current `?q` value stripped, or `""`) into the template context — regardless of configuration state.
- **FR-005**: `SearchMixin` MUST call `super().get_queryset()` and operate on its result, preserving any prior queryset transformations (including `django_filters` output).
- **FR-006**: `OrderMixin` MUST read the `?o` query parameter and apply ordering only when the value is present in the declared `order_by` whitelist.
- **FR-006a**: `OrderMixin` MUST support opaque ordering keys — the value matched by `?o=` MUST be an arbitrary developer-chosen string that need not match the underlying ORM field name. This prevents database column names from being exposed in URLs. The planning agent is responsible for determining the appropriate data structure (e.g., three-tuple, dict, or named mapping) that separates the public key from the private ORM expression.
- **FR-007**: When the `?o` value is not in the whitelist (or is absent), `OrderMixin` MUST NOT modify the queryset ordering.
- **FR-008**: When `order_by` is `None` or empty, `OrderMixin` MUST NOT modify the queryset or add any ordering-related keys to the template context.
- **FR-009**: `OrderMixin` MUST add `order_by_choices` (the full list of permitted options) and `current_ordering` (the active `?o` value) to the template context when `order_by` is configured.
- **FR-010**: `SearchOrderMixin` MUST combine `SearchMixin` and `OrderMixin` so that both `?q` and `?o` parameters are processed in a single mixin.
- **FR-011**: Both `SearchMixin` and `OrderMixin` MUST compose correctly when the base queryset is produced by a `django_filters` `FilterView` — neither mixin resets or replaces the filtered queryset. The required MRO convention is `class MyView(SearchOrderMixin, FilterView)` (search/order mixins left of `FilterView`), so that `super().get_queryset()` inside the mixins resolves to `FilterView.get_queryset()` and receives the already-filtered queryset. This convention MUST be documented in the class docstrings and quickstart.
- **FR-012**: Search results containing records that match via multiple fields MUST be deduplicated (appear only once). When ordering is also active, ordering MUST be applied before search filtering and `distinct()` to remain safe on PostgreSQL JOIN + ORDER BY combinations.
- **FR-013**: `search_fields` values MUST support ORM relationship traversal syntax (e.g., `'category__name'`).

### Key Entities

- **SearchMixin**: A Django view mixin that adds `?q=` text search capability. Configured via `search_fields` (list of ORM field paths). No-op when unconfigured.
- **OrderMixin**: A Django view mixin that adds `?o=` ordering capability. Configured via `order_by` (list of `(value, label)` tuples). Only permitted values are accepted; others are silently ignored.
- **SearchOrderMixin**: A convenience mixin that combines `SearchMixin` and `OrderMixin` for views needing both capabilities.
- **Ordering whitelist entry**: A configuration entry declaring one permitted ordering option. It MUST associate three things: a public key (the value matched by `?o=`, chosen freely by the developer and never required to match a column name), a display label (shown in the UI), and the private ORM sort expression applied to the queryset. The exact data structure is determined during planning.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can add full-text search to any list view by setting a single class attribute (`search_fields`), with zero additional code.
- **SC-002**: A developer can add safe column ordering to any list view by setting a single class attribute (`order_by`), with zero additional code.
- **SC-003**: An unrecognised `?o=` value never causes an error, never exposes internal field names, and never changes the displayed result set compared to the default ordering.
- **SC-007**: The `?o=` query parameter value is always a developer-chosen opaque string. At no point does the mixin apply an ORM expression that was not explicitly declared in the `order_by` configuration — including indirect exposure of column names through default parameter echo.
- **SC-004**: A list view with neither `search_fields` nor `order_by` set produces exactly the same queryset as a plain `ListView`. The only additional context keys are `is_searchable = False` and `search_query = ""`, which are always injected as safe sentinel defaults.
- **SC-005**: Search and ordering compose correctly with `django_filters` — the active filterset constraints are preserved when `?q=` and `?o=` are also present.
- **SC-006**: Multi-word search queries return a superset of single-word results for each individual word, and no record appears more than once in results.

## Assumptions

- The `?q` and `?o` query parameters are read-only; the mixins never write to them or redirect to normalise them.
- Search matching uses case-insensitive substring (`icontains`) lookup — no stemming, tokenisation, or full-text indexing is required.
- Ordering direction (ascending/descending) is encoded entirely in the `order_by` whitelist values (e.g., `-name` for descending); there is no separate direction parameter.
- When `django_filters` is not installed, the mixins operate identically — there is no conditional import failure.
- Multi-column ORM ordering (e.g., sorting by a primary and secondary field simultaneously from a single `?o=` selection) is out of scope and deferred to a future spec. Each whitelist entry maps to exactly one ORM sort expression (single field, with optional `-` prefix).
- The exact data structure for `order_by` whitelist entries (separating public key, display label, and ORM expression) is a planning decision. The spec requires the three concerns to be expressible; it does not prescribe a two-tuple, three-tuple, or dict.
- The `SearchOrderMixin` resolves MRO conflicts between `SearchMixin` and `OrderMixin` by inheriting both and relying on Python's cooperative `super()` chain.
- Template rendering of search inputs and ordering dropdowns is the responsibility of the view templates, not the mixins; the mixins only inject the necessary context variables.
