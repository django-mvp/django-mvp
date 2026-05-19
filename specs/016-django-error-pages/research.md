# Research: Django Error Pages

**Feature**: 016-django-error-pages
**Branch**: feature/016-django-error-pages
**Date**: 2026-05-19

## Research Questions

The spec had no `NEEDS CLARIFICATION` items. Research focused on three technical
questions that directly influence the design:

1. How does Django dispatch to custom error handlers, and what arguments do they receive?
2. How is `DEFAULT_FROM_EMAIL` safely injected into the 500 error template?
3. Is `mvp/base.html` / `error_base.html` safe to render during a 500 error (no DB calls)?

---

## Q1: Django Error Handler Dispatch

### Decision
Use simple Django view functions registered as module-level variables in the root
URL config (`demo/urls.py`). For 400, 403, and 404 the handler receives
`(request, exception)`; for 500 it receives only `(request)`.

### Rationale
Django's error handler mechanism is well-defined and stable across 4.x–5.x:

| Handler | Signature | When triggered |
|---------|-----------|----------------|
| `handler400` | `(request, exception)` | `SuspiciousOperation` / `BadRequest` |
| `handler403` | `(request, exception)` | `PermissionDenied` |
| `handler404` | `(request, exception)` | `Http404` |
| `handler500` | `(request)` | Unhandled exception in view |

These are set by pointing the module-level names at callables in `demo/urls.py`:

```python
handler400 = "mvp.views.error.bad_request"
handler403 = "mvp.views.error.permission_denied"
handler404 = "mvp.views.error.not_found"
handler500 = "mvp.views.error.server_error"
```

Django requires the handler to be importable as a string path OR assigned as a
callable. String paths are preferred for clarity.

Each view must return an `HttpResponse` with the correct status code explicitly set
(Django does NOT set it automatically from the handler name).

### Alternatives Considered
- **Use Django's built-in `defaults.page_not_found` etc.**: These render `404.html`
  without any extra context — would work for 400/403/404 but not for 500 (which
  needs `support_email` in context).
- **Single generic error view**: Rejected — conflates distinct error types and makes
  template logic more complex.

---

## Q2: DEFAULT_FROM_EMAIL in the 500 Template

### Decision
The `server_error` view function reads `settings.DEFAULT_FROM_EMAIL` at call time
and passes it as `support_email` in the template context. If the setting is empty
(`""` or `None`), `support_email` is set to `None` and the template conditionally
hides the contact button.

```python
from django.conf import settings
from django.shortcuts import render

def server_error(request):
    support_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or None
    return render(request, "500.html", {"support_email": support_email}, status=500)
```

Reading from `settings` is synchronous, instant, and never touches the database — it
is safe to call from within a 500 error handler.

### Rationale
`DEFAULT_FROM_EMAIL` is already a standard Django setting present in every project.
No additional configuration is required of downstream integrators.

### Alternatives Considered
- **Context processor**: Rejected — context processors run for every request and add
  overhead; `support_email` is only needed on one page.
- **Template tag that reads settings**: Rejected — coupling a template tag to
  settings is non-obvious; view-level injection is more transparent.
- **Hardcoded placeholder**: Rejected by spec clarification (Q3 answer was Option A).

---

## Q3: Safety of error_base.html During a 500 Error

### Decision
`error_base.html` is safe to render during all error scenarios, including genuine
500 errors where the database may be unavailable.

### Rationale
Verified by reading the template inheritance chain:

1. `error_base.html` extends `mvp/base.html`
2. `mvp/base.html` defines a `{% block app %}` that renders `<c-app>`, which
   includes `<c-app.sidebar />` (which runs `{% render_menu "AppMenu" ... %}`)
3. **However**, `error_base.html` **completely overrides** `{% block app %}` with a
   minimal centered layout — sidebar, header, footer, and menu are never rendered
4. The `<head>` block (CSS, JS) is inherited unchanged — this is pure static asset
   delivery with no DB interaction

**Context processors** run regardless of which template is rendered:
- `debug` — reads `settings.DEBUG` (no DB)
- `request` — wraps the request object (no DB)
- `auth` — reads from the session cache (no direct DB call; sessions use cache by
  default)
- `messages` — reads from session (no direct DB call)
- `mvp.context_processors.mvp_config` — returns static config dict (no DB)

**Conclusion**: No context processor in the project makes a direct DB call in the
request/response path. The template is safe to render even if the DB is down.

### Alternatives Considered
- **Standalone 500 template with no inheritance**: Would guarantee DB-safety but
  requires duplicating all CSS/JS includes. Rejected — risk is already mitigated.
- **Use `django.views.defaults.server_error` directly**: Does not support custom
  context (cannot inject `support_email`). Rejected.
