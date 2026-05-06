# Public API Contract: MVPListView and MVPListViewMixin

**Feature**: `015-mvp-list-view` | **Date**: 2026-05-06

This contract describes the public API surface that downstream application developers
depend on. Any change to these signatures or semantics is a **breaking change** and
requires a version bump and migration note.

---

## Class: `MVPListViewMixin`

**Module**: `mvp.views.list`  
**MRO**: `BaseTemplateNameMixin → SearchOrderMixin → CRUDDirectoryMixin → PageMixin`

### Configuration Attributes (set on subclass)

```python
list_item_template: str | None = None
# Explicit item partial path. When falsy, auto-discovery runs.

grid: dict = {}
# Grid layout dict. Passed unchanged to context as `grid_config`.

empty_state_heading: str | None = _("There's nothing here yet")
# Heading for zero-results state. None suppresses heading.

empty_state_message: str | None = _("You haven't added any records yet. Click the button below to get started.")
# Body for zero-results state. None suppresses body.

directory: list[str] = ["create"]
# Limits CRUDDirectoryMixin to the create action only.

# Inherited from SearchMixin:
search_fields: list[str] | None = None

# Inherited from OrderMixin:
order_by: list[tuple[str, str, str]] | None = None
```

### Override Hooks (override in subclass)

```python
def get_list_item_template(self) -> str:
    """Return the partial template path for rendering each list item.

    Priority: explicit list_item_template → auto-discovery.
    Auto-discovery produces: "<app_label>/<model_name>_list_item.html"
    Raises AttributeError when neither model nor list_item_template is set.
    """

def get_page_title(self) -> str:
    """Return page title. page_title attribute takes precedence; 
    falls back to model._meta.verbose_name_plural.title()."""

def get_breadcrumbs(self) -> list[dict]:
    """Return breadcrumb trail.
    Default: [{"text": "Home", "href": "/"}, {"text": <page_title>}]"""

def get_empty_state_heading(self) -> str | None:
    """Return empty state heading text."""

def get_empty_state_message(self) -> str | None:
    """Return empty state body text."""

def get_grid_config(self) -> dict:
    """Return grid configuration dict."""
```

### Context Keys Injected (always present)

| Key | Type | Notes |
|---|---|---|
| `list_item_template` | `str` | Resolved item partial path |
| `empty_state` | `dict` | `{"heading": str\|None, "message": str\|None}` |
| `grid_config` | `dict` | May be empty dict |
| `directory` | `dict` | May be `{}` when `has_create_permission` is falsy |
| `page` | `dict` | `{"title", "subtitle", "icon", "class", "breadcrumbs"}` |
| `search_query` | `str` | Always `""` when search is unconfigured |
| `is_searchable` | `bool` | `False` when `search_fields` is None |

---

## Class: `MVPListView`

**Module**: `mvp.views.list`  
**Bases**: `MVPListViewMixin, ListView`

### Class Attributes

```python
paginate_by: int = 24
# Override to change page size. 24 is divisible by 1, 2, 3, 4.
```

### Minimum Required Configuration

```python
class MyListView(MVPListView):
    model = MyModel
    # paginate_by = 24 by default
    # list_item_template auto-resolved to "<app>/<model>_list_item.html"
    # page title auto-resolved to model.verbose_name_plural.title()
```

---

## Stability

All attributes and methods listed above are **stable public API**. Renaming,
removing, or changing their type/return contract requires a semver-major
version bump and an entry in `CHANGELOG.md`.

Private helpers (methods prefixed `_`) are exempt from this contract.
