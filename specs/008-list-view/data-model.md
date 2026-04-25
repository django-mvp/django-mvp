# Data Model: Dashboard List View Mixin

**Feature**: 008-dash-list-view
**Date**: February 4, 2026

## Mixin Class Hierarchy

```text
                    ┌─────────────────┐
                    │   SearchMixin   │
                    │                 │
                    │ search_fields   │
                    │ get_search_fields() │
                    │ _apply_search() │
                    └────────┬────────┘
                             │
         ┌───────────────────┴───────────────────┐
         │                                       │
         ▼                                       ▼
┌─────────────────┐                   ┌─────────────────────┐
│   OrderMixin    │                   │ ListItemTemplateMixin│
│                 │                   │                     │
│ order_by        │                   │ list_item_template  │
│ get_order_by_choices() │            │ get_list_item_template() │
│ _apply_ordering()│                  │                     │
└────────┬────────┘                   └──────────┬──────────┘
         │                                       │
         ▼                                       │
┌─────────────────────┐                          │
│ SearchOrderMixin    │                          │
│ (SearchMixin +      │                          │
│  OrderMixin)        │                          │
└────────┬────────────┘                          │
         │                                       │
         └───────────────────┬───────────────────┘
                             │
                             ▼
                   ┌─────────────────────┐
                   │  MVPListViewMixin   │
                   │                     │
                   │ grid                │
                   │ page_title          │
                   │ get_grid_config()   │
                   │ get_page_title()    │
                   └─────────────────────┘
```

## Entity Definitions

### SearchMixin

**Purpose**: Adds search functionality to list views

**Attributes**:

| Attribute       | Type           | Default | Description                           |
| --------------- | -------------- | ------- | ------------------------------------- |
| `search_fields` | `list[str]`    | `None`  | Model fields to search across         |

**Methods**:

| Method               | Returns          | Description                              |
| -------------------- | ---------------- | ---------------------------------------- |
| `get_search_fields()`| `list[str]|None` | Returns search_fields (can be overridden)|
| `_apply_search()`    | `QuerySet`       | Applies OR search filter to queryset     |
| `get_queryset()`     | `QuerySet`       | Overrides to apply search filtering      |
| `get_context_data()` | `dict`           | Adds `search_query`, `is_searchable`     |

**Context Variables**:

| Variable        | Type   | Description                           |
| --------------- | ------ | ------------------------------------- |
| `search_query`  | `str`  | Current search term from `?q=`        |
| `is_searchable` | `bool` | True if search_fields is defined      |

### OrderMixin

**Purpose**: Adds ordering/sorting functionality to list views

**Attributes**:

| Attribute  | Type                          | Default | Description                           |
| ---------- | ----------------------------- | ------- | ------------------------------------- |
| `order_by` | `list[tuple[str, str]]`       | `None`  | List of (field, label) tuples         |

**Methods**:

| Method                  | Returns                    | Description                              |
| ----------------------- | -------------------------- | ---------------------------------------- |
| `get_order_by_choices()`| `list[tuple]|None`         | Returns order_by (can be overridden)     |
| `_apply_ordering()`     | `QuerySet`                 | Applies ordering to queryset             |
| `get_queryset()`        | `QuerySet`                 | Overrides to apply ordering              |
| `get_context_data()`    | `dict`                     | Adds `order_by_choices`, `current_ordering`|

**Context Variables**:

| Variable            | Type                    | Description                           |
| ------------------- | ----------------------- | ------------------------------------- |
| `order_by_choices`  | `list[tuple[str, str]]` | Available ordering options            |
| `current_ordering`  | `str`                   | Current ordering from `?o=`           |

### SearchOrderMixin

**Purpose**: Combines SearchMixin and OrderMixin

**Inherits**: `SearchMixin`, `OrderMixin`

**Additional Attributes**: None

**Additional Methods**: None (inherits all from parents)

### ListItemTemplateMixin

**Purpose**: Provides list item template resolution

**Attributes**:

| Attribute            | Type   | Default | Description                           |
| -------------------- | ------ | ------- | ------------------------------------- |
| `list_item_template` | `str`  | `None`  | Path to list item template            |

**Methods**:

| Method                     | Returns | Description                              |
| -------------------------- | ------- | ---------------------------------------- |
| `get_list_item_template()` | `str`   | Returns template path (auto-generates if None)|
| `get_template_names()`     | `list`  | Adds `list_view.html` as fallback        |
| `get_context_data()`       | `dict`  | Adds `list_item_template`                |

**Context Variables**:

| Variable             | Type   | Description                           |
| -------------------- | ------ | ------------------------------------- |
| `list_item_template` | `str`  | Template path for rendering list items|

**Auto-Generation Pattern**: `{app_label}/{model_name}_list_item.html`

### MVPListViewMixin

**Purpose**: Top-level mixin combining all functionality

**Inherits**: `SearchOrderMixin`, `ListItemTemplateMixin`

**Attributes**:

| Attribute    | Type   | Default | Description                           |
| ------------ | ------ | ------- | ------------------------------------- |
| `grid`       | `dict` | `{}`    | Grid configuration for layout         |
| `page_title` | `str`  | `""`    | Page title (uses verbose_name if empty)|

**Methods**:

| Method             | Returns | Description                              |
| ------------------ | ------- | ---------------------------------------- |
| `get_grid_config()`| `dict`  | Returns grid configuration               |
| `get_page_title()` | `str`   | Returns page title (auto-generates from model)|
| `get_context_data()`| `dict` | Adds `grid_config`, `page_title`         |

**Context Variables**:

| Variable      | Type   | Description                           |
| ------------- | ------ | ------------------------------------- |
| `grid_config` | `dict` | Grid configuration dictionary         |
| `page_title`  | `str`  | Page title string                     |

## Grid Configuration Schema

The `grid` attribute is passed directly to the `c-row` Cotton component.

**Properties**:

| Property | Type  | Default | Description                              |
| -------- | ----- | ------- | ---------------------------------------- |
| `cols`   | `int` | `1`     | Default column count                     |
| `gap`    | `int` | `1`     | Gap between items (Bootstrap spacing)    |
| `xs`     | `int` | -       | Columns at xs breakpoint                 |
| `sm`     | `int` | -       | Columns at sm breakpoint (≥576px)        |
| `md`     | `int` | -       | Columns at md breakpoint (≥768px)        |
| `lg`     | `int` | -       | Columns at lg breakpoint (≥992px)        |
| `xl`     | `int` | -       | Columns at xl breakpoint (≥1200px)       |
| `xxl`    | `int` | -       | Columns at xxl breakpoint (≥1400px)      |

**Examples**:

```python
# Single column (default)
grid = {}  # or grid = {"cols": 1}

# Fixed 3 columns
grid = {"cols": 3, "gap": 2}

# Responsive: 1 on mobile, 2 on tablet, 3 on desktop
grid = {"cols": 1, "md": 2, "lg": 3}

# Fully responsive
grid = {"cols": 1, "sm": 2, "md": 3, "xl": 4, "gap": 3}
```

## Query Parameters

The mixins use URL query parameters for state management:

| Parameter | Used By      | Description                           |
| --------- | ------------ | ------------------------------------- |
| `q`       | SearchMixin  | Search query string                   |
| `o`       | OrderMixin   | Ordering field (from order_by choices)|
| `page`    | Django       | Pagination page number                |
| (various) | django-filter| Filter fields (managed by django-filter)|

## Template Context Summary

Combined context from all mixins when using MVPListViewMixin:

| Variable             | Type                    | Source                |
| -------------------- | ----------------------- | --------------------- |
| `object_list`        | `QuerySet`              | Django ListView       |
| `page_obj`           | `Page`                  | Django pagination     |
| `paginator`          | `Paginator`             | Django pagination     |
| `is_paginated`       | `bool`                  | Django pagination     |
| `search_query`       | `str`                   | SearchMixin           |
| `is_searchable`      | `bool`                  | SearchMixin           |
| `order_by_choices`   | `list[tuple]`           | OrderMixin            |
| `current_ordering`   | `str`                   | OrderMixin            |
| `list_item_template` | `str`                   | ListItemTemplateMixin |
| `grid_config`        | `dict`                  | MVPListViewMixin      |
| `page_title`         | `str`                   | MVPListViewMixin      |
| `filter`             | `FilterSet`             | django-filter (optional)|
