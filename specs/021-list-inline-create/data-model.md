# Data Model: List View Inline Create

**Feature**: `021-list-inline-create`
**Date**: 2026-06-02

No new database models are introduced by this feature. All changes are at the view
layer (Python) and template layer (HTML/Cotton).

---

## View API Contract

### `MVPListViewMixin` — New Attributes & Hooks

| Name | Type | Default | Description |
|---|---|---|---|
| `create_form_class` | `type[Form] \| None` | `None` | Django form class for inline object creation. When `None`, inline create is disabled. |
| `create_modal_title` | `str \| None` | `None` | Override the modal title. When `None`, auto-derived as `"Add <verbose_name>"`. |

### `MVPListViewMixin` — New Hook Method

```python
def get_create_form(self) -> Form | None:
    """Instantiate and return the create form, or None if not configured.

    Default implementation returns ``self.create_form_class()`` (unbound).
    Override to pass additional kwargs (e.g. request, user, initial data).

    Returns:
        Form instance, or None when create_form_class is not set.
    """
```

### `MVPListViewMixin` — Context Keys Added

| Context key | Type | Condition | Description |
|---|---|---|---|
| `create_form` | `Form` | `create_form_class` set **and** `has_create_permission` is `True` | Unbound form instance for the inline create modal. |
| `create_modal_title` | `str` | Same as above | Resolved modal title: `create_modal_title` attribute if set, else `"Add <verbose_name>"`. |

---

## Template Contracts

### `list_view.html` — createModal changes

| Attribute | Before | After |
|---|---|---|
| `title` on `<c-form>` | `"Create product"` (hardcoded) | `{{ create_modal_title }}` |
| `action` on `<c-form>` | `{{ directory.create_url }}` | `{{ directory.create_url }}?next={{ request.path }}` |
| Modal conditional guard | Always rendered | Wrapped in `{% if create_form %}` |

### `list/toolbar.html` — no changes

The three-state conditional is already correct:

```
{% if directory.create_url and create_form %}  → modal trigger button
{% elif directory.create_url %}                → link button to create page
{# else: nothing #}
```

---

## Permission Resolution Logic

The permission check added to `MVPListViewMixin.get_context_data()`:

```python
perm = self.has_create_permission
allowed = perm(self.request.user) if callable(perm) else bool(perm)
```

This mirrors `CRUDDirectoryMixin.resolve_crud_url()` exactly, and handles:

- `has_create_permission = False` (default) → form not injected
- `has_create_permission = True` → form injected
- `has_create_permission = staticmethod(lambda user: user.has_perm("app.add_model"))` → evaluated per-request

---

## Invariants

- When `create_form_class` is `None`, `create_form` is never in context regardless of permission.
- When `has_create_permission` is `False` (or callable returning `False`), `create_form` is never in context regardless of `create_form_class`.
- `create_modal_title` is only injected into context when `create_form` is also injected.
- Existing `MVPListViewMixin` subclasses with neither attribute set exhibit zero behavioral difference.
