# Quickstart: HTMX Form Mixin

A minimal guide to adding htmx progressive enhancement to any `django-mvp` form view using `HtmxFormMixin`.

---

## Prerequisites

### 1. Install `django-htmx`

```bash
poetry add django-htmx
```

`django-cotton` is already a dependency of `django-mvp`.

### 2. Add Middleware

In your Django settings, add `HtmxMiddleware` **after** `SessionMiddleware`:

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django_htmx.middleware.HtmxMiddleware",  # ← add here
    "django.middleware.common.CommonMiddleware",
    ...
]
```

### 3. Load htmx in Templates

In your base template (e.g. `base.html`):

```html
<script src="https://unpkg.com/htmx.org@2" defer></script>
```

---

## Minimum Configuration: Success Partial

Add the mixin **before** the base view class and set `htmx_success_component`. `htmx_form_component` defaults to `"form.card"` (the package's standard card form component) and does not need to be set:

```python
# views.py
from mvp.views import MVPCreateView
from mvp.views.htmx import HtmxFormMixin

class ProductCreateView(HtmxFormMixin, MVPCreateView):
    model = Product
    form_class = ProductForm
    htmx_success_component = "demo.product-created"  # → cotton/demo/product_created.html
    # htmx_form_component defaults to "form.card" — no need to set it unless overriding
    success_url = "/products/"  # used for non-htmx POST fallback
```

**Success partial** — shown when the form is valid and submitted via htmx:

```html
<!-- templates/cotton/demo/product-created.html -->
<div class="alert alert-success">
  Product "{{ object.name }}" was created successfully.
</div>
```

**Form partial** — shown when validation fails:

```html
<!-- templates/cotton/demo/product-form.html -->
<form hx-post="{{ request.path }}"
      hx-target="#form-container"
      hx-swap="outerHTML">
  {% csrf_token %}
  {{ form.as_div }}
  <button type="submit" class="btn btn-primary">Save</button>
</form>
```

**Page template** — wraps the form partial in a swap target:

```html
<!-- In the full-page template -->
<div id="form-container">
  <c-demo.product-form :form="form" />
</div>
```

---

## HX-Redirect on Success

Use `htmx_redirect_on_success = True` when the form should navigate the user to a new page (rather than swap a partial) after htmx submission:

```python
class OrderCreateView(HtmxFormMixin, MVPCreateView):
    model = Order
    form_class = OrderForm
    htmx_redirect_on_success = True   # returns HX-Redirect header
    # htmx_form_component defaults to "form.card"
    success_url = "list"              # resolved via CRUDDirectoryMixin
```

When both `htmx_redirect_on_success` and `htmx_success_component` are set, the redirect takes precedence.

---

## Emitting HX-Trigger Events on Success

Notify other htmx elements on the page when the form succeeds, without writing JavaScript:

```python
class ProductCreateView(HtmxFormMixin, MVPCreateView):
    model = Product
    form_class = ProductForm
    htmx_success_component = "demo.product-created"
    # htmx_form_component defaults to "form.card"
    htmx_trigger = "productCreated"           # simple string → HX-Trigger: productCreated
    htmx_trigger_after = "settle"             # → HX-Trigger-After-Settle
```

With a dict, include event params:

```python
htmx_trigger = {"productCreated": {"id": 1}}  # one event with params
```

Listen for the event in the template:

```html
<!-- Refreshes automatically when productCreated is triggered -->
<div hx-get="/products/" hx-trigger="productCreated from:body">
  ...
</div>
```

---

## Progressive Enhancement (Non-htmx Fallback)

The mixin is **completely transparent** for non-htmx requests. If a user submits the form without JavaScript, or without htmx loaded, the base view's standard behavior (full-page redirect or re-render) applies unchanged:

```python
class ProductCreateView(HtmxFormMixin, MVPCreateView):
    model = Product
    form_class = ProductForm
    htmx_success_component = "demo.product-created"
    # htmx_form_component defaults to "form.card"
    success_url = "/products/"   # used when htmx is not present
```

---

## Dynamic Template Selection

Override `get_htmx_success_component()` or `get_htmx_form_component()` for per-request logic:

```python
class ProductView(HtmxFormMixin, MVPCreateView):
    # htmx_form_component defaults to "form.card"

    def get_htmx_success_component(self):
        if self.request.user.is_staff:
            return "products.created-admin"
        return "products.created"
```

---

## Django Messages

When an htmx partial is returned on success, the mixin automatically drains Django's session message queue so that no stale toast appears on the next full-page navigation. Use `htmx_trigger` to deliver equivalent feedback to htmx-driven UI elements instead:

```python
class ProductCreateView(HtmxFormMixin, MVPCreateView):
    ...
    # success_message = "Product created."  ← queued by SuccessMessageMixin,
    #                                          then discarded on htmx paths
    htmx_trigger = "showSuccessToast"       # ← use this for htmx feedback
```

---

## Configuration Reference

| Attribute | Type | Default | Purpose |
|---|---|---|---|
| `htmx_success_component` | `str \| None` | `None` | Cotton component (dot-notation) rendered on success |
| `htmx_form_component` | `str` | `"form.card"` | Cotton component (dot-notation) rendered on invalid form |
| `htmx_redirect_on_success` | `bool` | `False` | Return `HX-Redirect` header on success instead of partial |
| `htmx_trigger` | `str \| dict \| None` | `None` | Event(s) to emit via `HX-Trigger` family headers on success |
| `htmx_trigger_after` | `'receive' \| 'settle' \| 'swap'` | `'receive'` | Controls timing variant of the trigger header |

### `htmx_trigger_after` Header Mapping

| Value | Header |
|---|---|
| `'receive'` (default) | `HX-Trigger` |
| `'settle'` | `HX-Trigger-After-Settle` |
| `'swap'` | `HX-Trigger-After-Swap` |

---

## Error Messages

| Scenario | Exception |
|---|---|
| htmx POST valid + `htmx_success_component` not set + `htmx_redirect_on_success=False` | `ImproperlyConfigured` |
| htmx POST invalid + `htmx_form_component` explicitly cleared to falsy | `ImproperlyConfigured` (default `"form.card"` prevents this) |
