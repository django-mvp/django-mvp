# Data Model: Document and Test Core View Mixins

**Branch**: `003-base-mixin-classes` | **Date**: 2026-05-02

> No database models are introduced or modified by this feature. This document describes the **class model** — the public interface, attributes, and MRO relationships for `BaseTemplateNameMixin` and `PageMixin`.

---

## Class: `BaseTemplateNameMixin`

**Module**: `mvp.views.base`  
**Purpose**: Extends Django's template resolution to support a mandatory fallback base template. The most-specific template (from the concrete view) is tried first; the base template acts as a catch-all shell.

### Class Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_template_name` | `str \| None` | `None` | The fallback template name appended to the template candidate list. **Must** be set by subclasses; raises `ImproperlyConfigured` otherwise. |

### Public Methods

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `get_template_names()` | `(self) → list[str]` | List of template name strings | Calls `super().get_template_names()`, then appends `self.base_template_name`. Raises `ImproperlyConfigured` if `base_template_name` is `None`. |

### Behaviour Contracts

- `get_template_names()` MUST always return `super().get_template_names()` results first (higher specificity), with `base_template_name` appended last.
- When `base_template_name is None`: raises `ImproperlyConfigured` with message: `"{ClassName} requires a 'base_template_name' attribute to be set."`
- When `base_template_name` is a non-empty string: appends it unconditionally to the list.

### Known Subclasses

| Class | Module | `base_template_name` value |
|-------|--------|---------------------------|
| `MVPDetailView` | `mvp.views.detail` | `"detail_view.html"` |
| `MVPListViewMixin` | `mvp.views.list` | `"list_view.html"` |
| `MVPFormBase` | `mvp.views.edit` | `"form_view.html"` |
| `MVPDeleteView` | `mvp.views.edit` | `"delete_view.html"` |
| `MVPTableView` / `MVPTableListView` | `mvp.views.table` | `"table_view.html"` |

---

## Class: `PageMixin`

**Module**: `mvp.views.base`  
**Purpose**: Injects a `page` context dict into the template context, grouping all page-level rendering metadata (title, subtitle, icon, CSS class, breadcrumbs) under a single key to avoid namespace pollution.

### Class Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `page_title` | `str \| Promise` | `""` | Declarative page title. Override `get_page_title()` for dynamic values. |
| `page_subtitle` | `str \| Promise` | `""` | Declarative page subtitle. Override `get_page_subtitle()` for dynamic values. |
| `page_icon` | `str \| None` | `None` | Icon name (e.g., `"fas fa-home"`). Override `get_page_icon()` for dynamic values. |
| `page_class` | `str` | `""` | Extra CSS class(es) appended to the page container after `"mvp-page"`. |
| `breadcrumbs` | `list` | `[]` | Declarative breadcrumb list. Override `get_breadcrumbs()` for dynamic values. |

### Public Methods

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `get_context_data(**kwargs)` | `(self, **kwargs) → dict` | Template context dict | Calls `super().get_context_data(**kwargs)`, adds `context["page"]` from `get_page_context()`. |
| `get_page_context()` | `(self) → dict` | Page context dict | Returns dict with keys: `title`, `subtitle`, `icon`, `class`, `breadcrumbs`. |
| `get_page_title()` | `(self) → str \| Promise` | Page title string | Returns `self.page_title`. |
| `get_page_subtitle()` | `(self) → str \| Promise` | Page subtitle string | Returns `self.page_subtitle`. |
| `get_page_icon()` | `(self) → str \| None` | Icon name or `None` | Returns `self.page_icon`. |
| `get_page_class()` | `(self) → str` | CSS class string | Returns `"mvp-page"` joined with `self.page_class` (filters empty strings). Always includes `"mvp-page"`. |
| `get_breadcrumbs()` | `(self) → list` | List of breadcrumb dicts | Returns `self.breadcrumbs`. |

### `page` Context Dict Shape

```python
{
    "title": str | Promise,      # from get_page_title()
    "subtitle": str | Promise,   # from get_page_subtitle()
    "icon": str | None,          # from get_page_icon()
    "class": str,                # from get_page_class(); always starts with "mvp-page"
    "breadcrumbs": list,         # from get_breadcrumbs()
}
```

### Breadcrumb Item Shape (convention)

Each item in the breadcrumbs list is a dict:

```python
{"text": str, "href": str}           # linked breadcrumb
{"text": str}                         # unlinked (current page) breadcrumb
```

### Behaviour Contracts

- `get_page_class()` MUST always include `"mvp-page"` as a prefix regardless of `page_class` value.
- `get_page_class()` MUST silently ignore an empty `page_class` (no leading/trailing spaces or double-spaces).
- `get_context_data()` MUST preserve all keys from `super().get_context_data()` and only add `"page"`.
- `get_breadcrumbs()` returns `self.breadcrumbs` — subclasses may override to return computed lists.

---

## Class Hierarchy (relevant excerpt)

```
django.views.generic.base.ContextMixin
    └── PageMixin                         (injects page context)
            └── MVPTemplateView           (PageMixin + TemplateView)
                    └── MVPHomeView

django.views.generic.base.TemplateResponseMixin
    └── BaseTemplateNameMixin             (extends template resolution)
            └── MVPDetailView             (+ PageMixin, DetailView)
            └── MVPListViewMixin          (+ PageMixin, ListView)
            └── MVPFormBase               (+ PageMixin, FormView)
            └── MVPDeleteView             (extends MVPFormBase)
            └── MVPTableView              (+ PageMixin, ListView)
```
