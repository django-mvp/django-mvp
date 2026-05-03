# API Contract: ModelInfoMixin

**Branch**: `005-model-resolution-mixin` | **Date**: 2026-05-03
**Module**: `mvp.views.base` (canonical import)
**Re-exported from**: `mvp.views.detail` (backward-compatible); `mvp.views` (top-level package)

---

## Overview

`ModelInfoMixin` is a view mixin that resolves the Django model class for any model-driven view and exposes human-readable model metadata in the template context. It is the single authoritative source of model identity for all django-mvp model-driven views.

---

## Public Interface

### `get_model_class() -> type`

Resolves the model class for the current view.

**Returns**: The Django model class (may be a proxy model class).

**Raises**: `django.core.exceptions.ImproperlyConfigured` if none of the four strategies can identify a model class.

**Override**: Yes. Subclasses may override this method to implement custom resolution logic. The override is the sole supported extension point; `model_meta` and `get_model_info()` must not be overridden to change resolution behavior.

**Resolution order** (first successful strategy wins):

| Priority | Strategy | Condition |
|---|---|---|
| 1 | `self.model` | Attribute is non-`None` |
| 2 | `self.get_queryset().model` | `get_queryset()` succeeds and result has a `.model` attribute |
| 3 | `self.form_class._meta.model` or `self.get_form_class()._meta.model` | Form class has `_meta.model` (i.e., is a ModelForm) |
| 4 | `self.object.__class__` | `self.object` is non-`None` |

**Exception behavior**: If `get_queryset()` or `get_form_class()` raises any exception during resolution, that exception is silenced and the next strategy is attempted. Exceptions raised by a developer-provided `get_model_class()` override are **not** silenced.

---

### `model_meta` (property)

Returns `get_model_class()._meta` — the Django model `Options` object.

**Returns**: `django.db.models.options.Options`

**Consumed by**: `CRUDDirectoryMixin` (URL generation), `PageObjectMixin` (CSS class, list title, breadcrumbs).

**Note**: `model_meta` is a cached property in the current implementation. Implementers must not rely on re-evaluation within the same request.

---

### `get_model_info() -> dict`

Returns a plain dict of human-readable model metadata for use in templates.

**Returns**:

```python
{
    "verbose_name": str,        # model._meta.verbose_name
    "verbose_name_plural": str, # model._meta.verbose_name_plural
    "app_label": str,           # model._meta.app_label
    "model_name": str,          # model._meta.model_name (lowercase)
}
```

The model class is **not** included. Python consumers that require the class must call `get_model_class()`.

---

### `get_context_data(**kwargs) -> dict`

Injects model metadata into the template context.

**Context key**: `model_info`
**Value**: Return value of `get_model_info()`.

**Stability guarantee**: The `model_info` key name is stable and will not change in minor releases. Templates may rely on `{{ model_info.verbose_name }}`, `{{ model_info.verbose_name_plural }}`, `{{ model_info.app_label }}`, and `{{ model_info.model_name }}` without version guards.

---

## Error Contract

When no model can be resolved:

- **Error type**: `django.core.exceptions.ImproperlyConfigured`
- **Message format**: `"{ClassName} inherits from \`ModelInfoMixin\` but could not determine a model class. Set \`model\`, \`queryset\`, use a ModelForm \`form_class\` or override the \`get_model_class()\` method."`
- **Guaranteed content**: the view's class name, and a description of each supported configuration option.

---

## Import Paths

| Import path | Status |
|---|---|
| `from mvp.views.base import ModelInfoMixin` | Canonical — preferred |
| `from mvp.views.detail import ModelInfoMixin` | Backward-compatible re-export — supported |
| `from mvp.views import ModelInfoMixin` | Top-level package alias — supported |

---

## Stability

This contract is stable as of `005-model-resolution-mixin`. Breaking changes (removal of methods, changes to `model_info` key shape, removal of import paths) require a major version bump.
