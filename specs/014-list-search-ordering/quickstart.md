# Quickstart: List Search and Ordering Mixins

**Feature**: 014 — List Search and Ordering  
**Package**: `django-mvp`

---

## Overview

Three mixins in `mvp.views` add search and ordering capabilities to any list view with a single class attribute each:

| Mixin | Query param | Attribute |
|---|---|---|
| `SearchMixin` | `?q=` | `search_fields` |
| `OrderMixin` | `?o=` | `order_by` |
| `SearchOrderMixin` | Both | Both |

All three are included automatically in `MVPListView` and `MVPListViewMixin`.

---

## 1. Adding Text Search

Set `search_fields` to a list of ORM field paths:

```python
from django.views.generic import ListView
from mvp.views import SearchMixin

class ProductListView(SearchMixin, ListView):
    model = Product
    search_fields = ["name", "description", "category__name"]
```

- `?q=django` — returns records where `name`, `description`, or `category__name` contains "django" (case-insensitive).
- `?q=django python` — returns records matching "django" **or** "python" in any configured field.
- No `?q=` or blank `?q=` — returns all records unfiltered.
- `search_fields` not set — mixin is a **complete no-op**; the queryset is unchanged.

### Template context

Always available, regardless of configuration:

```html
{% if is_searchable %}
  <form method="get">
    <input name="q" value="{{ search_query }}" placeholder="Search…">
    <button type="submit">Search</button>
  </form>
{% endif %}
```

---

## 2. Adding Safe Column Ordering

Set `order_by` to a list of three-tuples `(public_key, label, orm_expression)`:

```python
from django.views.generic import ListView
from mvp.views import OrderMixin

class ProductListView(OrderMixin, ListView):
    model = Product
    order_by = [
        ("name_asc",   "Name (A–Z)",           "name"),
        ("name_desc",  "Name (Z–A)",           "-name"),
        ("price_asc",  "Price (Low to High)",  "price"),
        ("price_desc", "Price (High to Low)",  "-price"),
        ("newest",     "Newest First",         "-created_at"),
    ]
```

- `?o=newest` — applies `queryset.order_by("-created_at")`. The string `"created_at"` never appears in the URL.
- `?o=arbitrary_value` — silently ignored; queryset uses its default ordering.
- `order_by` not set — mixin is a **complete no-op**; no context variables are injected.

### Template context

Available when `order_by` is configured:

```html
{% if order_by_choices %}
  <select name="o" onchange="this.form.submit()">
    <option value="">Default order</option>
    {% for key, label, _ in order_by_choices %}
      <option value="{{ key }}" {% if key == current_ordering %}selected{% endif %}>
        {{ label }}
      </option>
    {% endfor %}
  </select>
{% endif %}
```

> **Security note**: `OrderMixin` never passes the raw `?o=` value to the ORM. Only the `orm_expression` declared by the developer (the third tuple element) is ever passed to `queryset.order_by()`.

---

## 3. Using Both Together

Use `SearchOrderMixin` to enable both with a single base class:

```python
from django.views.generic import ListView
from mvp.views import SearchOrderMixin

class ProductListView(SearchOrderMixin, ListView):
    model = Product
    search_fields = ["name", "description"]
    order_by = [
        ("name_asc",  "Name (A–Z)",          "name"),
        ("name_desc", "Name (Z–A)",          "-name"),
        ("newest",    "Newest First",        "-created_at"),
    ]
```

`?q=python&o=newest` returns records matching "python", ordered by `created_at` descending.

`MVPListView` and `MVPListViewMixin` already include `SearchOrderMixin`; configure `search_fields` and `order_by` directly on your subclass.

---

## 4. Composing with django_filters

When your view uses `django_filters.views.FilterView`, place `SearchOrderMixin` (or the individual mixins) **left** of `FilterView` in the class definition:

```python
from django_filters.views import FilterView
from mvp.views import SearchOrderMixin

class ProductListView(SearchOrderMixin, FilterView):
    model = Product
    filterset_fields = ["category", "status"]
    search_fields = ["name", "description"]
    order_by = [
        ("newest", "Newest First", "-created_at"),
        ("name_asc", "Name (A–Z)", "name"),
    ]
```

`?category=1&q=python&o=newest` returns records in category 1, containing "python", ordered newest-first. The filterset, ordering, and search constraints are all applied simultaneously.

> **Required pattern**: `SearchOrderMixin` must appear **left of** `FilterView`. Reversing the order causes the filterset to be applied after search/ordering, producing incorrect results.

Use `MVPFilteredListView` (requires `django-filter` installed) for the AdminLTE-integrated version with full `django_filters` support:

```python
from mvp.views import MVPFilteredListView

class ProductListView(MVPFilteredListView):
    model = Product
    filterset_fields = ["category"]
    search_fields = ["name", "description"]
    order_by = [
        ("newest", "Newest First", "-created_at"),
    ]
```

---

## 5. Customising Search Fields at Runtime

Override `get_search_fields()` to compute the list dynamically:

```python
class ProductListView(SearchMixin, ListView):
    model = Product

    def get_search_fields(self):
        if self.request.user.is_staff:
            return ["name", "description", "internal_notes"]
        return ["name", "description"]
```

---

## 6. Customising Ordering Choices at Runtime

Override `get_order_by_choices()` to compute the list dynamically:

```python
class ProductListView(OrderMixin, ListView):
    model = Product

    def get_order_by_choices(self):
        choices = [("name_asc", "Name (A–Z)", "name")]
        if self.request.user.is_staff:
            choices.append(("id_asc", "ID (oldest)", "id"))
        return choices
```
