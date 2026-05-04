# Data Model: Safe Post-Submit Redirect

**Feature**: 008-safe-post-submit-redirect
**Date**: 2026-05-03

This feature introduces no new Django models or database migrations. The "data model" here describes the **class hierarchy and state transitions** relevant to the redirect mechanism.

---

## Class Hierarchy

```text
NextURLMixin
    └── get_next_url() → str | None      # validates next as a URL only
    └── get_context_data()               # injects next_url into template context

MVPFormBase(SuccessMessageMixin, BaseTemplateNameMixin, NextURLMixin, PageObjectMixin)
    └── get_success_url()  [NEW — lifted from MVPModelFormBase]
        Priority: validated URL → shorthand (if crud_views present) → super()
    └── get_context_data() [MODIFIED — preserves shorthand in next_url on re-render]

MVPModelFormBase(MVPFormBase)
    └── get_url_kwargs()   # extends base: adds pk fallback after creation (existing)

MVPFormView(MVPFormBase, generic.FormView)
    └── inherits get_success_url() from MVPFormBase [gains shorthand resolution via this feature]

MVPCreateView(MVPModelFormBase, generic.CreateView)   [no change]
MVPUpdateView(MVPModelFormBase, generic.UpdateView)   [no change]
MVPDeleteView(MVPModelFormBase, generic.DeleteView)   [no change]
```

---

## `next_url` State Machine

The `next_url` context variable transitions through these states during a typical form flow:

```
GET (initial render)
  next=<safe-url>     → next_url = "/safe/path/"       # validated URL
  next=list           → next_url = "list"               # CRUD shorthand [NEW in this feature]
  next=<external>     → next_url = None                 # rejected (+ DEBUG log)
  next absent/empty   → next_url = None

POST (failed validation — re-render)
  next=<safe-url>     → next_url = "/safe/path/"       # preserved
  next=list           → next_url = "list"               # preserved [NEW — was None before]
  next=<external>     → next_url = None                 # rejected
  next absent/empty   → next_url = None

POST (successful submission)
  next=<safe-url>     → redirect to "/safe/path/"      # priority 1
  next=list           → redirect to resolved list URL  # priority 2 shorthand
  next absent/unsafe  → redirect to success_url        # priority 3
  no success_url set  → redirect to resoluve_crud_url("list")     # priority 4 fallback
```

---

## Redirect Priority Chain (get_success_url)

```
Priority 1 — Validated same-origin next URL
  → NextURLMixin.get_next_url() returns a non-None URL
  → Return immediately

Priority 2 — CRUD action shorthand
  → next POST value is in self.crud_views keys
  → self.resolve_crud_url(next_key) returns a non-empty URL
  → Return immediately
  → Silently skipped when crud_views is unavailable (MVPFormView with no model)
  → Silently skipped when resolution fails (permission denied, no object)

Priority 3 — Configured success URL
  → super().get_success_url() (Django FormMixin) returns self.success_url
  → Only reached in MVPModelFormBase via try/except ImproperlyConfigured

Priority 4 — Built-in fallback
  → self.resoluve_crud_url("list")  (MVPModelFormBase only)
```

---

## Changes to Existing Methods

| Method | Class | Change Type | Description |
|--------|-------|-------------|-------------|
| `get_next_url()` | `NextURLMixin` | Modified | Add `logger.warning` when candidate is rejected and `settings.DEBUG` is True |
| `get_context_data()` | `MVPFormBase` | Modified | After `super()` injects `next_url`, preserve raw shorthand when `next_url` is `None` and raw value is a recognized CRUD shorthand |
| `get_success_url()` | `MVPFormBase` | New | Lifted from `MVPModelFormBase`; handles URL validation, CRUD shorthand, then delegates to `super()` |
| `get_success_url()` | `MVPModelFormBase` | Modified | Wraps `super()` call in `try/except ImproperlyConfigured`; falls back to `self.resoluve_crud_url("list")` |

---

## Invariants

- `get_next_url()` ALWAYS returns either a validated same-origin URL string or `None`. It NEVER returns a CRUD shorthand.
- `next_url` in template context may hold a CRUD shorthand string (e.g., `"list"`) — this is intentional for round-trip preservation.
- `get_success_url()` ALWAYS returns a non-empty string. It NEVER raises `ImproperlyConfigured` to the caller.
- Logging is a side-effect only; it never influences the return value or raises.
