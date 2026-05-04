# Data Model: Form View Base Classes (009-form-view-base)

This feature introduces no new database models. The "entities" are Python view base
classes that form the inheritance layer beneath all form views in the package.

---

## Class Hierarchy

```
MVPFormBase
├── Inherits: SuccessMessageMixin (Django), BaseTemplateNameMixin, NextURLMixin, PageObjectMixin
├── Direct subclasses: MVPFormView (concrete), MVPModelFormBase (abstract)
│
MVPModelFormBase
├── Inherits: MVPFormBase
└── Direct subclasses: MVPCreateView, MVPUpdateView, MVPDeleteView (all concrete)
```

---

## Entity: `MVPFormBase`

**Location**: `mvp/views/edit.py`
**Role**: Shared foundation for all form views. Not a concrete view — must be combined
with a Django generic view class. Provides layout, success message wiring, and the
post-submit redirect priority chain.

### Class Attributes

| Attribute | Value | Description |
|-----------|-------|-------------|
| `base_template_name` | `"form_view.html"` | Fallback template appended by `BaseTemplateNameMixin.get_template_names()` |
| `page_class` | `"mvp-form-page"` | CSS class injected into `context["page"]["class"]` by `PageMixin` |

### Methods

#### `get_next_url() → str | None`

Extends `NextURLMixin.get_next_url()` with CRUD action shorthand resolution.

**Priority**:
1. If the raw `next` candidate matches a key in `self.crud_views`, resolve it via
   `resolve_crud_url(candidate)` and return the URL directly (bypasses open-redirect
   validation — resolved URLs are always same-origin).
2. Otherwise, delegate to `NextURLMixin.get_next_url()` for standard safe-URL
   validation.

**Returns**: Resolved URL string, or `None` when absent/unsafe/unresolvable.

#### `get_success_url() → str`

Post-submit redirect destination using the priority chain:

1. `get_next_url()` — validated `next` URL or resolved CRUD shorthand.
2. `str(self.success_url)` — if set and truthy.
3. **Raises `ImproperlyConfigured`** — when neither is present.

**Raises**: `ImproperlyConfigured` — when no redirect destination is configured.

---

## Entity: `MVPModelFormBase`

**Location**: `mvp/views/edit.py`
**Role**: Extends `MVPFormBase` with model-aware success message interpolation and
an automatic list-view fallback in the redirect chain. Serves as the base for
`MVPCreateView`, `MVPUpdateView`, and `MVPDeleteView`.

### Methods

#### `get_success_message(cleaned_data) → str`

Interpolates `success_message` with:
- All keys from `cleaned_data` (form field values, if present).
- `%(verbose_name)s` → `self.model_meta.verbose_name`.

Uses `collections.defaultdict(str, ...)` so that field-value placeholders present in
`success_message` but absent from `cleaned_data` (e.g. `%(name)s` on a delete view
where `cleaned_data = {}`) are replaced with `""` instead of raising `KeyError`.

**Parameters**:
- `cleaned_data (dict)`: Form `cleaned_data` dict. May be empty (e.g. on delete views).

**Returns**: Interpolated message string.

#### `get_url_kwargs(action: str) → dict | None`

Extends `CRUDDirectoryMixin.get_url_kwargs()` with a post-create pk fallback.

After a create operation, `self.kwargs` is still empty (no pk in the URL at request
time), but `self.object.pk` is now available. This method checks `self.object.pk` when
`super().get_url_kwargs(action)` returns `None`, enabling CRUD shorthand redirects to
pk-requiring views (e.g. `?next=detail`) immediately after creation.

**Returns**: URL kwargs dict, or `None` to suppress the action.

#### `get_success_url() → str`

Extends `MVPFormBase.get_success_url()` with a built-in list-view fallback:

1–2. Inherited from `MVPFormBase` (next URL → `success_url`).
3. `resolve_crud_url("list")` — built-in fallback when neither of the above is set.
4. **Raises `ImproperlyConfigured`** — when the list URL cannot be resolved (e.g.
   `crud_views` not configured or no list permission), symmetric with FR-005.

**Raises**: `ImproperlyConfigured` — when no redirect destination is resolvable.

---

## Validation Rules

| Rule | Where Enforced |
|------|----------------|
| `success_url` must be truthy when used | `MVPFormBase.get_success_url()` — falsy values are treated as absent |
| `next` parameter must be same-origin | `NextURLMixin.get_next_url()` (spec 008) |
| CRUD shorthands bypass URL validation | `MVPFormBase.get_next_url()` — resolved URLs are always same-origin |
| Missing `%(key)s` placeholders → `""` | `MVPModelFormBase.get_success_message()` via `defaultdict(str)` |
| No redirect destination configured → error | `MVPFormBase.get_success_url()` / `MVPModelFormBase.get_success_url()` |

---

## State Transitions

The redirect priority chain can be thought of as a three-step waterfall:

```
POST submission → form_valid() → get_success_url()
                                      │
                               ┌──────▼──────┐
                               │ get_next_url │ ── valid? → redirect
                               └──────┬──────┘
                                      │ None
                               ┌──────▼──────┐
                               │ success_url  │ ── truthy? → redirect
                               └──────┬──────┘
                                      │ falsy/absent
                      ┌───────────────▼──────────────────┐
                      │ [MVPModelFormBase only]           │
                      │ resolve_crud_url("list")          │ ── URL? → redirect
                      └───────────────┬──────────────────┘
                                      │ None
                               ┌──────▼──────────────┐
                               │ ImproperlyConfigured │
                               └─────────────────────┘
```
