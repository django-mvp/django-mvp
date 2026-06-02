# Quickstart: List View Inline Create

**Feature**: `021-list-inline-create`
**Applies to**: `MVPListViewMixin`, `MVPListView`, `MVPTableViewMixin`

---

## Zero-config enablement

Add `create_form_class` to any `MVPListViewMixin` subclass and set
`has_create_permission = True`. The modal button, modal, and form injection are
handled automatically.

```python
# views.py
from mvp.views.list import MVPListView
from .forms import ProductForm


class ProductListView(MVPListView):
    model = Product
    create_form_class = ProductForm
    has_create_permission = True  # or a callable — see below
```

That's it. The toolbar will show an "Add new" button that opens a modal containing
the form. On successful submission the user is redirected back to the list page.

---

## Permission gating

`has_create_permission` accepts a boolean or a callable that receives `request.user`:

```python
class ProductListView(MVPListView):
    model = Product
    create_form_class = ProductForm
    has_create_permission = staticmethod(lambda user: user.has_perm("shop.add_product"))
```

When the callable returns `False` no form is injected and no button appears.

---

## Overriding the modal title

The default title is `"Add Product"` (derived from `model._meta.verbose_name`).
Override it with the `create_modal_title` attribute:

```python
class ProductListView(MVPListView):
    model = Product
    create_form_class = ProductForm
    has_create_permission = True
    create_modal_title = "Create a new product"
```

---

## Customising form instantiation

Override `get_create_form()` to pass extra kwargs (e.g. initial data, the request
object, or a queryset):

```python
class ProductListView(MVPListView):
    model = Product
    create_form_class = ProductForm
    has_create_permission = True

    def get_create_form(self):
        return self.create_form_class(
            initial={"category": self.request.GET.get("category")}
        )
```

---

## Fallback behaviour

| Scenario | Result |
|---|---|
| `create_form_class` set, permission granted, `create_url` resolved | "Add new" button opens modal |
| `create_form_class` set, permission granted, `create_url` unavailable | `create_form` in context but no button shown |
| `create_form_class` not set, permission granted | "Add new" button links to create page |
| Permission denied (any case) | No button, no form in context |

---

## Success redirect

The modal form POSTs to `create_url?next=<list_url>`. After a successful create the
user is automatically redirected back to the list page (honoured by `MVPCreateView`'s
`NextURLMixin`). If the create view is not an `MVPCreateView`, ensure its
`get_success_url()` honours the `?next=` parameter.
