# Quickstart: Django Error Pages

**Feature**: 016-django-error-pages
**Audience**: Developers integrating `django-mvp` into a new project

---

## What You Get Out of the Box

`django-mvp` ships four styled error page templates:

| Template | HTTP Code | Meaning |
|----------|-----------|---------|
| `400.html` | 400 | Bad Request (malformed/suspicious input) |
| `403.html` | 403 | Forbidden (insufficient permissions) |
| `404.html` | 404 | Not Found (missing URL or object) |
| `500.html` | 500 | Server Error (unhandled exception) |

All four extend `mvp/error_base.html` — they share a consistent full-viewport
centered layout, use your existing Bootstrap 5 theme, and are fully responsive
(mobile-first, WCAG 2.1 AA).

---

## Step 1: Register Error Handlers

Django uses module-level handler variables in your root URL configuration. Add these
four lines to your project's root `urls.py`:

```python
# myproject/urls.py  (or demo/urls.py for django-mvp's own demo app)

handler400 = "mvp.views.error.bad_request"
handler403 = "mvp.views.error.permission_denied"
handler404 = "mvp.views.error.not_found"
handler500 = "mvp.views.error.server_error"
```

> **Note**: Django only uses custom error handlers when `DEBUG = False` for 404/500.
> In development (`DEBUG = True`), Django renders its own debug pages. Use the
> demo preview routes (Step 3) to inspect styling during development.

---

## Step 2: Configure the Support Email (Optional)

The 500 error page optionally displays a "Contact support" button. It reads from
Django's built-in `DEFAULT_FROM_EMAIL` setting:

```python
# settings.py
DEFAULT_FROM_EMAIL = "support@yourcompany.com"
```

If this setting is empty or not set, the button is automatically hidden — no
template changes required.

---

## Step 3: Preview Error Pages in Development

The demo app registers preview routes for each error page. Navigate to these URLs
while `DEBUG = True` to inspect the layout and styling without triggering real errors:

| URL | Preview |
|-----|---------|
| `/errors/400/` | Bad Request page |
| `/errors/403/` | Forbidden page |
| `/errors/404/` | Not Found page |
| `/errors/500/` | Server Error page |

These routes also appear in the demo app's sidebar under **Error Pages**.

---

## Step 4: Override a Template (Optional)

To replace a specific error page with your own design while keeping the base layout,
create a template with the same name in your app's `templates/` directory:

```html
{# myapp/templates/404.html #}
{% extends "mvp/error_base.html" %}
{% load i18n %}

{% block title %}{% trans "404 — Not Found" %}{% endblock %}
{% block error_code %}<div class="display-1 fw-bold text-primary lh-1 mb-3">404</div>{% endblock %}
{% block heading %}<h1 class="h3 mb-3">{% trans "This page doesn't exist." %}</h1>{% endblock %}
{% block description %}
  <p class="text-secondary mb-4">{% trans "Double-check your URL and try again." %}</p>
{% endblock %}
{% block actions %}
  <c-button variant="outline-secondary" icon="arrow-left" href="/" text="{% trans 'Go home' %}" />
{% endblock %}
```

Make sure your app appears **before** `mvp` in `INSTALLED_APPS` so that Django's
template loader finds your override first.

---

## Template Block Reference

| Block | Default | Description |
|-------|---------|-------------|
| `title` | `"Error"` | Browser `<title>` content |
| `error_code` | *(empty)* | Large numeric code element |
| `heading` | *(empty)* | Primary `<h1>` heading |
| `description` | *(empty)* | Explanatory paragraph |
| `actions` | *(empty)* | CTA buttons (use `<c-button>`) |

Full API reference: [contracts/template-block-api.md](contracts/template-block-api.md)
