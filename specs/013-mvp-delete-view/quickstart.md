# Quickstart: MVPDeleteView

**Feature**: `013-mvp-delete-view`

`MVPDeleteView` is a configurable class-based delete view that integrates with the AdminLTE layout. It handles four deletion scenarios through class-level flags — no custom templates or form code required.

---

## Scenario 1 — Simple Confirmation (zero config)

Wire the view, set `model`, point `success_url` at the list view:

```python
# myapp/views.py
from mvp.views import MVPDeleteView
from myapp.models import Product

class ProductDeleteView(MVPDeleteView):
    model = Product
    success_url = "list"          # CRUD shorthand; also accepts a literal URL path
    has_list_permission = True    # enables the List breadcrumb and Go Back fallback
    has_detail_permission = True  # enables the Detail breadcrumb
```

```python
# myapp/urls.py
from django.urls import path
from myapp.views import ProductDeleteView

urlpatterns = [
    path("products/<int:pk>/delete/", ProductDeleteView.as_view(), name="product-delete"),
]
```

**What the user sees**: a warning banner ("You are about to permanently delete this record"), a Go Back button, and a Delete button.

**On Delete**: the record is removed, a flash message "Product successfully deleted." appears, and the user is redirected to the list view.

---

## Scenario 2 — Related-Objects Summary

Add `show_related_objects = True`:

```python
class ProductDeleteView(MVPDeleteView):
    model = Product
    success_url = "list"
    show_related_objects = True   # opt-in: one line
```

**What the user sees**: in addition to the warning, a grouped list of all records that will also be cascade-deleted (e.g. "Order Lines: Line 1, Line 2, … and 3 more"). The Delete button remains active.

No queryset code or template override needed. The view discovers cascade relations automatically.

### Raising the display cap

By default, each group shows at most 25 records. Change it:

```python
class ProductDeleteView(MVPDeleteView):
    model = Product
    success_url = "list"
    show_related_objects = True
    related_objects_max_per_group = 10  # show fewer, with "… and N more"
```

---

## Scenario 3 — Protected-Record Detection

No configuration needed. When `Product` has a `PROTECT` FK pointing to it (e.g. an `OrderLine`), the view detects this automatically:

**What the user sees**: instead of the warning + Delete button, an error banner lists the blocking records ("It is referenced by the following records…"). The Delete button is absent.

**On crafted POST**: the view re-renders the protection page — the record is never deleted.

```python
# No extra config required — protection detection is always active.
class ProductDeleteView(MVPDeleteView):
    model = Product
    success_url = "list"
```

---

## Scenario 4 — Type-to-Confirm

Add `require_confirmation = True`:

```python
class ProductDeleteView(MVPDeleteView):
    model = Product
    success_url = "list"
    require_confirmation = True   # opt-in: one line
```

**What the user sees**: an input field with the prompt "To confirm, type **Test Product** below:" (the object's `__str__`). The Delete button is disabled until the text matches.

**On wrong value**: the form is invalid, the page re-renders with an error, and the record is not deleted.

### Custom confirmation string

Override `get_confirmation_value()` to require something other than `str(object)`:

```python
class ProductDeleteView(MVPDeleteView):
    model = Product
    success_url = "list"
    require_confirmation = True

    def get_confirmation_value(self):
        return self.object.sku  # user must type the SKU code
```

### Custom input label

```python
class ProductDeleteView(MVPDeleteView):
    model = Product
    require_confirmation = True
    confirmation_label = _("Type the product SKU to confirm")
```

---

## Combining scenarios

Scenarios 2 and 4 can be combined:

```python
class SensitiveProductDeleteView(MVPDeleteView):
    model = Product
    success_url = "list"
    show_related_objects = True
    require_confirmation = True
```

Protection detection always takes precedence: when `is_protected=True`, both the related-objects list and the type-to-confirm input are hidden, and the Delete button is absent.

---

## Redirects: `?back` and `?next`

The update view passes `?back=<update-url>&?next=<list-url>` to the delete view automatically. The delete view uses:
- `?back=` for the Go Back button.
- `?next=` (from the POST body) for the post-delete redirect destination.

When generated manually (e.g. from a detail template):

```html
<a href="{% url 'product-delete' pk=product.pk %}?back={{ request.path }}&next={% url 'product-list' %}">
  Delete
</a>
```

---

## Breadcrumbs

Default: **All Products** → **Test Product** → **Delete Product**

Each breadcrumb link is gated by the corresponding permission flag:

```python
class ProductDeleteView(MVPDeleteView):
    model = Product
    has_list_permission = True    # "All Products" renders as a link
    has_detail_permission = True  # "Test Product" renders as a link
    # Without these flags, the crumbs render as plain text.
```

---

## Page title and success message

Both use the model's `verbose_name` automatically:

| Attribute | Default | Example |
|---|---|---|
| `page_title` | `_("Delete %(verbose_name)s")` | "Delete Product" |
| `success_message` | `_("%(verbose_name)s successfully deleted.")` | "product successfully deleted." |

Override either as a class attribute:

```python
class ProductDeleteView(MVPDeleteView):
    model = Product
    page_title = _("Remove product from catalogue")
    success_message = _("Product removed.")
```
