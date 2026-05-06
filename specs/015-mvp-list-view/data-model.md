# Data Model: MVPListView — Item Templates and Composed List Page

**Feature**: `015-mvp-list-view` | **Date**: 2026-05-06 | **Phase**: 1

No new Django models or database migrations are introduced by this feature.

---

## Configuration Attributes (Class-Level API)

The following attributes are defined on `MVPListViewMixin` and `MVPListView` and constitute
the developer-facing configuration surface.

### `MVPListViewMixin`

| Attribute | Type | Default | Description |
|---|---|---|---|
| `base_template_name` | `str` | `"list_view.html"` | Fallback base template (from `BaseTemplateNameMixin`). Set at class level; not overridden by developers. |
| `list_item_template` | `str \| None` | `None` | Explicit partial template path for each list item. When falsy, auto-discovery applies. |
| `grid` | `dict` | `{}` | Grid configuration dict passed unchanged to context as `grid_config`. Schema defined by consuming Cotton component. |
| `empty_state_heading` | `str \| None` | `_("There's nothing here yet")` | Heading for the zero-results state. Set to `None` to suppress. |
| `empty_state_message` | `str \| None` | `_("You haven't added any records yet…")` | Body text for the zero-results state. Set to `None` to suppress. |
| `directory` | `list[str]` | `["create"]` | Inherited from `CRUDDirectoryMixin`. **Set to `["create"]` on this mixin** — limits CRUD URL injection to the create action only. |
| `search_fields` | `list[str] \| None` | `None` | Inherited from `SearchMixin`. Field paths for `?q=` text search. |
| `order_by` | `list[tuple] \| None` | `None` | Inherited from `OrderMixin`. Three-tuple whitelist for `?o=` ordering. |

### `MVPListView` (concrete class)

| Attribute | Type | Default | Description |
|---|---|---|---|
| `paginate_by` | `int` | `24` | Page size. 24 is grid-friendly (divisible by 1, 2, 3, 4). Inherited by Django's `ListView`. Override to any positive integer. |

---

## Context Variables

The following context keys are injected by `MVPListViewMixin.get_context_data()` and
the mixins it composes. All keys are always present.

| Key | Type | Source | Description |
|---|---|---|---|
| `list_item_template` | `str` | `MVPListViewMixin.get_list_item_template()` | Path to the item partial. Either explicit (`list_item_template`) or derived (`<app_label>/<model_name>_list_item.html`). |
| `empty_state` | `dict` | `MVPListViewMixin.get_context_data()` | Dict with `heading` (`str \| None`) and `message` (`str \| None`). Always present; heading/message may be `None`. |
| `grid_config` | `dict` | `MVPListViewMixin.get_grid_config()` | Passthrough of `grid` attribute. May be empty dict. |
| `directory` | `dict` | `CRUDDirectoryMixin.get_directory()` | Resolved CRUD URLs. For list views: only `create_url` is eligible. Dict is empty when `has_create_permission` is falsy. |
| `page` | `dict` | `PageMixin.get_page_context()` | Page metadata: `title`, `subtitle`, `icon`, `class`, `breadcrumbs`. `title` defaults to `verbose_name_plural.title()`. |
| `search_query` | `str` | `SearchMixin.get_context_data()` | Raw `?q=` value or `""`. Always present. |
| `is_searchable` | `bool` | `SearchMixin.get_context_data()` | `True` when `search_fields` is configured. Always present. |
| `order_by_choices` | `list[tuple]` | `OrderMixin.get_context_data()` | Full three-tuple ordering whitelist. Present only when `order_by` is configured. |
| `current_ordering` | `str` | `OrderMixin.get_context_data()` | Matched `public_key` for active `?o=`, or `""`. Present only when `order_by` is configured. |

---

## Override Hooks

| Method | Defined on | Returns | Purpose |
|---|---|---|---|
| `get_list_item_template()` | `MVPListViewMixin` | `str` | Return item partial path. Override for custom resolution logic. |
| `get_page_title()` | `MVPListViewMixin` | `str` | Return page title. Checks `page_title` first; falls back to `verbose_name_plural.title()`. |
| `get_breadcrumbs()` | `MVPListViewMixin` | `list[dict]` | Return breadcrumb trail. Default: Home → page title. |
| `get_empty_state_heading()` | `MVPListViewMixin` | `str \| None` | Return empty state heading. |
| `get_empty_state_message()` | `MVPListViewMixin` | `str \| None` | Return empty state body text. |
| `get_grid_config()` | `MVPListViewMixin` | `dict` | Return grid config dict. |
| `get_search_fields()` | `SearchMixin` | `list[str] \| None` | Return search fields dynamically. |
| `get_order_by_choices()` | `OrderMixin` | `list[tuple] \| None` | Return ordering whitelist dynamically. |

---

## Item Template Convention

```
<app_label>/<model_name>_list_item.html
```

Examples:

| Model | App | Resolved path |
|---|---|---|
| `Product` | `shop` | `shop/product_list_item.html` |
| `Order` | `sales` | `sales/order_list_item.html` |
| `Category` | `demo` | `demo/category_list_item.html` |

Django normalises `app_label` and `model_name` to lowercase underscores via `model._meta`.
No special handling is required for apps with hyphens or unusual capitalisation.
