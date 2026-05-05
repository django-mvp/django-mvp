# Quickstart: MVPUpdateView

## What it does

`MVPUpdateView` is a drop-in update view for any Django model. With two class
attributes you get a working edit page with:

- A model-aware page title ("Update Product")
- A three-level breadcrumb: list → record → form
- A Delete button that appears only when a delete view is accessible
- A success flash ("Product successfully updated.")

## Minimal setup

```python
# views.py
from mvp.views import MVPUpdateView
from .models import Product

class ProductUpdateView(MVPUpdateView):
    model = Product
    fields = ["name", "slug", "description", "price", "stock", "category"]
```

```python
# urls.py
from django.urls import path
from .views import ProductUpdateView

urlpatterns = [
    path("products/<int:pk>/update/", ProductUpdateView.as_view(), name="product-update"),
]
```

That's it. Navigate to `/products/1/update/` and you get:

- **Title**: "Update Product"
- **Breadcrumb**: Products (linked) → <product name> (linked) → Update Product
- **Delete button**: visible if `product-delete` URL is registered; hidden otherwise
- **Success redirect**: `product-detail` URL (via `resolve_crud_url("detail")`)

## Overriding defaults

```python
class ProductUpdateView(MVPUpdateView):
    model = Product
    fields = ["name", "slug"]
    page_title = "Edit product details"          # Custom title (no interpolation needed)
    success_message = "%(name)s was saved."      # Uses cleaned_data keys
    success_url = "list"                         # CRUD shorthand: redirects to product-list
```

## Breadcrumb behaviour

The middle breadcrumb item links to the detail view via `resolve_crud_url("detail")`.
If no detail view is registered (or `has_detail_permission` is falsy), the item
renders as plain text with no link — no configuration required.

```
Products  >  My Widget  >  Update Widget
    ↑             ↑              ↑
  list URL    detail URL    (current page)
              (or plain     (no link)
               text)
```

## Delete link behaviour

The Delete button is shown only when `get_delete_url()` returns a non-empty string.
It automatically includes `?back=<update_url>&next=<list_url>` query parameters so
the delete view redirects correctly:

- **Cancel** → back to the edit page
- **Confirm** → forward to the list page

To hide the Delete button unconditionally, override `get_delete_url()`:

```python
def get_delete_url(self):
    return ""
```

## Config reference

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `type[Model]` | — (required) | The Django model to update |
| `fields` | `list[str]` | — (required) | Fields to include in the auto-generated form |
| `form_class` | `type[ModelForm]` | `None` | Supply instead of `fields` for full form control |
| `page_title` | `str` | `_("Update %(verbose_name)s")` | Title shown in page header and breadcrumb |
| `page_icon` | `str` | `"edit"` | AdminLTE icon name |
| `page_class` | `str` | `"mvp-form-page mvp-update-page"` | CSS classes on the page container |
| `success_message` | `str` | `_("%(verbose_name)s successfully updated.")` | Flash message after save |
| `success_url` | `str` | `None` | CRUD shorthand (`"list"`, `"detail"`) or literal path |

## Override hooks

| Method | Returns | Override to… |
|--------|---------|-------------|
| `get_breadcrumbs()` | `list[dict]` | Customise the three-level breadcrumb items |
| `get_delete_url()` | `str` | Customise or suppress the delete link |
| `get_page_title()` | `str` | Fully replace title logic (inherited from `MVPModelFormBase`) |
| `get_success_message(cleaned_data)` | `str` | Fully replace message logic (inherited from `MVPModelFormBase`) |
| `get_success_url()` | `str` | Override the post-save redirect chain (inherited from `MVPModelFormBase`) |
