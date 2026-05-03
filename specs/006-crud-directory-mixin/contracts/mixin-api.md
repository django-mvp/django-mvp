# API Contract: CRUDDirectoryMixin

**Branch**: `006-crud-directory-mixin` | **Date**: 2026-05-03
**Module**: `mvp.views.detail`

This document defines the stable public API contract for `CRUDDirectoryMixin`. Any change to the items listed here constitutes a breaking change and requires a version bump and migration note.

---

## Class Attributes (Public Configuration)

| Attribute | Type | Default | Stable |
|---|---|---|---|
| `crud_views` | `dict[str, str]` | `MVP_DEFAULT_VIEW_NAMES` | ✅ |
| `directory` | `list[str]` | `[]` | ✅ |
| `has_list_permission` | `bool \| callable` | `False` | ✅ |
| `has_detail_permission` | `bool \| callable` | `False` | ✅ |
| `has_create_permission` | `bool \| callable` | `False` | ✅ |
| `has_update_permission` | `bool \| callable` | `False` | ✅ |
| `has_delete_permission` | `bool \| callable` | `False` | ✅ |

**Removed** (was present in experimental implementation; not part of the stable contract):

- `has_read_permission` — replaced by `has_detail_permission`

---

## Public Methods

### `get_url_kwargs(action: str) -> dict | None`

Returns the URL kwargs to use when reversing the URL for `action`.

- **Default for `"list"` and `"create"`**: `{}` — no kwargs; collection-level URLs work without an object.
- **Default for all other actions** (including custom ones): `dict(self.kwargs) or None` — all captured request URL kwargs, or `None` when there are none.
- **Override to**: branch on `action` to control kwargs per action for nested URL patterns or custom routing.
- **Return `None`**: suppresses the action silently (no URL generated, no error raised).

**Contract**:

- Return value MUST be a `dict` or `None`.
- `{}` (empty dict) is a valid return: the URL is reversed with no kwargs.
- `None` causes the action to be excluded from `directory` regardless of permission.
- Callable permission exceptions propagate; kwargs-return exceptions propagate.
- Subclass overrides MUST call `super().get_url_kwargs(action)` when delegating to the default.

**Example override for nested routes**:

```python
def get_url_kwargs(self, action: str) -> dict | None:
    if action in {"list", "create"}:
        return {"project_pk": self.kwargs["project_pk"]}
    pk = self.kwargs.get("pk")
    if pk is None:
        return None
    return {"project_pk": self.kwargs["project_pk"], "pk": pk}
```

### `get_directory() -> dict[str, str]`

Resolves all actions listed in `self.directory` and returns a mapping of `{action}_url` keys to resolved URL strings.

**Contract**:

- Return value is always a `dict` (never `None`).
- Only actions listed in `self.directory` are processed.
- Keys are of the form `"{action}_url"` (e.g. `"list_url"`, `"update_url"`).
- An action is excluded from the result when:
  - Its `has_{action}_permission` attribute is absent, `False`, or a callable returning `False`.
  - `get_url_kwargs(action)` returns `None`.
- An action is included when its permission evaluates to truthy and the URL can be reversed.

### `get_context_data(**kwargs) -> dict`

Standard Django CBV method. Adds `"directory"` key to the template context.

**Contract**:

- The `"directory"` key is ALWAYS present in the returned context (even when the dict is empty).
- Value is the result of `get_directory()`.

---

## Internal Methods (Not Part of Public API)

These methods are implementation details. Do NOT override them in subclasses.

| Method | Purpose |
|---|---|
| `_get_view_name(action: str) -> str` | Looks up and formats the URL name for an action from `crud_views`. Raises `ValueError` for unknown action names. |
| `_resolve_directory_url(action: str) -> str \| None` | Resolves a single action URL applying permission gate and kwargs dispatch. Returns `None` when excluded. |

---

## Template Context Contract

The `directory` variable is injected into the template context by `get_context_data()`.

**Shape**: `dict[str, str]` — always a dict, never `None`, may be empty.

**Key format**: `"{action}_url"` where `action` is one of the values in `self.directory`.

**Presence**: A key is present if and only if:

1. The action is listed in `self.directory`.
2. The corresponding `has_{action}_permission` evaluates to truthy.
3. `get_url_kwargs(action)` returns a value that is not `None`.

**Example**:

```python
# directory = ["list", "update", "delete"]
# has_list_permission = True, has_update_permission = True, has_delete_permission = False
# On a detail view with pk=42
{
    "list_url":   "/products/",
    "update_url": "/products/42/edit/",
    # delete_url absent (permission denied)
}
```

---

## Permission Callable Interface

When a `has_{action}_permission` attribute is callable, it is invoked as:

```python
result = has_{action}_permission(request.user)
```

- **Argument**: `request.user` (Django `User` instance or `AnonymousUser`)
- **Return**: any truthy/falsy value (coerced to `bool` internally)
- **Exception handling**: exceptions propagate — they are NOT silently swallowed

---

## Invariants

1. `directory` context key is always a `dict` and always present — even when empty.
2. `get_url_kwargs(action)` returning `None` suppresses that action’s URL silently (no error).
3. `get_url_kwargs(action)` returning `{}` (empty dict) proceeds with URL reversal using no kwargs — the action is NOT suppressed.
4. Unknown action names in `directory` raise `ValueError` (not silently suppressed).
5. Permission callable exceptions propagate (not silently suppressed).
6. URL reversal errors (`NoReverseMatch`) propagate — they signal genuine misconfiguration.
