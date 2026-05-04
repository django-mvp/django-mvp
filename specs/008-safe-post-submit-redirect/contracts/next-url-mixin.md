# Contract: NextURLMixin — Safe `next` Parameter Handling

**Feature**: 008-safe-post-submit-redirect
**Date**: 2026-05-03
**Scope**: Public API contract for `NextURLMixin` and the `get_success_url()` redirect priority chain

---

## Overview

`NextURLMixin` provides safe handling of the `next` query/POST parameter for all form views in django-mvp. It is composed into `MVPFormBase`, which is the base for all concrete form view classes (`MVPFormView`, `MVPCreateView`, `MVPUpdateView`, `MVPDeleteView`).

---

## `NextURLMixin.get_next_url()`

### Signature

```python
def get_next_url(self) -> str | None
```

### Behaviour

- On **GET** requests: reads `next` from `request.GET`
- On **POST** requests: reads `next` from `request.POST`
- Validates the candidate value using `django.utils.http.url_has_allowed_host_and_scheme`:
  - `allowed_hosts = {request.get_host()}`
  - `require_https = request.is_secure()`
- Returns the validated URL string if safe; returns `None` otherwise
- When the candidate is present but rejected **and** `settings.DEBUG is True`, emits `logger.warning(...)` with the rejected value

### Return values

| Input | Return |
|-------|--------|
| Absent or empty `next` | `None` (silent) |
| Same-origin relative path (e.g., `/orders/`) | `"/orders/"` |
| Cross-origin absolute URL (e.g., `https://evil.com/`) | `None` (+ DEBUG log) |
| Protocol-relative URL (e.g., `//evil.com/path`) | `None` (+ DEBUG log) |
| Unsafe scheme (e.g., `javascript:alert(1)`) | `None` (+ DEBUG log) |
| CRUD action shorthand (e.g., `"list"`) | `None` — shorthands are NOT valid URLs |

> **Note**: `get_next_url()` is URL-only. CRUD shorthand resolution is separate and happens in `get_success_url()` and `get_context_data()`.

---

## `NextURLMixin.get_context_data()`

### Behaviour

Injects `next_url` into the template context. Value is determined as:

1. `get_next_url()` result (validated URL), or
2. Raw `next` value if it is a recognized CRUD shorthand (when `crud_views` is available on the view), or
3. `None`

### Template context key

| Key | Type | Value |
|-----|------|-------|
| `next_url` | `str \| None` | Validated URL path, CRUD shorthand string, or `None` |

### Usage in templates

```html
{% if next_url %}
  <input type="hidden" name="next" value="{{ next_url }}">
{% endif %}
```

This hidden field ensures `next_url` survives the POST round-trip, including for CRUD shorthands.

---

## `MVPFormBase.get_success_url()`

### Priority chain

```
1. get_next_url()           → validated same-origin next URL (FR-001 → FR-005a)
2. next shorthand           → resolved CRUD action URL via resolve_crud_url()
                               silently skipped when no crud_views or resolution fails
3. super().get_success_url() → Django FormMixin; uses self.success_url attribute
```

### Notes

- Steps 1 and 2 are only reached when a `next` value was present in POST data
- Step 3 is the Django standard `success_url` attribute
- If `success_url` is not set on the view, `super().get_success_url()` raises `ImproperlyConfigured` — this propagates upward (intended: `MVPFormView` developers must set `success_url`)

---

## `MVPModelFormBase.get_success_url()`

Extends `MVPFormBase.get_success_url()` with a model-specific fallback:

### Priority chain

```
1–3. Inherited from MVPFormBase (URL → shorthand → success_url)
4.   resoluve_crud_url("list")         → list URL for the current model (built-in fallback)
                               only reached when success_url is not set
```

### Notes

- Wraps step 3 in `try/except ImproperlyConfigured` to safely fall through to `resoluve_crud_url("list")`
- `resoluve_crud_url("list")` is always resolvable for model-based views (provided the list URL is registered)
- After a `CreateView` save, `get_url_kwargs()` is extended to include the new object's pk so that object-level shorthands (`next=detail`, `next=update`) resolve correctly

---

## Overridable extension points

| Method | Purpose |
|--------|---------|
| `get_next_url()` | Override to customize URL validation logic (e.g., allow additional trusted hosts) |
| `get_context_data()` | Override to change how `next_url` is exposed to templates |
| `get_success_url()` | Override to add project-specific redirect priority steps |
| `get_url_kwargs(action)` | Override to control which URL kwargs are used when resolving CRUD shorthands |
