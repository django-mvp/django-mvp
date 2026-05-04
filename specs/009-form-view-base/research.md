# Research: Form View Base Classes (009-form-view-base)

## Scope

This document records all investigation findings for `MVPFormBase` and `MVPModelFormBase`
in `mvp/views/edit.py`, mapping each functional requirement in the spec to the current
implementation state.

---

## FR-by-FR Implementation Audit

### FR-001 — `form_view.html` fallback template

**Status: COMPLETE**

`MVPFormBase` sets `base_template_name = "form_view.html"`. `BaseTemplateNameMixin.get_template_names()`
appends this as the last candidate, giving every subclass the shared layout with no extra
configuration required.

### FR-002 — Success message machinery

**Status: COMPLETE**

`MVPFormBase` inherits from `SuccessMessageMixin` (Django built-in). Subclasses set
`success_message` to activate message display after `form_valid()`.

### FR-003 — `mvp-form-page` scoped CSS class

**Status: COMPLETE**

`MVPFormBase` sets `page_class = "mvp-form-page"`. `PageMixin` injects this into
`context["page"]["class"]`.

### FR-004 — Redirect priority chain (next → success_url)

**Status: COMPLETE**

`MVPFormBase.get_success_url()`:
1. Calls `get_next_url()` (validates `next` parameter and resolves CRUD shorthands).
2. Falls back to `str(self.success_url)` if set and truthy.

### FR-005 — `ImproperlyConfigured` for `MVPFormBase` misconfiguration

**Status: COMPLETE**

When neither `next` nor `success_url` is present, `MVPFormBase.get_success_url()` raises:

```python
raise ImproperlyConfigured(
    f"'{self.__class__.__name__}' must define 'success_url' or override 'get_success_url()'."
)
```

### FR-006 — CRUD action shorthand resolution

**Status: COMPLETE**

`MVPFormBase.get_next_url()` checks whether the raw `next` candidate is a key in
`self.crud_views` and resolves it via `resolve_crud_url()`. Unknown shorthands fall
through to base-class URL validation silently.

### FR-007 — `%(verbose_name)s` interpolation + empty string for missing placeholders

**Status: INCOMPLETE — code change required**

Current implementation:

```python
def get_success_message(self, cleaned_data):
    return self.success_message % {
        **cleaned_data,
        "verbose_name": self.model_meta.verbose_name,
    }
```

**Gap**: `%(verbose_name)s` interpolation works correctly for create/update views where
`cleaned_data` is populated. However, on `MVPDeleteView` the delete confirmation form
has no data fields, so `cleaned_data = {}`. If a developer puts `%(name)s` in a
delete-view `success_message`, Python's `%` operator raises `KeyError` because `name`
is absent from the dict.

**Decision**: Substitute `""` (empty string) for missing field placeholders, using
`collections.defaultdict(str, ...)`. This is safe, backward-compatible, and consistent
with the clarification accepted in session 2026-05-04.

**Rationale**: `defaultdict(str, mapping)` returns `str()` (i.e. `""`) for any key
not present in the mapping. The `%` operator on strings calls `mapping.__getitem__()`,
which `defaultdict` overrides to trigger the default factory. All existing success
messages (`%(verbose_name)s only`) are unaffected; `verbose_name` is always injected
explicitly.

**Alternatives considered**:
- `string.Template.safe_substitute()` — requires changing the format string syntax from
  `%(name)s` to `$name`; would break all existing `success_message` strings. Rejected.
- `try/except KeyError` — catches and swallows the error but doesn't substitute; the
  output would be a malformed string. Rejected.
- Raise `KeyError` as-is — the spec explicitly says no error should be raised for
  missing field placeholders on delete views. Rejected.

### FR-008 — List-view fallback in `MVPModelFormBase` + `ImproperlyConfigured` when unresolvable

**Status: INCOMPLETE — code change required**

Current implementation:

```python
def get_success_url(self):
    try:
        return super().get_success_url()
    except ImproperlyConfigured:
        return self.resolve_crud_url("list")
```

**Gap**: When `resolve_crud_url("list")` returns `None` (e.g. no `crud_views`
configured, no list permission), the method returns `None`. Django then uses `None` as
a redirect URL, producing a cryptic `TypeError` or `ValueError` at response time — not
`ImproperlyConfigured`, and not a named, actionable error.

**Decision**: Raise `ImproperlyConfigured` when `resolve_crud_url("list")` returns
`None`, symmetric with FR-005. This is the clarification accepted in session 2026-05-04.

**Rationale**: FR-005 establishes the principle that misconfiguration produces a named,
actionable error. `MVPModelFormBase` should honour the same principle. Returning `None`
defeats the intent and produces harder-to-diagnose bugs.

**Alternatives considered**:
- Return `None` and let Django fail — matches current behaviour; error message is cryptic
  and points to framework internals, not the misconfiguration site. Rejected.
- Raise `ValueError` — would be inconsistent with FR-005 which uses
  `ImproperlyConfigured`. Rejected.

### FR-009 — Post-create pk fallback in `MVPModelFormBase`

**Status: COMPLETE**

`MVPModelFormBase.get_url_kwargs()` checks `self.object.pk` after the object is saved,
so CRUD shorthand redirects that require a pk (e.g. `?next=detail`) work on create
views where `self.kwargs` is still empty at request time.

### FR-010 — Clean composition with Django generic views

**Status: COMPLETE**

`MVPCreateView`, `MVPUpdateView`, `MVPDeleteView` all inherit from `MVPModelFormBase` +
the corresponding Django generic view. All existing tests (35 passing) confirm the
composition does not break Django's form processing or validation.

---

## Test Coverage Audit

### Existing tests (`tests/test_views/test_edit_view.py`) — 35 tests, all passing

Covered:
- `NextURLMixin.get_next_candidate()` — GET/POST behavior, override contract
- `NextURLMixin.get_next_url()` — safe URLs, cross-origin rejection, empty string
- `MVPFormBase.get_success_url()` — next URL, success_url, CRUD shorthands
- `MVPModelFormBase.get_success_url()` — list fallback, shorthand resolution
- `MVPFormBase` `ImproperlyConfigured` is implicitly covered via the `MVPFormView`
  test with `success_url` set (happy path only)
- Open-redirect protection logging (DEBUG on/off)

**Gaps — tests needed for this spec**:

| Test ID | Description |
|---------|-------------|
| T-FM-001 | `get_success_message()` with `%(verbose_name)s` on create view → verbose_name resolved |
| T-FM-002 | `get_success_message()` on delete view with `%(name)s` → empty string, no error |
| T-FM-003 | `get_success_message()` with combined `%(verbose_name)s` + `%(name)s` on update view → both resolved |
| T-FM-004 | `MVPModelFormBase.get_success_url()` when `resolve_crud_url("list")` returns `None` → `ImproperlyConfigured` |
| T-FM-005 | `MVPFormBase.get_success_url()` with no next and no success_url → `ImproperlyConfigured` (explicit, not just implied) |
| T-FM-006 | `MVPFormBase.base_template_name` is `"form_view.html"` |
| T-FM-007 | `MVPFormBase.page_class` is `"mvp-form-page"` |

---

## Dependency Confirmation

| Dependency | Status |
|------------|--------|
| spec 007 — Object Page Foundation (`PageObjectMixin`, `CRUDDirectoryMixin`) | ✅ In place |
| spec 008 — Safe Post-Submit Redirect (`NextURLMixin`, open-redirect protection) | ✅ In place |
| Django `SuccessMessageMixin` | ✅ Already composed into `MVPFormBase` |
| `form_view.html` template | ✅ Exists in `mvp/templates/` |

---

## Conclusions

Two code changes are required:

1. **`MVPModelFormBase.get_success_message()`** — wrap the interpolation dict in
   `collections.defaultdict(str, ...)` so missing field placeholders resolve to `""`
   instead of raising `KeyError`.

2. **`MVPModelFormBase.get_success_url()`** — after catching `ImproperlyConfigured`
   from `super()`, check whether `resolve_crud_url("list")` returned `None` and raise
   `ImproperlyConfigured` with a clear message if so.

All other FRs are already satisfied by the existing implementation. The test suite
needs seven new unit tests targeting the two new behaviors and explicit coverage of
class-level attribute contracts.
