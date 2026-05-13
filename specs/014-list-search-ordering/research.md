# Research: List Search and Ordering Mixins

**Phase**: 0 — Pre-design research
**Feature**: [spec.md](spec.md)
**Date**: 2026-05-06

---

## 1. OrderEntry Data Structure (FR-006a)

**Decision**: Three-tuple `(public_key, label, orm_expression)`

**Rationale**: The spec requires that the value matched by `?o=` (the public key) is an arbitrary developer-chosen string that need not match the underlying ORM field name. A three-tuple separates these concerns explicitly:

- `public_key` (str): Matched against `?o=` query parameter. Developer-chosen; never required to equal a DB column name.
- `label` (str): Human-readable description shown in the UI.
- `orm_expression` (str): ORM field name passed to `queryset.order_by()`. May have a leading `-` for descending order. Never exposed in the URL.

**Alternatives considered**:

- *Two-tuple `(value, label)`* (current implementation): `value` serves as both the public key and the ORM expression. This directly exposes DB column names in `?o=`. Rejected per FR-006a.
- *Dict `{'key': ..., 'label': ..., 'field': ...}`*: More readable but more verbose to declare and iterate. Three-tuple is idiomatic for ordered lookup tables in Python.
- *Backward-compat shim* (detect two-tuple vs three-tuple at runtime): Adds branching complexity, makes docstrings harder to write clearly, and obscures the security guarantee. Rejected. Since the package is alpha (v0.1.1), a clean breaking change is acceptable.

**Impact**: The existing demo `order_by` declarations use two-tuples and must be migrated to three-tuples in the same PR.

---

## 2. Evaluation Order: Ordering-First, Then Search (FR-012 clarification)

**Decision**: The `SearchOrderMixin(SearchMixin, OrderMixin)` MRO already guarantees the required order. No additional code is needed.

**Rationale**: Python's cooperative `super()` chain for `SearchOrderMixin(SearchMixin, OrderMixin, …)` produces this call sequence:

```
SearchMixin.get_queryset()          # called first by Django dispatch
  → calls super().get_queryset()
    → OrderMixin.get_queryset()     # called second
        → calls super().get_queryset()
          → ListView.get_queryset() # base queryset
        ← applies ordering          # ordering applied to base queryset
    ← (ordered queryset returned)
  ← applies search + distinct       # search+distinct applied on top of ordered queryset
← (filtered + ordered queryset returned)
```

This satisfies the spec requirement: ordering is applied first (to the base queryset), and `distinct()` is applied last. The PostgreSQL DISTINCT + ORDER BY conflict is therefore avoided.

**Alternatives considered**:

- Reverse MRO `SearchOrderMixin(OrderMixin, SearchMixin)`: Would apply search+distinct first, then try to re-order the already-distinct queryset. This triggers the PostgreSQL error for JOIN-based search fields. Rejected.

---

## 3. django_filters Integration (FR-011)

**Decision**: The required integration is achieved purely through MRO convention: `class MyView(SearchOrderMixin, FilterView)`. No special-case code is needed in the mixins.

**Rationale**: With `class MyView(SearchOrderMixin, FilterView)`:

```
SearchMixin.get_queryset()
  → OrderMixin.get_queryset()
      → FilterView.get_queryset()   ← returns filterset-filtered queryset
    ← applies ordering on filtered queryset
  ← applies search+distinct on ordered+filtered queryset
```

`FilterView.get_queryset()` reads `self.filterset` and returns the filtered queryset. The search and ordering mixins operate on that result via `super().get_queryset()`. No mixin resets or replaces the filtered queryset.

**The convention must be documented** in class docstrings and the quickstart as a required pattern. Reversing the order (`class MyView(FilterView, SearchOrderMixin)`) silently bypasses search and ordering.

---

## 4. `is_searchable` / `search_query` Context Sentinels (FR-003 / FR-004)

**Decision**: Always inject `is_searchable` and `search_query` regardless of whether `search_fields` is configured.

**Implementation**: The existing `SearchMixin.get_context_data()` already does this unconditionally:

```python
context["search_query"] = self.request.GET.get("q", "")
context["is_searchable"] = bool(self.search_fields)
```

No code change is needed for this requirement; only the docstring needs updating to document this guarantee.

---

## 5. OrderMixin Context When Unconfigured (FR-008)

**Decision**: When `order_by` is `None` or empty, `order_by_choices` and `current_ordering` are NOT injected into context. This contrasts with `SearchMixin` (which always injects sentinels) because there is no equivalent "is_orderable" sentinel requirement in the spec.

**Rationale**: The spec explicitly states only search sentinels must always be present (FR-004 clarification). The spec is silent on ordering sentinels, and templates conditionally rendering ordering controls can check `{% if order_by_choices %}`. Injecting empty sentinels for ordering adds no template-usability benefit since templates must branch on whether choices exist regardless.

---

## 6. Backward Compatibility

**Decision**: The three-tuple `order_by` format is a **breaking change** to the `OrderMixin` public API. The change is acceptable because:

1. The package is alpha (`v0.1.1`) with no stable API guarantees.
2. The existing two-tuple format violates the security requirement (FR-006a) and must be replaced.
3. The only existing usage of `order_by` is in `demo/views.py`, which is internal to this repository.

**Migration**: All `order_by` declarations in `demo/views.py` must be updated to three-tuples in the same PR. The quickstart.md must show only the three-tuple format.

---

## 7. No New Dependencies

**Decision**: No new dependencies are required. `django_filters` remains an optional dev dependency (`DEP004` in `pyproject.toml`). All mixin code works identically whether or not `django_filters` is installed. The `MVPFilteredListView` conditional import already handles the optional case.
