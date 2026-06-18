# Quickstart: MVPListView

**Feature**: `015-mvp-list-view` | **Spec**: [spec.md](spec.md)

## Minimum Setup

Subclass `MVPListView` and declare `model`. Everything else has sensible defaults.

```python
# views.py
from mvp.views.list import MVPListView
from .models import Product

class ProductListView(MVPListView):
    model = Product
    # Automatic defaults:
    #   paginate_by = 24
    #   page title = "Products"  (verbose_name_plural.title())
    #   list_item_template = "shop/product_list_item.html"
    #   empty_state_heading = "There's nothing here yet"
```

```python
# urls.py
from django.urls import path
from .views import ProductListView

urlpatterns = [
    path("products/", ProductListView.as_view(), name="product-list"),
]
```

Create the item partial:

```html
{# templates/shop/product_list_item.html #}
<div class="card">
  <div class="card-body">{{ item.name }}</div>
</div>
```

---

## Search and Ordering

```python
class ProductListView(MVPListView):
    model = Product
    search_fields = ["name", "description", "category__name"]
    order_by = [
        ("name_asc",  "Name (A–Z)",       "name"),
        ("name_desc", "Name (Z–A)",        "-name"),
        ("newest",    "Newest First",      "-created_at"),
    ]
```

The template receives `search_query`, `is_searchable`, `order_by_choices`, and
`current_ordering` in context for building the search form and ordering controls.

---

## Grid Layout

Pass a `grid` dict to configure responsive column widths. The consuming Cotton
component (`<c-page.list-view>` or similar) reads `grid_config` from context.

```python
class ProductListView(MVPListView):
    model = Product
    grid = {"sm": 1, "md": 2, "lg": 3, "xl": 4}
```

---

## Custom Item Template

Override the default convention when needed:

```python
class ProductListView(MVPListView):
    model = Product
    list_item_template = "shared/product_card.html"
```

Or override `get_list_item_template()` for dynamic resolution:

```python
class ProductListView(MVPListView):
    model = Product

    def get_list_item_template(self):
        if self.request.user.is_premium:
            return "shop/product_list_item_rich.html"
        return "shop/product_list_item.html"
```

---

## Empty State

```python
class ProductListView(MVPListView):
    model = Product
    empty_state_heading = "No products found"
    empty_state_message = "Try adjusting your search or filters."
    # Set either to None to suppress that element entirely.
```

---

## Create Action Link

```python
class ProductListView(MVPListView):
    model = Product
    has_create_permission = True  # or a callable: lambda user: user.has_perm("shop.add_product")
    # directory.create_url is now available in the template context
```

The create URL is resolved via `CRUDDirectoryMixin` using the project's standard
view-naming convention. Only the create action is available from the list page context
— detail, update, and delete URLs are not injected.

---

## Custom Page Title

```python
class ProductListView(MVPListView):
    model = Product
    page_title = "Our Catalogue"  # overrides the model-derived default
```

---

## Pagination

`paginate_by = 24` is the library default. Override it on your subclass:

```python
class ProductListView(MVPListView):
    model = Product
    paginate_by = 12  # show 12 items per page
```

Django's standard pagination variables (`page_obj`, `paginator`, `is_paginated`)
are injected by `ListView` and available in the template.

---

## Context Reference

| Key | Type | Description |
|---|---|---|
| `list_item_template` | `str` | Path to item partial |
| `empty_state` | `dict` | `{"heading": str\|None, "message": str\|None}` |
| `grid_config` | `dict` | Grid layout config (may be empty) |
| `directory` | `dict` | `{"create_url": str}` when create permission is granted |
| `page.title` | `str` | Page heading |
| `page.breadcrumbs` | `list` | Breadcrumb trail |
| `search_query` | `str` | Active `?q=` value |
| `is_searchable` | `bool` | Whether search is configured |
| `order_by_choices` | `list[tuple]` | Ordering options (when configured) |
| `current_ordering` | `str` | Active `?o=` public key (when configured) |
| `page_obj` | `Page` | Django paginator page object |
| `is_paginated` | `bool` | Whether pagination is active |
