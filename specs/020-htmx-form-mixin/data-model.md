# Data Model & Interface Design: HTMX Form Mixin (020-htmx-form-mixin)

**Date**: 2026-05-28
**Branch**: `020-htmx-form-mixin`

## Note

This feature introduces **no Django model changes** and **no database migrations**. The design artifact here is the Python class interface contract for `HtmxFormMixin`.

---

## Class Hierarchy

```
                    ┌──────────────────────────────┐
                    │        HtmxFormMixin          │
                    │    (mvp/views/htmx.py)        │
                    └──────────────┬───────────────┘
                                   │  mixed in before base view class
                    ┌──────────────▼───────────────┐
                    │   MVPFormView                 │
                    │   MVPCreateView               │
                    │   MVPUpdateView         (any) │
                    │   MVPDeleteView               │
                    └──────────────────────────────┘
```

**MRO example** (Python method resolution order):

```python
class MyCreateView(HtmxFormMixin, MVPCreateView):
    ...
# MRO: MyCreateView → HtmxFormMixin → MVPCreateView → MVPModelFormBase
#      → MVPFormBase → SuccessMessageMixin → BaseTemplateNameMixin
#      → NextURLMixin → PageObjectMixin → BaseCreateView → ...
```

`HtmxFormMixin` MUST appear before the base view class in the inheritance list so that its `form_valid()` and `form_invalid()` overrides intercept before the base class methods.

---

## HtmxFormMixin — Class Specification

### Class Attributes

| Attribute | Type | Default | Description |
|---|---|---|---|
| `htmx_success_template` | `str \| None` | `None` | Cotton component name (dot-notation) for the success partial. Example: `"ui.product-created"` → `cotton/ui/product_created.html` |
| `htmx_form_template` | `str \| None` | `None` | Cotton component name (dot-notation) for the form-error partial. Required when htmx POST is expected. |
| `htmx_redirect_on_success` | `bool` | `False` | When `True`, returns `HttpResponseClientRedirect` on a valid htmx POST instead of a success partial. |
| `htmx_trigger` | `str \| dict \| None` | `None` | Event(s) to emit on the success response via `HX-Trigger` family headers. A string emits one event; a dict emits one event per key. |
| `htmx_trigger_after` | `Literal['receive', 'settle', 'swap']` | `'receive'` | Controls which `HX-Trigger` header variant is used. |

---

### Public Method Contracts

#### `get_htmx_success_template() → str`

Returns the Cotton component name for the success partial.

Default implementation returns `self.htmx_success_template`.

Override for dynamic (per-request) component name resolution.

**Raises**: `ImproperlyConfigured` if `self.htmx_success_template` is falsy and `self.htmx_redirect_on_success` is also falsy — enforced in `form_valid()`, not in this method itself.

---

#### `get_htmx_form_template() → str`

Returns the Cotton component name for the form-error partial.

Default implementation returns `self.htmx_form_template`.

Override for dynamic component name resolution.

**Raises**: `ImproperlyConfigured` if `self.htmx_form_template` is falsy — enforced in `form_invalid()`, not in this method itself.

---

#### `form_valid(form) → HttpResponse`

**Triggered**: When the form passes validation (`form.is_valid()` returns `True`).

**Non-htmx path** (`not request.htmx`): Delegates entirely to `super().form_valid(form)`. No deviation from the base view's behavior.

**Htmx path** (`request.htmx`):

1. Calls `super().form_valid(form)` to:
   - Save the model instance (for model form views).
   - Queue any success message via `SuccessMessageMixin`.
   - Note: the standard redirect response returned by `super()` is **discarded**.
2. Drains the Django message queue: `list(get_messages(request))`.
3. If `htmx_redirect_on_success` is truthy:
   - Returns `HttpResponseClientRedirect(self.get_success_url())`.
4. Otherwise:
   - Verifies `get_htmx_success_template()` returns a non-empty value; raises `ImproperlyConfigured` if not.
   - Builds context via `self.get_context_data(form=form)`.
   - Returns `HttpResponse(render_component(request, template, context))`.
5. If `htmx_trigger` is set, calls `trigger_client_event()` on the response before returning.

---

#### `form_invalid(form) → HttpResponse`

**Triggered**: When the form fails validation (`form.is_valid()` returns `False`).

**Non-htmx path** (`not request.htmx`): Delegates entirely to `super().form_invalid(form)`. No deviation.

**Htmx path** (`request.htmx`):

1. Verifies `get_htmx_form_template()` returns a non-empty value; raises `ImproperlyConfigured` if not.
2. Builds context via `self.get_context_data(form=form)`.
3. Returns `HttpResponse(render_component(request, template, context), status=200)`.

---

### Response Decision Tree

```
POST received
│
├─ request.htmx is False
│   └─ delegate to super().form_valid() / super().form_invalid()  [no change]
│
└─ request.htmx is True
    │
    ├─ form.is_valid() → True
    │   ├─ super().form_valid(form)          [saves object, queues message]
    │   ├─ list(get_messages(request))       [drain & discard messages]
    │   │
    │   ├─ htmx_redirect_on_success=True
    │   │   └─ HttpResponseClientRedirect(success_url)
    │   │       └─ if htmx_trigger: trigger_client_event(response, ...)
    │   │
    │   └─ htmx_redirect_on_success=False
    │       └─ HttpResponse(render_component(request, success_template, context))
    │           └─ if htmx_trigger: trigger_client_event(response, ...)
    │
    └─ form.is_valid() → False
        └─ HttpResponse(render_component(request, form_template, context), status=200)
```

---

### Context Passed to `render_component()`

**Success path** (when `htmx_success_template` is used):

```python
context = self.get_context_data(form=form)
# Includes: object (saved instance), form (bound + valid), request, view, ...
```

**Error path** (when `htmx_form_template` is used):

```python
context = self.get_context_data(form=form)
# Includes: form (bound + invalid, with .errors populated), request, view, ...
```

`get_context_data()` is inherited from the base view and includes all standard Django context (object, view, request processor output, etc.).

---

### Trigger Dispatch Logic

When `htmx_trigger` is a **string**:

```python
trigger_client_event(response, self.htmx_trigger, after=self.htmx_trigger_after)
```

When `htmx_trigger` is a **dict** (`{event_name: params, ...}`):

```python
for name, params in self.htmx_trigger.items():
    trigger_client_event(response, name, params, after=self.htmx_trigger_after)
```

---

### Header Mapping

| `htmx_trigger_after` value | Header written |
|---|---|
| `'receive'` (default) | `HX-Trigger` |
| `'settle'` | `HX-Trigger-After-Settle` |
| `'swap'` | `HX-Trigger-After-Swap` |

---

## Precedence Rules

| Configuration | Behaviour |
|---|---|
| `htmx_redirect_on_success=True` + `htmx_success_template` set | Redirect takes precedence; success template ignored |
| `htmx_success_template` not set + `htmx_redirect_on_success=False` | `ImproperlyConfigured` raised on valid htmx POST |
| `htmx_form_template` not set | `ImproperlyConfigured` raised on invalid htmx POST |
| Neither htmx attribute set + non-htmx request | Full transparent delegation to base view (no error) |

---

## External Interfaces

### Imports Required in `mvp/views/htmx.py`

```python
from django.contrib.messages import get_messages
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django_cotton import render_component
from django_htmx.http import HttpResponseClientRedirect, trigger_client_event
```

### Export in `mvp/views/__init__.py`

```python
from .htmx import HtmxFormMixin

__all__ += ["HtmxFormMixin"]
```
