# Research: HTMX Form Mixin (020-htmx-form-mixin)

**Date**: 2026-05-28
**Branch**: `020-htmx-form-mixin`

All decisions below were established during the spec clarification session (2026-05-28) via direct inspection of `django-htmx` and `django-cotton` source code and documentation. No unknowns remain.

---

## Decision Log

### 1. Htmx Request Detection

**Decision**: Use `request.htmx` from `django-htmx`'s `HtmxMiddleware`.

**Rationale**: `request.htmx` is a boolean-compatible `HtmxDetails` object that evaluates to `True` when the `HX-Request` header is present. It is injected by `HtmxMiddleware` and provides a clean, library-tested API. Raw header inspection (`request.headers.get("HX-Request")`) is fragile and bypasses this tested path.

**API**:

```python
from django_htmx.middleware import HtmxMiddleware  # configured in MIDDLEWARE

if request.htmx:
    # htmx-initiated request
```

**Alternatives considered**:

- Raw `request.headers.get("HX-Request") == "true"` — rejected (not idiomatic when django-htmx is installed; bypasses the library's tested interface)

---

### 2. Partial Response Rendering

**Decision**: Use `render_component(request, component_name, context)` from `django_cotton`.

**Rationale**: `django-cotton==2.6.1` is already a package dependency. `render_component()` renders a Cotton component to an HTML string using dot-notation component names. This integrates seamlessly with the project's existing Cotton template ecosystem.

**API**:

```python
from django_cotton import render_component
from django.http import HttpResponse

html = render_component(request, "ui.form-success", {"form": form, "object": obj})
response = HttpResponse(html)
```

**Component name convention**: `"ui.form-success"` → `cotton/ui/form_success.html`

**Alternatives considered**:

- `render_to_string()` with a standard Django template — rejected (does not integrate with Cotton component system)
- `TemplateResponse` — rejected (`render_component` returns a string; wrapping in `HttpResponse` is idiomatic)

---

### 3. Client-Side Redirect on Success

**Decision**: Use `HttpResponseClientRedirect(url)` from `django_htmx.http`.

**Rationale**: Sets the `HX-Redirect` response header, causing htmx to perform a full browser navigation to the target URL. This is the idiomatic django-htmx API for triggering client-side redirects after htmx requests.

**Note**: Django's standard `HttpResponseRedirect` (302) is ignored by htmx. `HttpResponseLocation` (SPA-style navigation) is out of scope for this feature.

**API**:

```python
from django_htmx.http import HttpResponseClientRedirect

return HttpResponseClientRedirect(self.get_success_url())
```

**Alternatives considered**:

- `HttpResponseLocation` — rejected (SPA-style navigation without full reload; not the behaviour requested)
- Setting `HX-Redirect` header manually — rejected (not idiomatic when django-htmx is available)

---

### 4. Client-Side Event Triggers

**Decision**: Use `trigger_client_event(response, name, params=None, *, after='receive')` from `django_htmx.http`.

**Rationale**: Modifies the response to include the appropriate `HX-Trigger` family header. The `after` parameter supports `'receive'` (default → `HX-Trigger`), `'settle'` (→ `HX-Trigger-After-Settle`), and `'swap'` (→ `HX-Trigger-After-Swap`). Safe to call multiple times on the same response for multiple events.

**API**:

```python
from django_htmx.http import trigger_client_event

trigger_client_event(response, "itemCreated", after="receive")
trigger_client_event(response, "listRefresh", {"section": "active"}, after="settle")
```

**Header mapping**:

| `after=` | Header set |
|---|---|
| `'receive'` | `HX-Trigger` |
| `'settle'` | `HX-Trigger-After-Settle` |
| `'swap'` | `HX-Trigger-After-Swap` |

**Alternatives considered**:

- Setting `HX-Trigger` header directly — rejected (not idiomatic; `trigger_client_event` handles JSON serialization and multiple calls correctly)

---

### 5. Django Messages Handling on HTMX Paths

**Decision**: Drain the message queue via `list(get_messages(request))` immediately after `super().form_valid()` on htmx success paths.

**Rationale**: `SuccessMessageMixin.form_valid()` (in the base view chain) queues a success message into the Django session. When returning an htmx partial instead of a full page, that message would surface as a stale toast on the next full-page navigation. `get_messages(request)` iterates the queue and marks messages as used, clearing them from the session.

**Important**: `get_messages()` must be iterated (not just called) for messages to be marked as used. The idiomatic pattern is `list(get_messages(request))`.

**API**:

```python
from django.contrib.messages import get_messages

# After super().form_valid() on htmx path:
list(get_messages(request))  # iterate to consume and discard
```

**Alternatives considered**:

- Passing messages to the partial via context — rejected (adds complexity; spec decision is to discard and use `htmx_trigger` for htmx-native feedback)
- Skipping `super().form_valid()` — rejected (would bypass object saving and other mixin logic)

---

### 6. Form-Error Response Status Code

**Decision**: Return HTTP 200 for form-error partials.

**Rationale**: Htmx by default only swaps content for 2xx responses. HTTP 422 or 400 responses require explicit client-side error handling configuration (`htmx.on('htmx:responseError', ...)` or `hx-validate`). HTTP 200 works with htmx's default swap behavior without any additional client-side configuration, matching the django-htmx recommended pattern.

**Alternatives considered**:

- HTTP 422 — rejected (requires `hx-validate` or custom JS error handler on the client)
- HTTP 400 — rejected (same issue as 422)

---

### 7. Mixin File Placement

**Decision**: New file `mvp/views/htmx.py`. Export `HtmxFormMixin` from `mvp/views/__init__.py`.

**Rationale**: Isolating the mixin in a dedicated file keeps `edit.py` clean (already ~250 LOC), makes the `django-htmx` dependency boundary explicit, and groups future htmx-related views naturally. Direct import in `__init__.py` (not try/except) since both libraries are required.

**Alternatives considered**:

- Adding to `edit.py` — rejected (edit.py is already complex; mixing form base classes with an htmx overlay creates conceptual clutter)
- Top-level `mvp/htmx.py` — rejected (inconsistent with the existing `mvp/views/` module structure)

---

### 8. Dependency Addition

**Decision**: Add `django-htmx>=1.0,<2.0` to `pyproject.toml` as a required package dependency.

**Rationale**: `django-cotton` is already present. `django-htmx` must be explicitly added. Both are required for the mixin to function.

**Required setup by consumers**:

1. `poetry add django-htmx` (or equivalent)
2. Add `"django_htmx.middleware.HtmxMiddleware"` to `MIDDLEWARE` in settings (after `SessionMiddleware`)

---

## Summary Table

| Decision | Choice | Rationale Key |
|---|---|---|
| Htmx detection | `request.htmx` | Library-idiomatic, tested API |
| Partial rendering | `render_component()` from django-cotton | Existing dep, Cotton ecosystem |
| Success redirect | `HttpResponseClientRedirect` | Sets `HX-Redirect`, full nav |
| Event triggers | `trigger_client_event()` | Sets `HX-Trigger` family correctly |
| Messages drain | `list(get_messages(request))` | Standard Django; clears session |
| Error status | HTTP 200 | htmx default swap, no client config |
| File placement | `mvp/views/htmx.py` | Separation of concerns |
| Dependency | `django-htmx>=1.0,<2.0` added | Required, not optional |
