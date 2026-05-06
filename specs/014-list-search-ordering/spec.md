# Feature Specification: List Search and Ordering Mixins

**Feature Branch**: `014-list-search-ordering`  
**Created**: 2026-05-06  
**Status**: Draft  
**Input**: User description: "Any list view in this package should be able to offer ?q= text search across a set of declared fields with a single attribute. The search should behave the way users expect from Django admin: multi-word queries match records that contain any of the words in any of the configured fields. When no search fields are configured, the mixin should be a complete no-op — it should not filter anything or add unnecessary context. Additionally, any list view should be able to offer ?o= column ordering from a declared list of permitted options. The permitted-options design is intentional — it prevents users from passing arbitrary database field names as query parameters, which can expose column names or allow exploitation of database-level quirks. This spec defines how ordering is applied, how it is communicated back to the template, and what happens when an unrecognised ordering value is submitted. Finally, this spec defines a combined mixin for easily adding both search and ordering functionality to any views. Both functionalities MUST integrate with django_filters if present."

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

**Independent Test**: Configure an `MVPFilteredListView` with a `filterset_class` that filters by category, and add `search_fields` and `order_by`. Verify that `?category=books&q=python&o=name` returns records in the "books" category whose name or description contains "python", ordered by name.

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

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `SearchMixin` MUST read the `?q` query parameter and apply case-insensitive substring matching across all fields declared in `search_fields`.
- **FR-002**: Multi-word `?q` values MUST be split on whitespace; a record matches if it contains ANY of the words in ANY of the declared fields (OR semantics across both words and fields).
- **FR-003**: When `search_fields` is `None` or empty, `SearchMixin` MUST NOT modify the queryset or add any search-related keys to the template context.
- **FR-004**: `SearchMixin` MUST add `search_query` (the current `?q` value, stripped) and `is_searchable` (a boolean) to the template context when configured.
- **FR-005**: `SearchMixin` MUST call `super().get_queryset()` and operate on its result, preserving any prior queryset transformations (including `django_filters` output).
- **FR-006**: `OrderMixin` MUST read the `?o` query parameter and apply ordering only when the value is present in the declared `order_by` whitelist.
- **FR-007**: When the `?o` value is not in the whitelist (or is absent), `OrderMixin` MUST NOT modify the queryset ordering.
- **FR-008**: When `order_by` is `None` or empty, `OrderMixin` MUST NOT modify the queryset or add any ordering-related keys to the template context.
- **FR-009**: `OrderMixin` MUST add `order_by_choices` (the full list of permitted options) and `current_ordering` (the active `?o` value) to the template context when `order_by` is configured.
- **FR-010**: `SearchOrderMixin` MUST combine `SearchMixin` and `OrderMixin` so that both `?q` and `?o` parameters are processed in a single mixin.
- **FR-011**: Both `SearchMixin` and `OrderMixin` MUST compose correctly when the base queryset is produced by a `django_filters` `FilterView` — neither mixin resets or replaces the filtered queryset.
- **FR-012**: Search results containing records that match via multiple fields MUST be deduplicated (appear only once).
- **FR-013**: `search_fields` values MUST support ORM relationship traversal syntax (e.g., `'category__name'`).

### Key Entities

- **SearchMixin**: A Django view mixin that adds `?q=` text search capability. Configured via `search_fields` (list of ORM field paths). No-op when unconfigured.
- **OrderMixin**: A Django view mixin that adds `?o=` ordering capability. Configured via `order_by` (list of `(value, label)` tuples). Only permitted values are accepted; others are silently ignored.
- **SearchOrderMixin**: A convenience mixin that combines `SearchMixin` and `OrderMixin` for views needing both capabilities.
- **Ordering whitelist entry**: A two-tuple `(ordering_value, display_label)` where `ordering_value` is the ORM field name (optionally prefixed with `-` for descending) and `display_label` is the human-readable name shown in the UI.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can add full-text search to any list view by setting a single class attribute (`search_fields`), with zero additional code.
- **SC-002**: A developer can add safe column ordering to any list view by setting a single class attribute (`order_by`), with zero additional code.
- **SC-003**: An unrecognised `?o=` value never causes an error, never exposes internal field names, and never changes the displayed result set compared to the default ordering.
- **SC-004**: A list view with neither `search_fields` nor `order_by` set produces exactly the same queryset and context as a plain `ListView` — the mixins are true no-ops.
- **SC-005**: Search and ordering compose correctly with `django_filters` — the active filterset constraints are preserved when `?q=` and `?o=` are also present.
- **SC-006**: Multi-word search queries return a superset of single-word results for each individual word, and no record appears more than once in results.

## Assumptions

- The `?q` and `?o` query parameters are read-only; the mixins never write to them or redirect to normalise them.
- Search matching uses case-insensitive substring (`icontains`) lookup — no stemming, tokenisation, or full-text indexing is required.
- Ordering direction (ascending/descending) is encoded entirely in the `order_by` whitelist values (e.g., `-name` for descending); there is no separate direction parameter.
- When `django_filters` is not installed, the mixins operate identically — there is no conditional import failure.
- The `order_by` whitelist entries are `(value, label)` two-tuples; no multi-level ordering tuple is required in this feature.
- The `SearchOrderMixin` resolves MRO conflicts between `SearchMixin` and `OrderMixin` by inheriting both and relying on Python's cooperative `super()` chain.
- Template rendering of search inputs and ordering dropdowns is the responsibility of the view templates, not the mixins; the mixins only inject the necessary context variables.
