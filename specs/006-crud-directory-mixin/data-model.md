# Data Model: CRUD Directory Mixin

**Branch**: `006-crud-directory-mixin` | **Date**: 2026-05-03

This feature introduces no Django models, no database migrations, and no new data persistence. `CRUDDirectoryMixin` is a pure Python view mixin that resolves permission-gated CRUD URLs for the current model at request time and injects them into the template context as a `directory` dict.

---

## Entities

### CRUDDirectoryMixin

**What it represents**: A view mixin that declaratively resolves a set of CRUD action URLs for the current model, gates each URL against a per-action permission attribute, and injects the result into the template context under the key `directory`. Downstream templates use the presence or absence of a `{action}_url` key to conditionally render navigation links and action buttons.

**Module**: `mvp.views.detail`
**Inherits from**: `ModelInfoMixin` (supplies `model_meta` for URL name construction)

**Class-level attributes**:

| Attribute | Type | Default | Description |
|---|---|---|---|
| `crud_views` | `dict[str, str]` | `MVP_DEFAULT_VIEW_NAMES` | Maps action names to URL name patterns. Supports `{model_name}` and `{app_name}` substitution tokens. |
| `directory` | `list[str]` | `[]` | Actions to resolve on each request. Only listed actions appear in the `directory` context dict. |
| `has_list_permission` | `bool \| callable` | `False` | Controls whether `list_url` is included. |
| `has_detail_permission` | `bool \| callable` | `False` | Controls whether `detail_url` is included. (Replaces `has_read_permission`.) |
| `has_create_permission` | `bool \| callable` | `False` | Controls whether `create_url` is included. |
| `has_update_permission` | `bool \| callable` | `False` | Controls whether `update_url` is included. |
| `has_delete_permission` | `bool \| callable` | `False` | Controls whether `delete_url` is included. |

**Public methods**:

| Name | Signature | Description |
|---|---|---|
| `get_url_kwargs(action)` | `(str) -> dict \| None` | Returns URL kwargs for reversing the URL for `action`. Default: `{}` for `"list"` and `"create"`; `dict(self.kwargs) or None` for all other actions. Return `None` to suppress an action silently. Override to control kwargs per action for nested URL patterns. |
| `get_directory()` | `() -> dict[str, str]` | Resolves all actions in `self.directory` and returns a dict of `{action}_url` entries for permitted, resolvable actions. |
| `get_context_data(**kwargs)` | standard CBV | Injects `directory` dict into the template context. |

**Internal methods** (not part of the public API; do not override):

| Name | Signature | Description |
|---|---|---|
| `_get_view_name(action)` | `(str) -> str` | Looks up the URL name pattern for `action` in `crud_views` and applies model/app label substitution. Raises `ValueError` for unknown action names. |
| `_resolve_directory_url(action)` | `(str) -> str \| None` | Resolves a single action URL. Returns `None` when permission is denied, kwargs are empty for object-level actions, or no permission attribute exists. |

---

### `directory` context value shape

The `directory` key in the template context is always a `dict`. Keys are present only for actions that resolved successfully (permitted + URL reversible). The dict is always present (never `None`, never absent).

```python
# Example: detail view for Product, all permissions granted
{
    "list_url":   "/products/",
    "detail_url": "/products/42/",
    "update_url": "/products/42/edit/",
    "delete_url": "/products/42/delete/",
}

# Example: list view, read-only user
{
    "list_url": "/products/",
}

# Example: all permissions denied or no directory declared
{}
```

---

### `crud_views` default mapping (`MVP_DEFAULT_VIEW_NAMES`)

```python
MVP_DEFAULT_VIEW_NAMES = {
    "list":   "{model_name}-list",
    "detail": "{model_name}-detail",
    "create": "{model_name}-create",
    "update": "{model_name}-update",
    "delete": "{model_name}-delete",
}
```

URL name substitution: `{model_name}` → `model_meta.model_name`, `{app_name}` → `model_meta.app_label`.

---

### Action Classification

The `get_url_kwargs(action)` default implementation encodes collection vs. object-level behaviour directly. No frozensets or external constants are required.

| Action | Default behaviour in `get_url_kwargs` | Suppressed when `None` returned? |
|---|---|---|
| `detail` | `dict(self.kwargs) or None` | Yes — suppressed on views without URL kwargs |
| `update` | `dict(self.kwargs) or None` | Yes — suppressed on views without URL kwargs |
| `delete` | `dict(self.kwargs) or None` | Yes — suppressed on views without URL kwargs |
| `list` | `{}` (never `None`) | No — always attempted |
| `create` | `{}` (never `None`) | No — always attempted |
| custom | `dict(self.kwargs) or None` | Yes — same as object-level |

Subclasses override `get_url_kwargs(action)` to change this for any or all actions.

---

### Permission attribute resolution

For each action in `directory`, permission is evaluated as follows:

```
perm_attr = getattr(view, f"has_{action}_permission", None)
if perm_attr is None:          → exclude URL (attribute absent = denied)
elif callable(perm_attr):      → perm_attr(request.user) must be True to include
else:                          → bool(perm_attr) must be True to include
```

Callable permission attributes receive `request.user` as their sole argument and must return a boolean.

---

### Relationships to Other Entities

```
ModelInfoMixin                               [mvp.views.base]
    │  Provides: model_meta.model_name, model_meta.app_label
    │
    └── CRUDDirectoryMixin                   [mvp.views.detail]
            Provides: directory context dict
            │
            ├── PageObjectMixin(CRUDDirectoryMixin, PageMixin)    [mvp.views.detail]
            │       Extends: get_list_url(), get_breadcrumbs()
            │       │
            │       ├── MVPDetailView          [mvp.views.detail]
            │       ├── MVPFormBase            [mvp.views.edit]
            │       │       │
            │       │       ├── MVPModelFormBase
            │       │       │       Overrides: get_url_kwargs(action) (CreateView pk fallback)
            │       │       │       │
            │       │       │       ├── MVPCreateView
            │       │       │       ├── MVPUpdateView
            │       │       │       │       get_delete_url() → uses _resolve_directory_url("delete")
            │       │       │       └── MVPDeleteView
            │       │       └── MVPFormView
            │       └── (used by edit views above)
            │
            └── MVPListViewMixin               [mvp.views.list]
                    Inherits: directory resolution for list-page action links
```

---

### Modified entities (not new, but changed by this feature)

| Entity | Change |
|---|---|
| `CRUDDirectoryMixin` | Rename `has_read_permission` → `has_detail_permission`; add `has_list_permission`; remove `_OBJECT_ACTIONS` class attribute; rename `get_lookup_kwargs()` → `get_object_url_kwargs()`; add `get_collection_url_kwargs()`; update `_resolve_directory_url()` to dispatch to correct kwargs getter. |
| `PageObjectMixin` | Remove redundant `ModelInfoMixin` from explicit bases (already inherited via `CRUDDirectoryMixin`). |
| `MVPModelFormBase` | Rename `get_lookup_kwargs()` override → `get_object_url_kwargs()`. |
| `MVPUpdateView.get_delete_url()` | Apply `has_delete_permission` gate by delegating to `_resolve_directory_url("delete")` before appending `?back=...&next=...` params. |
