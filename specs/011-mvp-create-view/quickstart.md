# Quickstart: MVPCreateView — Zero-Config Model Create View

**Feature**: `specs/011-mvp-create-view/spec.md`
**Date**: 2026-05-05

---

## Two-Line Create Page

```python
# myapp/views.py
from mvp.views.edit import MVPCreateView
from .models import Product

class ProductCreateView(MVPCreateView):
    model = Product
    fields = ["name", "slug", "description", "price", "stock", "category"]
```

That is all that is required. The view automatically provides:

| Feature | Automatic value |
|---------|----------------|
| Page title | `"Create Product"` |
| Page icon | `"add"` |
| Page CSS | `"mvp-page product-page mvp-form-page mvp-create-page"` |
| Success message | `"Product successfully created."` |
| Breadcrumb | Products → Create Product |
| Success redirect | `product.get_absolute_url()` or `success_url` |

---

## URL wiring

```python
# myapp/urls.py
from django.urls import path
from .views import ProductCreateView

urlpatterns = [
    path("products/create/", ProductCreateView.as_view(), name="product-create"),
]
```

---

## Customising the title

The default `page_title` is the translatable template `_("Create %(verbose_name)s")`,
which `get_page_title()` interpolates with the model's `verbose_name.title()` at
request time. You may include `%(verbose_name)s` in your override too:

```python
class ProductCreateView(MVPCreateView):
    model = Product
    fields = ["name", "slug", "description"]
    page_title = "Add a new %(verbose_name)s"  # → "Add a new Product"

# Or a plain string with no placeholder:
class ProductCreateView(MVPCreateView):
    model = Product
    fields = ["name", "slug", "description"]
    page_title = "Add a new product"
```

Setting `page_title` to a falsy value (`None`, `False`, `""`) returns it as-is —
treated as a deliberate choice, not a fallback trigger.

Or make it dynamic by overriding `get_page_title()`:

```python
class ProductCreateView(MVPCreateView):
    model = Product
    fields = ["name", "slug"]

    def get_page_title(self):
        return f"Add {self.model._meta.verbose_name_plural.title()}"
```

---

## Customising the success message

Set `success_message`. Use `%(key)s` placeholders from `cleaned_data`
or `%(verbose_name)s` for the model name (title-cased):

```python
class ProductCreateView(MVPCreateView):
    model = Product
    fields = ["name", "slug"]
    success_message = "%(name)s was added to the catalogue."
```

To suppress the message entirely, set `success_message = ""`.

---

## Customising the redirect

After a successful save, the view uses this priority chain:

1. `?next=` / `POST next=` — URL or CRUD shorthand (e.g. `"list"`, `"detail"`)
2. `success_url` — CRUD shorthand or literal URL path
3. `object.get_absolute_url()` — the newly created object's URL
4. `ImproperlyConfigured` — if none of the above are available

```python
class ProductCreateView(MVPCreateView):
    model = Product
    fields = ["name", "slug"]
    success_url = "list"   # resolves to the product list URL
```

---

## Customising the breadcrumb

The breadcrumb is built automatically from the list view URL and the current
page title. To customise, override `get_breadcrumbs()`:

```python
class ProductCreateView(MVPCreateView):
    model = Product
    fields = ["name", "slug"]

    def get_breadcrumbs(self):
        return [
            {"text": "Catalogue", "href": "/catalogue/"},
            {"text": "Products", "href": self.resolve_crud_url("list")},
            {"text": self.get_page_title()},
        ]
```

When no list URL can be resolved (e.g. no `has_list_permission`), the first
breadcrumb item renders as plain text automatically — no extra code needed.

---

## CRUD permission gating

Connect view URLs to CRUD directory link generation by setting permission flags:

```python
class ProductCreateView(MVPCreateView):
    model = Product
    fields = ["name", "slug"]
    has_list_permission = True
    has_create_permission = True
    has_detail_permission = True
    has_update_permission = True
```

---

## Using a custom form class

```python
from myapp.forms import ProductForm

class ProductCreateView(MVPCreateView):
    model = Product
    form_class = ProductForm
    success_message = "%(name)s added."
```
