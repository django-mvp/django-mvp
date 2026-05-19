# Contract: Error Template Block API

**Feature**: 016-django-error-pages
**Type**: Template Override Contract
**Stability**: Stable (part of mvp public API)

## Overview

`mvp/error_base.html` is the shared layout scaffold for all Django error pages
provided by this package. It is a public extension point — downstream projects that
install `django-mvp` can override it to customise error page branding without
replacing individual error page templates.

---

## Template: `mvp/error_base.html`

**Inherits from**: `mvp/base.html`

**What it provides**: A minimal, full-viewport centered layout (no sidebar, header,
or footer) suitable for rendering standalone error pages at any HTTP error status.

### Block API

| Block name | Required | Default | Description |
|------------|----------|---------|-------------|
| `title` | No | `"Error"` | Page `<title>` content; appears in browser tab. Should include both the code and a human label (e.g. `"404 — Page Not Found"`). |
| `heading` | No | *(empty)* | Primary `<h1>` visible to the user. Should be short, friendly, and in plain language. |
| `description` | No | *(empty)* | Supporting paragraph explaining the error. Must use `{% trans %}` for i18n. |
| `actions` | No | *(empty)* | CTA row. Use `<c-button>` components. At minimum, provide a link back to `/`. |

> **Logo**: The application logo is rendered automatically by `error_base.html` above the heading on every error page. Individual templates do not need to include it.

> **Error code numbers**: Numeric HTTP status codes (e.g. "404") are NOT displayed on the visible page. The status code is communicated via the HTTP response headers and the page `<title>` only.

### Extending Example

```html
{# myapp/templates/403.html #}
{% extends "mvp/error_base.html" %}
{% load i18n %}

{% block title %}{% trans "403 — Forbidden" %}{% endblock %}

{% block heading %}
  {% trans "Access Denied." %}
{% endblock %}

{% block description %}
  {% trans "You do not have permission to view this page." %}
{% endblock %}

{% block actions %}
  <c-button variant="outline-secondary" icon="arrow-left" href="/" text="{% trans 'Back to home' %}" />
{% endblock %}
```

  <c-button variant="outline-secondary" icon="arrow-left" href="/" text="{% trans 'Back to home' %}" />
{% endblock %}
```

---

## Template: Individual Error Pages

Each of the four error page templates ships inside `django-mvp` and is referenced
automatically when Django's error handler mechanism fires.

| Template path | HTTP status | Handler |
|---------------|-------------|---------|
| `400.html` | 400 Bad Request | `handler400` → `mvp.views.error.bad_request` |
| `403.html` | 403 Forbidden | `handler403` → `mvp.views.error.permission_denied` |
| `404.html` | 404 Not Found | `handler404` → `mvp.views.error.not_found` |
| `500.html` | 500 Server Error | `handler500` → `mvp.views.error.server_error` |

All four extend `mvp/error_base.html` and can be overridden by placing a template
with the same name earlier in the template resolution order.

---

## Context Variables

### Shared (all error pages)

Context processors run normally. No additional context variables beyond the Django
standard set are injected into 400, 403, and 404 responses.

### 500 Only: `support_email`

| Variable | Type | When present |
|----------|------|-------------|
| `support_email` | `str` | When `settings.DEFAULT_FROM_EMAIL` is non-empty |
| `support_email` | `None` | When `settings.DEFAULT_FROM_EMAIL` is empty/absent |

Usage in `500.html`:

```html
{% if support_email %}
  <c-button variant="outline-secondary"
            icon="life-preserver"
            href="mailto:{{ support_email }}"
            text="{% trans 'Contact support' %}" />
{% endif %}
```

---

## View Function Signatures

Defined in `mvp/views/error.py`. All handlers are importable as string paths.

```python
def bad_request(request, exception):      # → HttpResponse 400
def permission_denied(request, exception): # → HttpResponse 403
def not_found(request, exception):         # → HttpResponse 404
def server_error(request):                 # → HttpResponse 500
```

**Registration** (in `demo/urls.py` or any root URLconf):

```python
handler400 = "mvp.views.error.bad_request"
handler403 = "mvp.views.error.permission_denied"
handler404 = "mvp.views.error.not_found"
handler500 = "mvp.views.error.server_error"
```
