# Quickstart: Form View Base Classes (009-form-view-base)

This guide shows how the two base classes (`MVPFormBase`, `MVPModelFormBase`) work in
practice from a developer-integrator perspective.

---

## Zero-configuration model form view

Subclass any concrete view. Set `model`. Wire the URL. Done.

```python
# myapp/views.py
from mvp.views.edit import MVPCreateView
from myapp.models import Order

class OrderCreateView(MVPCreateView):
    model = Order
    fields = ["customer", "total"]
```

After a successful form submission:
- The user sees: **"Order successfully created."** (from `MVPCreateView.success_message`)
- The user is redirected to the `order-list` URL (automatic list-view fallback)
- No `success_url`, `get_success_message()`, or template configuration needed

---

## Customising the success message

Use `%(verbose_name)s` to include the model name, or add any field from `cleaned_data`.

```python
class OrderCreateView(MVPCreateView):
    model = Order
    fields = ["customer", "total"]
    success_message = "%(verbose_name)s for %(customer)s was placed."
    # → "Order for ACME Corp was placed."
```

On a delete view, `cleaned_data` is empty. Only `%(verbose_name)s` is safe:

```python
class OrderDeleteView(MVPDeleteView):
    model = Order
    success_message = "%(verbose_name)s was deleted."
    # → "Order was deleted."
    # Field placeholders like %(customer)s are silently replaced with ""
```

---

## Controlling the redirect destination

The priority chain is applied in order; override only what you need.

### 1. Embed `?next=` in the link

```html
<a href="{% url 'order-create' %}?next={{ request.path }}">Create Order</a>
```

After submission, the user returns to the page that linked to the form.

### 2. Use a CRUD action shorthand

```html
<a href="{% url 'order-create' %}?next=detail">Create and View</a>
```

The shorthand `detail` is resolved to the order's detail URL. On a create view, the
newly created object's pk is used automatically.

### 3. Set `success_url` on the view

```python
class OrderCreateView(MVPCreateView):
    model = Order
    fields = ["customer", "total"]
    success_url = "/orders/dashboard/"
```

### 4. Default: model list view (model form views only)

If none of the above are configured, `MVPModelFormBase` redirects to the model's list
view automatically. Misconfiguration raises `ImproperlyConfigured` with a clear message.

---

## Non-model form views

`MVPFormView` uses `MVPFormBase` directly. You must provide `success_url` (or handle
the redirect via `?next=`). Omitting both raises `ImproperlyConfigured`.

```python
from mvp.views.edit import MVPFormView
from myapp.forms import ContactForm

class ContactView(MVPFormView):
    form_class = ContactForm
    success_url = "/contact/thank-you/"
    page_title = "Contact Us"
    success_message = "Thanks! We'll be in touch."
```

---

## Changing the layout template

All form views use `form_view.html` as the fallback. Override only if you need a
different base layout:

```python
class OrderCreateView(MVPCreateView):
    model = Order
    template_name = "myapp/order_create.html"  # Checked first; form_view.html still fallback
```

---

## Misconfiguration errors

| Situation | Error |
|-----------|-------|
| `MVPFormView` with no `success_url` and no `?next=` | `ImproperlyConfigured: 'ContactView' must define 'success_url' or override 'get_success_url()'.` |
| `MVPCreateView` with no list URL configured and no `success_url` | `ImproperlyConfigured: 'OrderCreateView' could not resolve a list URL. Configure 'crud_views' or set 'success_url'.` |
