# Data Model: Object Page Foundation

**Branch**: `007-object-page-foundation` | **Date**: 2026-05-03
**Source**: `mvp/views/detail.py`

This document captures the entities introduced by this feature and their public APIs as they exist in the current implementation (which satisfies all FRs without modification).

---

## Entity 1: PageObjectMixin

**Module**: `mvp.views.detail`
**Public import**: `from mvp.views import PageObjectMixin`

**Purpose**: Shared composition base for all object-level views (detail, create, update, delete). Merges model resolution (`ModelInfoMixin` via `CRUDDirectoryMixin`), permission-gated sibling URL resolution (`CRUDDirectoryMixin`), and page header/breadcrumb rendering (`PageMixin`) into a single inheritable class.

**Class hierarchy**:

```
PageObjectMixin(CRUDDirectoryMixin, PageMixin)
  └── CRUDDirectoryMixin(ModelInfoMixin)
        └── ModelInfoMixin
  └── PageMixin
```

**Class attributes**:

| Attribute | Type | Default | Description |
|---|---|---|---|
| `list_view_title` | `str` | `""` | Override text for the breadcrumb back-link to the list view. When empty, defaults to `verbose_name_plural.title()`. |

**Public methods**:

| Method | Signature | Returns | Description |
|---|---|---|---|
| `get_list_title` | `() → str` | `str` | Returns `list_view_title` or model's plural verbose name, title-cased. |
| `get_list_url` | `() → str` | `str` | Returns the resolved list URL, or `""` if suppressed by permission gating. |
| `get_breadcrumbs` | `() → list[dict]` | `list` | Two-item trail: `[{"text": list_title, "href": list_url}, {"text": page_title}]`. |
| `get_page_class` | `() → str` | `str` | Appends `{model_name}-page` to the class string from `PageMixin.get_page_class()`. |

**Inherited public API** (from `CRUDDirectoryMixin`):

| Attribute/Method | Description |
|---|---|
| `directory` | List of action names to resolve (e.g., `["list", "detail", "update", "delete"]`) |
| `has_{action}_permission` | `bool` or `Callable[[user], bool]` — gates each URL |
| `get_url_kwargs(action)` | Returns URL kwargs dict for action, or `None` to suppress |
| `crud_views` | Dict of action → URL name pattern |

**Template context contributions** (cumulative from MRO):

| Key | Type | Source |
|---|---|---|
| `page` | `dict` | `PageMixin` (`title`, `subtitle`, `icon`, `class`, `breadcrumbs`) |
| `directory` | `dict` | `CRUDDirectoryMixin` (`{action}_url` entries) |
| `model_info` | `dict` | `ModelInfoMixin` (`verbose_name`, `verbose_name_plural`, `app_label`, `model_name`) |

---

## Entity 2: MVPDetailView

**Module**: `mvp.views.detail`
**Public import**: `from mvp.views import MVPDetailView`

**Purpose**: Zero-configuration read-only detail page. Inherits all shared concerns from `PageObjectMixin` and adds only what is unique to a detail view: a page title derived from the displayed object and a fallback to the shared `detail_view.html` base template.

**Class hierarchy**:

```
MVPDetailView(BaseTemplateNameMixin, PageObjectMixin, generic.DetailView)
```

**Class attributes**:

| Attribute | Type | Value | Description |
|---|---|---|---|
| `base_template_name` | `str` | `"detail_view.html"` | Fallback template when no app-specific template is found |
| `page_class` | `str` | `"mvp-detail-page"` | Action-specific CSS class; combined with `"mvp-page"` and the model-name class by the `get_page_class()` MRO chain |

**Effective CSS classes** (on a rendered page for model `Order`):

```
mvp-page mvp-detail-page order-page
```

**Public methods**:

| Method | Signature | Returns | Description |
|---|---|---|---|
| `get_page_title` | `() → str` | `str` | Returns `str(self.object)` — the string representation of the resolved object |
| `get_template_names` | `() → list[str]` | `list[str]` | Via `BaseTemplateNameMixin`: tries `{app}/{model}_detail.html` first, falls back to `detail_view.html` |

**Minimal usage**:

```python
from mvp.views import MVPDetailView
from myapp.models import Order

class OrderDetailView(MVPDetailView):
    model = Order
    has_list_permission = True  # enables breadcrumb back-link
```

---

## Relationships

```
PageMixin ──────────────────────────────────────┐
ModelInfoMixin → CRUDDirectoryMixin              ├─→ PageObjectMixin → MVPDetailView
                                                 │                  → (MVPCreateView, MVPUpdateView, MVPDeleteView — future specs)
BaseTemplateNameMixin ───────────────────────────┘
```

`CRUDDirectoryMixin`, `ModelInfoMixin`, `PageMixin`, and `BaseTemplateNameMixin` are all defined in previous specs (002, 005, 006). This feature adds only the composition layer (`PageObjectMixin`) and its first concrete application (`MVPDetailView`).
