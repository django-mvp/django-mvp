# Research: Safe Post-Submit Redirect

**Feature**: 008-safe-post-submit-redirect
**Date**: 2026-05-03
**Status**: Complete — all NEEDS CLARIFICATION items resolved

---

## Decision Log

### 1. Canonical URL validation function

**Decision**: `django.utils.http.url_has_allowed_host_and_scheme`

**Rationale**: Already used by `NextURLMixin`. It covers all three classes of unsafe inputs in a single call:

- Cross-origin absolute URLs (different host) → `False`
- Protocol-relative URLs (`//evil.com/…`) → `False` when host differs
- Non-http/https schemes (`javascript:`, `data:`, etc.) → `False`
- Same-host relative paths (`/records/`, `../up`) → `True`
- Empty string → `False` (Django guards this internally)

`require_https=self.request.is_secure()` mirrors the spec clarification: HTTPS is required when the request itself was HTTPS; HTTP-only environments accept same-host `http://` absolute URLs.

**Alternatives considered**:

- `urllib.parse.urlparse` + manual host comparison: more code, more edge cases, misses scheme normalization.
- `django.utils.http.is_safe_url` (deprecated alias): removed in Django 4.0; not available.

---

### 2. Gap analysis: what `NextURLMixin` already satisfies

| FR | Description | Status |
|----|-------------|--------|
| FR-001 | Read `next` from POST (submission) / GET (initial render) | ✅ Implemented |
| FR-002 | Accept relative same-origin paths | ✅ Implemented |
| FR-003 | Reject external-origin absolute URLs | ✅ Implemented |
| FR-004 | Reject protocol-relative URLs | ✅ Implemented |
| FR-005 | Reject unsafe schemes | ✅ Implemented |
| FR-005a | HTTPS mirrors `request.is_secure()` | ✅ Implemented |
| FR-005b | DEBUG-level log on rejection | ❌ **Gap** |
| FR-006 | CRUD shorthand resolution in ALL form views | ❌ **Gap** — `MVPFormView` has none |
| FR-007 | Object-level shorthands use just-saved object | ✅ Implemented (via `get_url_kwargs` override in `MVPModelFormBase`) |
| FR-008 | Unresolvable shorthand falls through silently | ✅ Implemented (via `resolve_crud_url`) |
| FR-009 | Full priority chain: URL → shorthand → success_url → fallback | ❌ **Gap** — step 3 (`success_url`) missing |
| FR-010 | Inject `next_url` into context on GET | ✅ Implemented |
| FR-011 | `next_url = None` when absent/empty/unsafe | ✅ Implemented for safe-URL path |
| FR-012 | Retain `next_url` on failed POST re-render (incl. shorthands) | ❌ **Gap** — shorthand "list" fails `url_has_allowed_host_and_scheme` → lost |

**Four gaps identified**: FR-005b, FR-006, FR-009, FR-012.

---

### 3. Gap detail: FR-005b — DEBUG-level logging

**Decision**: Use Python `logging` module with a module-level logger (`logging.getLogger(__name__)`). Emit `logger.warning(...)` guarded by `settings.DEBUG`. This is consistent with Django's own internal behaviour (Django uses `logger.warning` in `url_has_allowed_host_and_scheme` contexts when DEBUG is on).

**Implementation pattern**:

```python
import logging
logger = logging.getLogger(__name__)

def get_next_url(self):
    ...
    if candidate and url_has_allowed_host_and_scheme(...):
        return candidate
    if candidate and settings.DEBUG:
        logger.warning(
            "next parameter %r rejected (unsafe or cross-origin); "
            "falling back to default destination.",
            candidate,
        )
    return None
```

Note: the log is emitted only when `candidate` is truthy (i.e., `next` was present but rejected). Absent `next` is silent even in DEBUG.

**Alternatives considered**:

- `warnings.warn()`: Not appropriate for security feedback; no Django integration.
- Always-on `logger.warning` (FR option C): Rejected per Q4 clarification — noisy in production.

---

### 4. Gap detail: FR-006 / FR-012 — Context injection and shorthand preservation on re-render

**Problem**: `get_context_data()` calls `get_next_url()` which validates `next` as a URL. CRUD shorthands (e.g. `"list"`, `"detail"`) are not valid URLs and therefore return `None`. On a failed POST re-render, the shorthand is lost from the template context, breaking the round-trip.

**Decision**: Extend `get_context_data()` to expose the raw `next` value when it is a recognized CRUD shorthand. `next_url` in context will hold:

1. A validated same-origin URL (current behaviour), or
2. A recognized CRUD shorthand string (new), or
3. `None` (current behaviour for absent/empty/rejected values)

The template treats `next_url` as an opaque string to embed in a hidden field — it does not distinguish between a path and a shorthand.

**Implementation pattern** (on `MVPFormBase` or `MVPModelFormBase`):

```python
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    # super() already set context["next_url"] via NextURLMixin
    # If it's None, check whether the raw next value is a CRUD shorthand
    if context.get("next_url") is None:
        raw = (
            self.request.POST.get("next")
            if self.request.method == "POST"
            else self.request.GET.get("next")
        )
        if raw and hasattr(self, "crud_views") and raw in self.crud_views:
            context["next_url"] = raw
    return context
```

This keeps `NextURLMixin.get_next_url()` pure (URL validation only) and adds shorthand preservation only where CRUD resolution is available (model form views).

**Alternatives considered**:

- Modify `get_next_url()` to also accept shorthands: mixes URL validation with CRUD knowledge; violates single-responsibility.
- A separate `get_next_url_for_context()` method: extra surface area for minimal gain.

---

### 5. Gap detail: FR-009 step 3 — `success_url` in priority chain

**Decision**: Insert `super().get_success_url()` (Django's `FormMixin.get_success_url()`) as step 3 in the priority chain of `MVPModelFormBase.get_success_url()`, before falling back to `self.resoluve_crud_url("list")`. Guard with `try/except ImproperlyConfigured` since Django raises that when `success_url` is not set.

**Current chain**: validated URL → shorthand → `self.resoluve_crud_url("list")`
**Target chain**: validated URL → shorthand → `success_url` → `self.resoluve_crud_url("list")`

**Implementation pattern**:

```python
from django.core.exceptions import ImproperlyConfigured

def get_success_url(self):
    if next_url := self.get_next_url():
        return next_url
    next_key = self.request.POST.get("next")
    if next_key and next_key in self.crud_views:
        if url := self.resolve_crud_url(next_key):
            return url
    try:
        return super().get_success_url()  # Django FormMixin — uses self.success_url
    except ImproperlyConfigured:
        pass
    return self.self.resoluve_crud_url("list")
```

**Alternatives considered**:

- Check `self.success_url` directly: bypasses the MRO and misses potential overrides in subclasses.
- Leave current behaviour unchanged and add `success_url` only in tasks: violates FR-009 directly.

---

### 6. Gap detail: FR-006 scope — shorthand resolution in `MVPFormView`

**Decision**: Move shorthand resolution logic up from `MVPModelFormBase.get_success_url()` to `MVPFormBase.get_success_url()`. In `MVPFormBase`, attempt shorthand resolution only when `hasattr(self, 'crud_views')` (i.e., `CRUDDirectoryMixin` is in the MRO). If not, silently skip. `MVPModelFormBase` inherits this behaviour and adds the `success_url` → `self.resoluve_crud_url("list")` fallback chain.

**Implementation pattern** (on `MVPFormBase`):

```python
def get_success_url(self):
    if next_url := self.get_next_url():
        return next_url
    if hasattr(self, "crud_views"):
        next_key = self.request.POST.get("next")
        if next_key and next_key in self.crud_views:
            if url := self.resolve_crud_url(next_key):
                return url
    return super().get_success_url()  # FormMixin uses self.success_url
```

`MVPModelFormBase.get_success_url()` then wraps the `super().get_success_url()` in the `try/except ImproperlyConfigured` guard that falls back to `resoluve_crud_url("list")`.

**Alternatives considered**:

- Keep resolution only in `MVPModelFormBase`: violates Q2 clarification that all form views should attempt shorthand resolution.
- Duplicate the shorthand block in both `MVPFormBase` and `MVPModelFormBase`: violates DRY.

---

### 7. Test approach

**Decision**: `RequestFactory` for unit tests of `NextURLMixin` and `get_success_url()`; Django `Client` for integration tests that exercise the full request-response cycle (form submit → redirect). Playwright E2E for the "create with ?next=list → redirected to list" story.

**Rationale**: Consistent with the approach used across the test suite (`test_base.py`, `test_crud_directory_mixin.py`, `test_delete_view.py`). `RequestFactory` avoids URL routing overhead for mixin unit tests; `Client` is used only where the full response is needed.

Test file location: `tests/test_views/test_edit_view.py` — mirrors `mvp/views/edit.py` per Principle I.
