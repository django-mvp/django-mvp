# Data Model: Django Error Pages

**Feature**: 016-django-error-pages
**Branch**: feature/016-django-error-pages
**Date**: 2026-05-19

## No Database Models

This feature introduces no Django models, migrations, or database schema changes.

All error pages are stateless — they render purely from template context populated at
request time from Django settings and the exception object (where applicable).

---

## Runtime Data Structures

Although there is no persistent data model, the following runtime context shapes are
passed to each error template. These are the "data model" for template authors.

### 400.html — Bad Request

| Variable | Type | Source | Notes |
|----------|------|--------|-------|
| `request` | `HttpRequest` | Django | Standard Django template context |
| `exception` | `Exception` or `None` | Django | The `SuspiciousOperation` exception; may be `None` in some paths |

### 403.html — Forbidden

| Variable | Type | Source | Notes |
|----------|------|--------|-------|
| `request` | `HttpRequest` | Django | Standard Django template context |
| `exception` | `PermissionDenied` or `None` | Django | The permission exception instance |

### 404.html — Not Found

| Variable | Type | Source | Notes |
|----------|------|--------|-------|
| `request` | `HttpRequest` | Django | Standard Django template context |
| `exception` | `Http404` or `None` | Django | The Http404 exception instance |

### 500.html — Server Error

| Variable | Type | Source | Notes |
|----------|------|--------|-------|
| `request` | `HttpRequest` | Django | Standard Django template context |
| `support_email` | `str` or `None` | `settings.DEFAULT_FROM_EMAIL` | `None` if the setting is empty; template hides contact action when `None` |

### error_base.html — Base Template Blocks

The base template is never rendered directly. It defines the layout scaffold and
the following named blocks consumed by child templates:

| Block name | Purpose | Default value |
|------------|---------|---------------|
| `title` | `<title>` content (also used in tab/browser title) | `"Error"` |
| `error_code` | Large numeric code display (e.g., `<div class="display-1">404</div>`) | *(empty)* |
| `heading` | Primary `<h1>` visible heading | *(empty)* |
| `description` | Supporting paragraph text | *(empty)* |
| `actions` | CTA buttons / navigation links | *(empty)* |
