# Data Model: List Search and Ordering Mixins

**Phase**: 1 — Design
**Feature**: [spec.md](spec.md)
**Date**: 2026-05-06

---

## Overview

This feature introduces no Django models, migrations, or database schema changes. The "data model" described here is the in-memory configuration data structure used by `OrderMixin` to declare its whitelist of permitted ordering options.

---

## OrderEntry (Configuration Tuple)

An `OrderEntry` is a three-element tuple that declares one permitted ordering option on a list view.

```
(public_key: str, label: str, orm_expression: str)
```

| Position | Name | Type | Description |
|---|---|---|---|
| 0 | `public_key` | `str` | The value matched against the `?o=` query parameter. Developer-chosen; MUST NOT be required to match a DB column name. |
| 1 | `label` | `str` | Human-readable display name shown in the ordering UI (e.g., a `<select>` option). |
| 2 | `orm_expression` | `str` | ORM field name passed directly to `queryset.order_by()`. May be prefixed with `-` for descending order. NEVER exposed in the URL. |

### Validation rules

- `public_key` must be a non-empty string. No whitespace restriction is enforced at runtime; however, URL-safe values are strongly recommended.
- `label` is used for display only; no uniqueness or format constraints are enforced.
- `orm_expression` is passed unmodified to `queryset.order_by()`. The developer is responsible for ensuring it is a valid ORM field path for the queryset's model.
- Single-field ORM expressions only. Multi-column expressions (e.g., tuples or multiple positional arguments to `order_by()`) are out of scope and deferred.

### Example declarations

```python
order_by = [
    ("name_asc",   "Name (A–Z)",            "name"),
    ("name_desc",  "Name (Z–A)",            "-name"),
    ("price_asc",  "Price (Low to High)",   "price"),
    ("price_desc", "Price (High to Low)",   "-price"),
    ("newest",     "Newest First",          "-created_at"),
]
```

In this example, `?o=newest` causes `queryset.order_by("-created_at")` to be applied. The string `"created_at"` is never visible in the URL.

---

## Context Variables Produced by the Mixins

### SearchMixin

These context variables are **always injected** regardless of `search_fields` configuration:

| Key | Type | Description |
|---|---|---|
| `search_query` | `str` | The current `?q` value, stripped of leading/trailing whitespace. Empty string when absent or whitespace-only. |
| `is_searchable` | `bool` | `True` when `search_fields` is configured (non-empty); `False` otherwise. |

### OrderMixin

These context variables are injected **only when `order_by` is configured** (non-`None`, non-empty):

| Key | Type | Description |
|---|---|---|
| `order_by_choices` | `list[tuple[str, str, str]]` | The full list of `OrderEntry` three-tuples as declared on the view. Templates iterate over this to build ordering UI controls. |
| `current_ordering` | `str` | The `public_key` matching the current `?o=` value. Empty string when `?o=` is absent or unrecognised. |

---

## MRO Invariant

The `SearchOrderMixin(SearchMixin, OrderMixin)` inheritance order is a documented invariant — it is not configurable:

```
SearchMixin → OrderMixin → (base view class)
```

Evaluation sequence (from deepest super call outward):

1. Base view (e.g., `ListView` or `FilterView`) returns the base queryset.
2. `OrderMixin.get_queryset()` applies ordering (if configured and `?o=` is valid).
3. `SearchMixin.get_queryset()` applies search filter and `distinct()` (if configured and `?q=` is non-empty).

This order ensures that `distinct()` is applied last, avoiding the PostgreSQL `SELECT DISTINCT` + `ORDER BY` conflict when the ordering field involves a JOIN.
