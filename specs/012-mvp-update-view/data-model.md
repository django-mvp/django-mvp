# Data Model: MVPUpdateView

**Feature**: `012-mvp-update-view` | **Date**: 2026-05-05

No new Django models, fields, or migrations are introduced by this feature.
All data entities are pre-existing; this section documents their roles as
they relate to the implementation.

---

## Entities

### MVPUpdateView (modified)

**File**: `mvp/views/edit.py`

Concrete view class combining `MVPModelFormBase` with Django's `generic.UpdateView`.

| Attribute / Method | Current state | Target state |
|--------------------|--------------|-------------|
| `page_title` | `_("Update Entry")` (static) | `_("Update %(verbose_name)s")` (interpolation template) |
| `page_icon` | `"edit"` | unchanged |
| `page_class` | `"mvp-form-page mvp-update-page"` | unchanged |
| `success_message` | `_("%(verbose_name)s successfully updated.")` | unchanged |
| `get_breadcrumbs()` | Middle item `href` = `self.object.get_absolute_url()` | Middle item `href` = `self.resolve_crud_url("detail")` |
| `get_delete_url()` | Fully implemented | unchanged |
| `get_context_data()` | Adds `delete_url` | unchanged |
| Class docstring | Single line | Principle XII-compliant (Config block, Override hooks, example) |

### form_view.html (modified)

**File**: `mvp/templates/form_view.html`

| Element | Current state | Target state |
|---------|--------------|-------------|
| Delete button guard | `{% if object %}` | `{% if delete_url %}` |

**Rationale**: On an update page, `object` is always set, making the current
guard ineffective at hiding the button when no delete view is registered.

### Breadcrumb item (runtime value, no model)

The three-level breadcrumb produced by `get_breadcrumbs()`:

| Index | `text` | `href` |
|-------|--------|--------|
| 0 | `self.get_list_title()` (e.g., `"Products"`) | `resolve_crud_url("list")` — `None` when list inaccessible |
| 1 | `str(self.object)` | `resolve_crud_url("detail")` — `None` when detail inaccessible |
| 2 | `self.get_page_title()` (e.g., `"Update Product"`) | absent (current page) |

When `href` is `None` or `""`, the Cotton breadcrumbs component renders a
`<span>` instead of an `<a>` — no Python guard required.

---

## Validation Rules

- `page_title` MUST contain `%(verbose_name)s` or be a plain string (no other
  format keys are injected by `get_page_title()`).
- `delete_url` is always a `str`; empty string signals "no delete available".
  The template guard `{% if delete_url %}` treats empty string as falsy.

---

## State Transitions

None — this feature adds no state machine behaviour. The update lifecycle is
Django's standard `generic.UpdateView` POST → validate → save → redirect.
