# Data Model: MVPCreateView — Zero-Config Model Create View

**Feature**: `specs/011-mvp-create-view/spec.md`
**Date**: 2026-05-05
**Derived from**: `research.md` (all unknowns resolved)

---

## Entities Modified

### `MVPCreateView` (modified — `mvp/views/edit.py`)

**Current state** (stub):

```python
class MVPCreateView(MVPModelFormBase, generic.CreateView):
    page_icon = "add"
    page_title = _("Create Entry")          # ← static, model-agnostic
    page_class = "mvp-form-page mvp-create-page"
    success_message = _("%(verbose_name)s successfully created.")
    # No get_page_title(), no get_success_message()
```

**Target state** (after this feature):

```python
class MVPCreateView(MVPModelFormBase, generic.CreateView):
    page_icon = "add"
    page_class = "mvp-form-page mvp-create-page"
    success_message = _("%(verbose_name)s successfully created.")
    # page_title removed → falls back to "" (PageMixin default)

    def get_page_title(self) -> str:
        """Return a model-aware page title, or the override if set."""
        if self.page_title:
            return str(self.page_title)
        return f"Create {self.model_meta.verbose_name.title()}"

    def get_success_message(self, cleaned_data: dict) -> str:
        """Interpolate success_message with title-cased verbose_name."""
        data = defaultdict(str, cleaned_data)
        data["verbose_name"] = self.model_meta.verbose_name.title()
        return self.success_message % data
```

**Changes from stub**:

| Attribute/Method | Before | After | Reason |
|-----------------|--------|-------|--------|
| `page_title` | `_("Create Entry")` | *(removed)* | Static; replaced by `get_page_title()` |
| `get_page_title()` | Inherited from `PageMixin` (returns `""`) | New override — model-aware | FR-001 |
| `get_success_message()` | Inherited from `MVPModelFormBase` (lowercase verbose_name) | New override — title-cases verbose_name | FR-004 |

---

## Inheritance Chain (unchanged)

```
MVPCreateView
  ├── MVPModelFormBase
  │     ├── MVPFormBase
  │     │     ├── SuccessMessageMixin   (Django)
  │     │     ├── BaseTemplateNameMixin
  │     │     ├── NextURLMixin
  │     │     └── PageObjectMixin
  │     │           ├── CRUDDirectoryMixin → ModelInfoMixin  (provides model_meta)
  │     │           └── PageMixin  (provides page_title="", get_page_title(), get_breadcrumbs())
  │     └── get_success_message()  ← overridden in MVPCreateView
  └── generic.CreateView  (Django)
```

---

## Behaviour Contracts

### `get_page_title()`

| Scenario | Input (`self.page_title`) | Output |
|----------|--------------------------|--------|
| No override (default) | `""` (falsy) | `"Create Product"` (for `Product` model) |
| Multi-word verbose_name | `""` (falsy) | `"Create Order Line"` (for `verbose_name = "order line"`) |
| Developer sets `page_title` | `"Add a new product"` (truthy) | `"Add a new product"` |
| Developer sets `page_title = _("Add Product")` | lazy string (truthy) | `"Add Product"` |
| Developer sets `page_title = ""` | `""` (falsy) | `"Create Product"` (falls back to derived) |

### `get_success_message()`

| Scenario | `success_message` template | `cleaned_data` | Output |
|----------|---------------------------|----------------|--------|
| Default message | `"%(verbose_name)s successfully created."` | `{}` | `"Product successfully created."` |
| Custom message with field | `"%(name)s was added."` | `{"name": "Widget"}` | `"Widget was added."` |
| Missing field key | `"%(verbose_name)s %(name)s added."` | `{}` | `"Product  added."` (empty string for missing) |
| `success_message = ""` | `""` | `{}` | `""` (no message) |

---

## Unchanged Entities

The following classes are **not modified** by this feature (FR-010):

| Class | File | Why unchanged |
|-------|------|---------------|
| `MVPFormBase` | `mvp/views/edit.py` | Base class; no create-specific concern |
| `MVPModelFormBase` | `mvp/views/edit.py` | Generic model-form base; `get_success_message()` remains with lowercase verbose_name for UpdateView/DeleteView use |
| `MVPUpdateView` | `mvp/views/edit.py` | Separate view; not affected |
| `MVPDeleteView` | `mvp/views/edit.py` | Separate view; not affected |
| `MVPFormView` | `mvp/views/edit.py` | Non-model form view; not affected |
| `PageObjectMixin` | `mvp/views/base.py` | Provides `get_breadcrumbs()` already correct for create |
| All templates | `mvp/templates/` | No template changes needed |

---

## Test Entities

### Tests to relocate (existing)

`TestGetSuccessMessage` in `tests/test_views/test_edit_view.py` uses a `MVPCreateView`
subclass as the test vehicle for `MVPModelFormBase.get_success_message()` behaviour.
These three tests will fail after the `MVPCreateView` override and must be moved to a
new class that uses `MVPUpdateView` (or a direct `MVPModelFormBase` subclass) instead:

- `test_verbose_name_only_resolves`
- `test_missing_field_placeholder_substitutes_empty_string`
- `test_field_value_and_verbose_name_both_resolve`

### New test classes

| Class | Tests | Covers |
|-------|-------|--------|
| `TestMVPCreateViewPageTitle` | ~5 parametrised unit tests | `get_page_title()` — default, multi-word verbose_name, override, empty string, lazy string |
| `TestMVPCreateViewSuccessMessage` | ~3 unit tests | `get_success_message()` — title-cased verbose_name, custom message, missing key |
| `TestMVPCreateViewDefaults` | ~3 unit tests | `page_icon`, `page_class`, and that no `page_title` class attribute is set |
| `TestMVPCreateViewE2E` | 2–3 playwright tests | Full create round-trip: zero-config title, message on redirect, breadcrumb |

**Test file locations**:
- Unit tests: append to `tests/test_views/test_edit_view.py`
- E2E tests: append to `tests/test_views/test_edit_view_e2e.py`
