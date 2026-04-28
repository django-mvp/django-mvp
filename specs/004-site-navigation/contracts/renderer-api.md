# API Contract: AdminLTE Renderer

**Feature**: 004-site-navigation
**Date**: January 7, 2026
**Purpose**: Define custom renderer for AdminLTE 4 sidebar menu rendering

## Overview

The `AdminLTERenderer` extends django-flex-menus' `BaseRenderer` to provide AdminLTE 4-specific menu rendering with support for single items, hierarchical groups, and custom template selection based on depth and item type.

## Class Definition

### Location

```python
# mvp/renderers.py
from flex_menu.renderers import BaseRenderer
from flex_menu.menu import MenuItem
from typing import Dict, Any

class AdminLTERenderer(BaseRenderer):
    """
    Custom renderer for AdminLTE 4 sidebar navigation.

    Handles:
    - Single items (no children) rendered first
    - Group items (with children) rendered after with headers
    - Depth-based template selection
    - Active state detection based on current URL
    - Icon and badge rendering via extra_context
    """
```

### Inheritance

- **Parent class**: `flex_menu.renderers.BaseRenderer`
- **Provides**: Template selection, context enrichment, sorting logic

## Public Interface

### templates Property

**Type**: `Dict[int | str, Dict[str, str]]`

**Purpose**: Maps depth levels and item types to Django template paths

**Structure**:

```python
templates = {
    # Depth 0: Container (root menu)
    0: {
        "default": "menus/container.html"
    },

    # Depth 1: Top-level items
    1: {
        "parent": "menus/parent-item.html",   # Has children
        "leaf": "menus/single-item.html"      # No children
    },

    # Depth 2+: Nested items (fallback)
    "default": {
        "parent": "menus/nested-parent.html",
        "leaf": "menus/nested-item.html"
    }
}
```

**Template selection logic**:

1. Check if item depth has explicit mapping (0, 1, 2, ...)
2. If found, select "parent" or "leaf" based on `item.children`
3. If not found, use "default" mapping
4. If item has `template_name` override, use that instead

### get_context_data Method

**Signature**:

```python
def get_context_data(
    self,
    item: MenuItem,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Build template context for rendering a menu item.

    Args:
        item: MenuItem instance to render
        **kwargs: Additional context (request, depth, parent_context, etc.)

    Returns:
        Dict with template context including:
        - All extra_context keys (label, icon, classes, etc.)
        - archived: bool - Whether item matches current URL
        - has_children: bool - Whether item has children
        - has_icon: bool - Whether icon is specified
        - has_badge: bool - Whether badge is specified
        - url: str - Resolved URL for item
        - depth: int - Nesting depth
    """
```

**Context keys provided**:

| Key | Type | Description | Source |
|-----|------|-------------|--------|
| `label` | str | Display text | `item.extra_context.get("label", item.name)` |
| `url` | str | Resolved URL | Django reverse() via view_name |
| `icon` | str \| None | Icon name | `item.extra_context.get("icon")` |
| `icon_set` | str | Icon set | `item.extra_context.get("icon_set", "bi")` |
| `classes` | str | CSS classes for `<li>` | `item.extra_context.get("classes", "")` |
| `link_classes` | str | CSS classes for `<a>` | `item.extra_context.get("link_classes", "")` |
| `badge` | str \| None | Badge text | `item.extra_context.get("badge")` |
| `badge_classes` | str | Badge CSS classes | `item.extra_context.get("badge_classes", "text-bg-secondary")` |
| `archived` | bool | Current page match | Compares request URL with view_name |
| `has_children` | bool | Has nested items | `len(item.children) > 0` |
| `has_icon` | bool | Icon specified | `"icon" in item.extra_context` |
| `has_badge` | bool | Badge specified | `"badge" in item.extra_context` |
| `depth` | int | Nesting level | anytree depth property |
| `group_header` | str \| None | Section header | `item.extra_context.get("group_header")` |

**Example implementation**:

```python
def get_context_data(self, item: MenuItem, **kwargs) -> Dict[str, Any]:
    # Get base context from parent class
    context = super().get_context_data(item, **kwargs)

    # Extract extra_context
    extra = item.extra_context or {}

    # Add derived flags
    context["has_children"] = len(item.children) > 0
    context["has_icon"] = "icon" in extra
    context["has_badge"] = "badge" in extra

    # Detect active state
    request = kwargs.get("request")
    if request and request.resolver_match:
        current_url_name = request.resolver_match.url_name
        item_url_name = item.view_name.split(":")[-1] if item.view_name else None
        context["archived"] = current_url_name == item_url_name
    else:
        context["archived"] = False

    # Check if parent contains active child
    context["is_open"] = self._has_active_descendant(item, request)

    return context

def _has_active_descendant(self, item: MenuItem, request) -> bool:
    """Check if item or any descendant is active."""
    if not request or not request.resolver_match:
        return False

    current = request.resolver_match.url_name

    # Check item itself
    if item.view_name:
        if item.view_name.split(":")[-1] == current:
            return True

    # Check descendants
    for child in item.descendants:
        if child.view_name and child.view_name.split(":")[-1] == current:
            return True

    return False
```

### render Method (Inherited)

**Signature** (from BaseRenderer):

```python
def render(
    self,
    menu: Menu,
    **kwargs: Any
) -> str:
    """
    Render complete menu to HTML string.

    Args:
        menu: Menu instance to render
        **kwargs: Context variables (request, user, etc.)

    Returns:
        Rendered HTML string
    """
```

**Behavior**:

1. Sort items (singles first, groups after)
2. Walk menu tree from root
3. For each item:
   - Select template based on depth/type
   - Build context via get_context_data()
   - Render template with context
   - If has children, recursively render children
4. Return assembled HTML

### Sorting Logic (Custom Method)

**Method**:

```python
def sort_items(self, items: List[MenuItem]) -> List[MenuItem]:
    """
    Sort menu items: singles first, then groups.

    Args:
        items: List of MenuItem instances at same level

    Returns:
        Sorted list with items without children first,
        then items with children
    """
    singles = [item for item in items if not item.children]
    groups = [item for item in items if item.children]
    return singles + groups
```

**Application**:

- Called before rendering depth 1 (top-level) items
- Ensures spec requirement: "single items rendered first"
- Preserves declaration order within each category

## Template Contract

### Container Template (Depth 0)

**Path**: `menus/container.html`

**Expected context**:

- `menu`: Menu instance
- `children`: Rendered HTML of top-level items

**Expected output**:

```html
<nav class="mt-2">
  <ul class="nav sidebar-menu flex-column"
      data-lte-toggle="treeview"
      role="navigation"
      aria-label="Main navigation">
    {{ children|safe }}
  </ul>
</nav>
```

### Single Item Template (Depth 1, Leaf)

**Path**: `menus/single-item.html`

**Expected context**:

- `label`: str
- `url`: str
- `icon`: str | None
- `icon_set`: str
- `archived`: bool
- `classes`: str

**Expected output**:

```html
<li class="nav-item {{ classes }}">
  <a href="{{ url }}" class="nav-link {% if archived %}active{% endif %} {{ link_classes }}">
    {% if has_icon %}
      <c-icon name="{{ icon }}" set="{{ icon_set }}" class="nav-icon" />
    {% endif %}
    <p>{{ label }}</p>
  </a>
</li>
```

### Parent Item Template (Depth 1, Parent)

**Path**: `menus/parent-item.html`

**Expected context**:

- `label`: str
- `group_header`: str | None
- `icon`: str | None
- `is_open`: bool
- `children`: Rendered HTML of nested items

**Expected output**:

```html
{% if group_header %}
  <li class="nav-header">{{ group_header|upper }}</li>
{% endif %}
<li class="nav-item {% if is_open %}menu-open{% endif %} {{ classes }}">
  <a href="#" class="nav-link {{ link_classes }}">
    {% if has_icon %}
      <c-icon name="{{ icon }}" set="{{ icon_set }}" class="nav-icon" />
    {% endif %}
    <p>
      {{ label }}
      {% if has_badge %}
        <span class="nav-badge badge {{ badge_classes }}">{{ badge }}</span>
      {% endif %}
      <i class="nav-arrow bi bi-chevron-right"></i>
    </p>
  </a>
  <ul class="nav nav-treeview" role="navigation" aria-label="{{ label }} submenu">
    {{ children|safe }}
  </ul>
</li>
```

### Nested Item Templates (Depth 2+)

**Paths**:

- `menus/nested-item.html` (leaf)
- `menus/nested-parent.html` (parent)

**Context**: Same as depth 1, but uses `.bi-circle` icon for children

## Usage Example

### Template Tag Invocation

```django
{% load flex_menu %}

{# Basic usage #}
{% render_menu 'AppMenu' renderer='adminlte' %}

{# With URL parameters #}
{% render_menu 'AppMenu' renderer='adminlte' user_id=user.id %}

{# With custom context #}
{% render_menu 'AppMenu' renderer='adminlte' request=request user=request.user %}
```

### Renderer Registration

```python
# mvp/renderers.py

# Renderer auto-discovered by name
class AdminLTERenderer(BaseRenderer):
    pass

# In template, use lowercase name
{% render_menu 'AppMenu' renderer='adminlte' %}
```

## Extension Points

### Custom Template Selection

Override `get_template` method for complex logic:

```python
class AdminLTERenderer(BaseRenderer):
    templates = {...}

    def get_template(self, item: MenuItem, **kwargs) -> str:
        """Custom template selection logic."""
        # Check for custom template on item
        if item.template_name:
            return item.template_name

        # Custom logic based on extra_context
        if item.extra_context.get("type") == "widget":
            return "menus/widget-item.html"

        # Fall back to default depth-based selection
        return super().get_template(item, **kwargs)
```

### Custom Context Enrichment

Add more context data:

```python
class AdminLTERenderer(BaseRenderer):
    def get_context_data(self, item: MenuItem, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(item, **kwargs)

        # Add permission check
        request = kwargs.get("request")
        if request and item.extra_context.get("permission"):
            context["has_permission"] = request.user.has_perm(
                item.extra_context["permission"]
            )

        # Add custom styling
        if item.extra_context.get("highlight"):
            context["link_classes"] += " text-warning"

        return context
```

## Testing Contract

### Unit Tests Required

```python
def test_renderer_sorts_singles_first():
    """Singles without children appear before groups."""

def test_renderer_detects_active_state():
    """Current URL marked as active."""

def test_renderer_selects_correct_template():
    """Depth and type determine template."""

def test_renderer_enriches_context():
    """Context includes archived, has_children, etc."""

def test_renderer_handles_group_headers():
    """Group headers rendered before parent items."""
```

### Integration Tests Required

```python
def test_menu_renders_with_adminlte_renderer():
    """Full menu renders to HTML with correct structure."""

def test_nested_items_use_nested_templates():
    """Depth 2+ items use default templates."""

def test_icons_render_with_easy_icons():
    """Icon names passed to c-icon component."""
```

## Summary

The AdminLTERenderer contract defines:

1. **templates**: Depth/type mapping to Django templates
2. **get_context_data()**: Context enrichment with active state, flags, extra_context
3. **sort_items()**: Singles first, groups after (at depth 1)
4. **Template expectations**: Container, single, parent, nested templates
5. **Extension points**: Override get_template() or get_context_data() for customization

Renderer integrates django-flex-menus with AdminLTE 4 sidebar structure and Cotton components.
