# API Contract: List Search and Ordering Mixins

**Phase**: 1 — Design  
**Feature**: [spec.md](../spec.md)  
**Date**: 2026-05-06

---

## SearchMixin

**Module**: `mvp.views.list`  
**Import**: `from mvp.views import SearchMixin`

### Class Attributes

| Attribute | Type | Default | Description |
|---|---|---|---|
| `search_fields` | `list[str] \| None` | `None` | ORM field paths to search across. Each entry may use relationship traversal syntax (e.g., `"category__name"`). When `None` or empty, the mixin is a complete no-op for queryset filtering. |

### Override Hooks

| Method | Return type | Description |
|---|---|---|
| `get_search_fields()` | `list[str] \| None` | Returns the effective search fields. Override to compute dynamically. |

### Context Variables (always injected)

| Variable | Type | Value when unconfigured | Value when configured |
|---|---|---|---|
| `is_searchable` | `bool` | `False` | `True` |
| `search_query` | `str` | `""` | Stripped `?q=` value, or `""` if blank/absent |

### Query Parameters Read

| Parameter | Description |
|---|---|
| `?q` | Search term. Whitespace-stripped. Split on whitespace for multi-word OR matching. |

### Behaviour

- When `search_fields` is configured and `?q=` is non-empty (after strip): builds an OR query across all fields and all words. Uses `icontains` (case-insensitive substring) matching. Applies `.distinct()` to deduplicate records that match via multiple fields.
- When `search_fields` is `None`/empty or `?q=` is blank: queryset is returned unmodified.
- Calls `super().get_queryset()` — compatible with `FilterView` when positioned left of `FilterView` in the MRO.

---

## OrderMixin

**Module**: `mvp.views.list`  
**Import**: `from mvp.views import OrderMixin`

### Class Attributes

| Attribute | Type | Default | Description |
|---|---|---|---|
| `order_by` | `list[tuple[str, str, str]] \| None` | `None` | Whitelist of permitted ordering options. Each entry is a three-tuple `(public_key, label, orm_expression)`. When `None` or empty, the mixin is a complete no-op. |

### OrderEntry Three-Tuple Format

```python
(public_key: str, label: str, orm_expression: str)
```

| Field | Description |
|---|---|
| `public_key` | Matched against `?o=`. Developer-chosen; need not match a DB column name. |
| `label` | Display string for UI controls (e.g., `<select>` options). |
| `orm_expression` | Passed to `queryset.order_by()`. May be prefixed with `-` for descending. Never URL-exposed. |

### Override Hooks

| Method | Return type | Description |
|---|---|---|
| `get_order_by_choices()` | `list[tuple[str, str, str]] \| None` | Returns the effective ordering whitelist. Override to compute dynamically. |

### Context Variables (injected only when `order_by` is configured)

| Variable | Type | Description |
|---|---|---|
| `order_by_choices` | `list[tuple[str, str, str]]` | Full whitelist as declared. Templates iterate over this list; each element is `(public_key, label, orm_expression)`. |
| `current_ordering` | `str` | The `public_key` of the active ordering, or `""` if `?o=` is absent or unrecognised. |

### Query Parameters Read

| Parameter | Description |
|---|---|
| `?o` | Ordering selection. Must match a `public_key` in the whitelist to take effect. Unrecognised values are silently ignored. |

### Behaviour

- When `order_by` is configured and `?o=` matches a `public_key`: applies `queryset.order_by(orm_expression)` where `orm_expression` is the third element of the matching tuple.
- When `order_by` is `None`/empty or `?o=` is absent/unrecognised: queryset is returned unmodified. No ordering-related context is injected.
- Calls `super().get_queryset()` — compatible with `FilterView` when the MRO places ordering mixins left of `FilterView`.

### Security Guarantee

`OrderMixin` never passes the raw `?o=` parameter value to `queryset.order_by()`. The `?o=` value is matched against the `public_key` column of the whitelist; only the corresponding `orm_expression` (a developer-declared constant) is passed to the ORM. Arbitrary or injected `?o=` values that are not in the whitelist have no effect.

---

## SearchOrderMixin

**Module**: `mvp.views.list`  
**Import**: `from mvp.views import SearchOrderMixin`

A convenience mixin that combines `SearchMixin` and `OrderMixin`. Use this as the single mixin when a view needs both capabilities.

```python
class SearchOrderMixin(SearchMixin, OrderMixin):
    pass
```

The MRO `(SearchMixin, OrderMixin)` guarantees:

1. Ordering is applied first (to the base queryset).
2. Search + `distinct()` is applied second (on the ordered queryset).

All attributes, override hooks, context variables, and query parameters of both `SearchMixin` and `OrderMixin` apply unchanged.

---

## django_filters Integration

When composing with `django_filters.views.FilterView`, the required class definition pattern is:

```python
class MyView(SearchOrderMixin, FilterView):
    ...
```

**`SearchOrderMixin` must appear LEFT of `FilterView`** in the class definition. This ensures that `super().get_queryset()` inside the ordering mixin resolves to `FilterView.get_queryset()`, which returns the filterset-filtered queryset. Search and ordering are then applied on top of the filtered result.

Reversing this order (`class MyView(FilterView, SearchOrderMixin)`) causes `FilterView.get_queryset()` to call into the mixin chain *before* the filterset is applied, producing incorrect results. This incorrect order is **not supported**.
