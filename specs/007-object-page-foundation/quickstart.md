# Quickstart: Object Page Foundation

**Branch**: `007-object-page-foundation` | **Date**: 2026-05-03

This guide shows how to use `MVPDetailView` and `PageObjectMixin` to build read-only detail pages with zero boilerplate.

---

## The minimal detail view

The only required attribute is `model` (or `queryset`):

```python
# myapp/views.py
from mvp.views import MVPDetailView
from myapp.models import Order

class OrderDetailView(MVPDetailView):
    model = Order
```

Wire it to a URL:

```python
# myapp/urls.py
from django.urls import path
from .views import OrderDetailView

urlpatterns = [
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="myapp_order_detail"),
]
```

That's it. The rendered page automatically:

- Sets the page title to `str(order_instance)` (from `Order.__str__`).
- Applies the CSS classes `mvp-page mvp-detail-page order-page` to the page container.
- Tries `myapp/order_detail.html` first, falls back to `detail_view.html`.

---

## Adding a breadcrumb back-link to the list view

Enable list permission and include `"list"` in `directory`:

```python
class OrderDetailView(MVPDetailView):
    model = Order
    directory = ["list"]
    has_list_permission = True
```

The breadcrumb trail will be:

```
Orders  >  Order #42
```

The back-link text defaults to the model's plural verbose name, title-cased.

---

## Customising the breadcrumb back-link text

Set `list_view_title` on the view class:

```python
class OrderDetailView(MVPDetailView):
    model = Order
    directory = ["list"]
    has_list_permission = True
    list_view_title = "Active Orders"
```

Breadcrumb: `Active Orders  >  Order #42`

---

## Permission-gated action buttons

Use `directory` to declare which sibling action URLs appear in context, and
`has_{action}_permission` to gate them:

```python
class OrderDetailView(MVPDetailView):
    model = Order
    directory = ["list", "update", "delete"]
    has_list_permission = True

    def has_update_permission(self, user):
        return user.has_perm("myapp.change_order")

    def has_delete_permission(self, user):
        return user.is_staff
```

In the template, check for the key before rendering a button:

```html
{% if directory.update_url %}
  <a href="{{ directory.update_url }}" class="btn btn-primary">Edit</a>
{% endif %}
```

---

## Using PageObjectMixin directly (for custom object views)

Inherit `PageObjectMixin` when building a view that isn't a standard CRUD page
(e.g., a custom action page or a report for a specific object):

```python
from django.views.generic import DetailView
from mvp.views import PageObjectMixin

class OrderShippingView(PageObjectMixin, DetailView):
    model = Order
    template_name = "myapp/order_shipping.html"
    page_title = "Shipping Details"
    directory = ["list", "detail"]
    has_list_permission = True
    has_detail_permission = True
```

The `page` context dict, model-name CSS class, and breadcrumbs are all available without any extra setup.

---

## URL naming convention

`CRUDDirectoryMixin` (which `PageObjectMixin` inherits) resolves action URLs by combining
the app label, model name, and action name:

```
{app_label}_{model_name}_{action}
```

For `Order` in `myapp` with action `"list"`:

```
myapp_order_list
```

Override `crud_views` to use a different pattern if your project uses a different convention.
See the [CRUDDirectoryMixin quickstart](../../006-crud-directory-mixin/quickstart.md) for details.
