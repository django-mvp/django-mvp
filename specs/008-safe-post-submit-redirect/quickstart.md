# Quickstart: Safe Post-Submit Redirect

**Feature**: 008-safe-post-submit-redirect

This guide shows how to use the `next` parameter to redirect users after a successful form submission in django-mvp views.

---

## Basic usage — redirect to an explicit URL

Pass `?next=` as a query parameter when linking to a form view. After a successful save, the user is redirected to that URL.

```html
<!-- Link from a parent record page to a nested create form -->
<a href="{% url 'order-create' %}?next={{ request.path }}">
  Add Order Line
</a>
```

The `next` parameter is automatically validated and rejected if it points to a different host or uses an unsafe scheme. Invalid values fall through to the view's normal success URL.

---

## CRUD action shorthands

For common post-save destinations, use a shorthand key instead of a URL:

| Shorthand | Redirects to |
|-----------|-------------|
| `next=list` | The model's list view |
| `next=detail` | The detail view of the saved object |
| `next=update` | The update view of the saved object |
| `next=delete` | The delete view of the saved object |
| `next=create` | The create view for the same model |

```html
<a href="{% url 'order-create' %}?next=list">Create and go to list</a>
<a href="{% url 'order-update' pk=order.pk %}?next=detail">Save and view details</a>
```

Shorthand resolution follows the same directory configured in `CRUDDirectoryMixin.crud_views`. Unknown shorthand keys are silently ignored and fall through to the normal success URL.

---

## Template — preserving `next` across failed validation

When the form is re-submitted with errors, `next_url` is automatically re-injected into the template context. Add a hidden field to your form template to preserve it:

```html
<form method="post">
  {% csrf_token %}
  {{ form }}
  {% if next_url %}
    <input type="hidden" name="next" value="{{ next_url }}">
  {% endif %}
  <button type="submit">Save</button>
</form>
```

This works for both plain URL values and CRUD shorthands — `next_url` holds whichever form was originally used.

---

## Success URL priority

If no `next` parameter is provided, redirect targets are resolved in this order:

1. `next` parameter — validated URL or CRUD shorthand (if present)
2. `success_url` — class attribute on the view (if set)
3. `resoluve_crud_url("list")` — the model's list view (model views only)

To set a fixed default destination:

```python
class OrderCreateView(MVPCreateView):
    model = Order
    success_url = "/orders/"  # used when no 'next' param provided
```

---

## Debug logging

When `settings.DEBUG = True`, rejected `next` values are logged as warnings. Enable logging in your development settings:

```python
# settings/local.py
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "mvp.views.edit": {
            "handlers": ["console"],
            "level": "DEBUG",
        }
    },
}
```

A log message will appear when an unsafe or cross-origin `next` value is rejected:

```
WARNING mvp.views.edit: next parameter 'https://evil.com/' rejected (unsafe or cross-origin); falling back to default destination.
```

This is silent in production (`DEBUG = False`).

---

## Non-model form views (`MVPFormView`)

`MVPFormView` also supports `next` URL redirect and CRUD shorthand resolution, but since it has no model identity, `success_url` is required as a fallback:

```python
class ContactFormView(MVPFormView):
    form_class = ContactForm
    success_url = "/contact/thank-you/"  # required

    def form_valid(self, form):
        form.send_email()
        return super().form_valid(form)
```

If `next=list` is passed but the view has no CRUD directory configured, it is silently ignored and `success_url` is used.
