# Data Model: Model Resolution Mixin

**Branch**: `005-model-resolution-mixin` | **Date**: 2026-05-03

This feature introduces no Django models, no database migrations, and no new data persistence. `ModelInfoMixin` is a pure Python class that resolves a model class from view configuration at request time and injects read-only metadata into the template context.

---

## Entities

### ModelInfoMixin

**What it represents**: A view mixin that encapsulates the logic for determining which Django model class a view is operating on, regardless of how that model was expressed in the view's configuration.

**Module**: `mvp.views.base` (canonical); re-exported from `mvp.views.detail` for backward compatibility.

**Public API**:

| Name | Kind | Description |
|---|---|---|
| `get_model_class()` | Method | Resolves and returns the model class using the four-strategy chain. Override this to supply custom resolution logic. |
| `model_meta` | Property | Returns the `_meta` object of the resolved model class. Consumed by downstream mixins (e.g., `CRUDDirectoryMixin`). |
| `get_model_info()` | Method | Returns the `model_info` dict with four human-readable fields derived from `model_meta`. |
| `get_context_data(**kwargs)` | Method | Injects `model_info` into the template context. |

**Resolution strategy chain** (executed in fixed priority order):

1. **Direct model attribute** — `self.model` is non-None → return it.
2. **Queryset** — call `self.get_queryset()` (exception-silenced); if result has a `.model` attribute → return it.
3. **Form class** — read `self.form_class` or call `self.get_form_class()` (exception-silenced); if result has `_meta.model` → return it.
4. **Object instance** — if `self.object` is non-None → return `self.object.__class__`.
5. **Error** — raise `ImproperlyConfigured` naming the view class and describing all configuration options.

**`model_info` context value shape**:

```python
{
    "verbose_name": str,        # e.g. "product"
    "verbose_name_plural": str, # e.g. "products"
    "app_label": str,           # e.g. "catalogue"
    "model_name": str,          # e.g. "product"
}
```

The model class itself is **not** included in `model_info`. Python consumers that need the class must call `get_model_class()` directly.

---

## State Transitions

Not applicable — `ModelInfoMixin` holds no mutable state and persists nothing. Resolution is a pure function of the view's configuration and the current request-scoped `object` binding.

---

## Relationships to Other Entities

```
ModelInfoMixin
    │
    ├── CRUDDirectoryMixin(ModelInfoMixin)       [mvp.views.detail]
    │       Consumes: model_meta.model_name, model_meta.app_label
    │
    └── PageObjectMixin(CRUDDirectoryMixin, ModelInfoMixin, PageMixin)  [mvp.views.detail]
            Consumes: model_meta.model_name (CSS class), model_meta.verbose_name_plural (list title)
                │
                ├── MVPDetailView          [mvp.views.detail]
                ├── MVPFormBase            [mvp.views.edit]
                ├── MVPModelFormBase       [mvp.views.edit]
                ├── MVPCreateView          [mvp.views.edit]
                ├── MVPUpdateView          [mvp.views.edit]
                └── MVPDeleteView          [mvp.views.edit]
```

All downstream view classes consume model identity exclusively through `model_meta` → `get_model_class()`. No downstream class implements its own independent model resolution (FR-011 verified).
