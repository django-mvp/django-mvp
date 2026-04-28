# Research: Configurable Site Navigation Menu System

**Feature**: 004-site-navigation
**Date**: January 7, 2026
**Purpose**: Document research findings and technology decisions for menu system implementation

## Overview

This document consolidates research on django-flex-menus integration, AdminLTE 4 menu structure, and Cotton component patterns to inform the site navigation implementation.

## Django Flex Menus Integration

### Decision: Use django-flex-menus for Menu Management

**Rationale**:

- Already a project dependency (^0.4.1)
- Provides tree-based menu structure via anytree
- Thread-safe processing and URL resolution
- Support for custom renderers and templates
- Depth-aware template selection
- Distinction between parent (has children) and leaf (no children) items

**Alternatives considered**:

- Custom menu system from scratch → Rejected: Unnecessary reinvention, missing features like URL resolution, thread safety
- Django-treebeard or django-mptt → Rejected: Database-backed, more complexity than needed for code-defined menus
- Simple Python dictionaries → Rejected: No URL resolution, no rendering infrastructure

### Menu Definition API

From django-flex-menus documentation:

```python
from flex_menu import Menu, MenuItem

# Create menu instance
blog_menu = Menu(
    "blog_menu",  # Unique identifier
    children=[
        MenuItem(
            name="home",
            view_name="blog:home",
            extra_context={"label": "Home", "icon": "house"}
        ),
        MenuItem(
            name="categories",
            view_name="blog:category_list",
            extra_context={"label": "Categories"},
            children=[
                MenuItem(
                    name="tech",
                    view_name="blog:category",
                    extra_context={"label": "Technology", "slug": "tech"}
                ),
            ]
        ),
    ],
)
```

**Key findings**:

- `Menu` and `MenuItem` inherit from `anytree.Node`
- `view_name` uses Django URL resolution (e.g., `"app_name:view_name"`)
- `extra_context` dict holds custom data (labels, icons, CSS classes, etc.)
- `children` parameter defines hierarchy
- URL parameters can be passed via template tag or context

### Custom Renderer Pattern

Django-flex-menus uses depth-based template selection:

```python
from flex_menu.renderers import BaseRenderer

class AdminLTERenderer(BaseRenderer):
    """Custom renderer for AdminLTE 4 sidebar."""

    templates = {
        0: {"default": "menus/container.html"},  # Root level
        1: {
            "parent": "menus/parent-item.html",   # Has children
            "leaf": "menus/single-item.html",     # No children
        },
        "default": {  # Fallback for deeper levels
            "parent": "menus/nested-parent.html",
            "leaf": "menus/nested-item.html",
        },
    }

    def get_context_data(self, item: MenuItem, **kwargs):
        """Add custom context for templates."""
        context = super().get_context_data(item, **kwargs)
        context["has_icon"] = "icon" in item.extra_context
        context["archived"] = self._check_active(item)
        return context
```

**Key findings**:

- `templates` dict maps depth → item type → template path
- Depth 0 is the container (root menu)
- Parent items have children, leaf items don't
- `get_context_data` method allows custom context injection
- Renderer has access to request, current URL for active state

### Template Tag Usage

In Django templates:

```django
{% load flex_menu %}
{% render_menu 'menu_name' renderer='custom_renderer' param1=value1 %}
```

**Key findings**:

- `render_menu` tag processes and renders menu
- Renderer name passed as string argument
- Additional kwargs available for URL parameters
- Menu filtering happens automatically based on URL patterns

## AdminLTE 4 Menu HTML Structure

### Research Method

Inspected <https://adminlte.io/themes/v4/> sidebar HTML structure using browser DevTools.

### Container Structure

```html
<nav class="mt-2">
  <ul class="nav sidebar-menu flex-column"
      data-lte-toggle="treeview"
      role="navigation"
      aria-label="Main navigation">
    <!-- Menu items here -->
  </ul>
</nav>
```

**Key findings**:

- Container is `<nav>` with `.mt-2` margin
- Menu list uses `.nav.sidebar-menu.flex-column`
- `data-lte-toggle="treeview"` enables collapsible behavior
- Proper ARIA roles for accessibility

### Single Menu Item (Leaf)

```html
<li class="nav-item">
  <a href="./generate/theme.html" class="nav-link">
    <i class="nav-icon bi bi-palette"></i>
    <p>Theme Generate</p>
  </a>
</li>
```

**Key findings**:

- `.nav-item` on `<li>`
- `.nav-link` on `<a>`
- `.nav-icon` on icon element (Bootstrap Icons)
- Label text in `<p>` tag

### Parent Menu Item (Has Children)

```html
<li class="nav-item menu-open">
  <a href="#" class="nav-link active">
    <i class="nav-icon bi bi-speedometer"></i>
    <p>
      Dashboard
      <i class="nav-arrow bi bi-chevron-right"></i>
    </p>
  </a>
  <ul class="nav nav-treeview" role="navigation" aria-label="Dashboard submenu">
    <li class="nav-item">
      <a href="./index.html" class="nav-link active">
        <i class="nav-icon bi bi-circle"></i>
        <p>Dashboard v1</p>
      </a>
    </li>
    <!-- More children -->
  </ul>
</li>
```

**Key findings**:

- `.menu-open` class when expanded
- `.active` class on current/active links
- `.nav-arrow` icon indicates expandable
- Nested `.nav.nav-treeview` for children
- Children use same `.nav-item` structure
- Nested items typically use `.bi-circle` icon

### Menu Group Header

```html
<li class="nav-header">EXAMPLES</li>
```

**Key findings**:

- Simple `<li>` with `.nav-header` class
- Text content is the header label
- Typically uppercase
- No link, just text separator

### Menu Item with Badge

```html
<li class="nav-item">
  <a href="#" class="nav-link">
    <i class="nav-icon bi bi-clipboard-fill"></i>
    <p>
      Layout Options
      <span class="nav-badge badge text-bg-secondary me-3">6</span>
      <i class="nav-arrow bi bi-chevron-right"></i>
    </p>
  </a>
</li>
```

**Key findings**:

- `.nav-badge.badge` for count/label badges
- Badge positioned before arrow icon
- Bootstrap badge utilities for styling

## Cotton Component Integration

### Component Pattern for Menus

Based on existing django-mvp Cotton components and django-cotton patterns:

```html
<!-- menu.html - Container component -->
<nav class="mt-2">
  <ul class="nav sidebar-menu flex-column"
      data-lte-toggle="treeview"
      role="navigation"
      aria-label="{{ c_label|default:'Main navigation' }}">
    <c-slot />
  </ul>
</nav>
```

```html
<!-- menu.item.html - Single or parent item -->
<li class="nav-item {{ c_classes }}">
  <a href="{{ c_url }}" class="nav-link {{ c_link_classes }}">
    {% if c_icon %}
      <c-icon name="{{ c_icon }}" class="nav-icon" />
    {% endif %}
    <p>
      {{ c_label }}
      {% if c_badge %}
        <span class="nav-badge badge {{ c_badge_classes }}">{{ c_badge }}</span>
      {% endif %}
      {% if c_has_children %}
        <i class="nav-arrow bi bi-chevron-right"></i>
      {% endif %}
    </p>
  </a>
  {% if c_has_children %}
    <ul class="nav nav-treeview" role="navigation" aria-label="{{ c_label }} submenu">
      <c-slot name="children" />
    </ul>
  {% endif %}
</li>
```

```html
<!-- menu-header.html - Section header -->
<li class="nav-header">{{ c_label|upper }}</li>
```

**Key findings**:

- Cotton c-vars for dynamic content (`c_label`, `c_url`, `c_icon`)
- `c-slot` for nested content
- Named slots for children (`<c-slot name="children" />`)
- Integration with django-easy-icons via `<c-icon />`
- CSS class customization via `c_classes`, `c_link_classes`

## Menu Ordering Strategy

### Decision: App Order Determines Menu Order

**Rationale**:

- Django processes apps in `INSTALLED_APPS` order
- Menu items added during app ready/import time
- Users control ordering via `INSTALLED_APPS` configuration
- Predictable and explicit (follows Django conventions)

**Implementation approach**:

1. Users import `AppMenu` from `mvp.menus` in their `app/menus.py`
2. Add items using django-flex-menus API
3. Items added in the order they're declared
4. Multiple apps can contribute; ordering follows `INSTALLED_APPS`

**Alternatives considered**:

- Explicit priority/weight system → Rejected: Adds complexity, app order is sufficient
- Alphabetical sorting → Rejected: Not predictable, users lose control
- Database-backed ordering → Rejected: Out of scope, menus are code-defined

## Menu Grouping Pattern

### Decision: Separate Single Items from Groups

From spec requirements:

- Single items (no children) render first
- Menu groups (with children) render after
- Groups have visual headers (`.nav-header`)

**Implementation approach**:

1. Custom renderer sorts menu items:
   - Collect items without children → render first
   - Collect items with children → render after
2. For grouped items, inject `.nav-header` before each group
3. Use `extra_context` to specify group header text

**Example**:

```python
AppMenu.children.extend([
    # Single items - render first
    MenuItem(name="home", view_name="app:home", extra_context={"label": "Home"}),
    MenuItem(name="profile", view_name="app:profile", extra_context={"label": "Profile"}),

    # Grouped items - render after with headers
    MenuItem(
        name="admin",
        view_name="#",  # No direct link
        extra_context={"label": "Administration", "group_header": "ADMIN TOOLS"},
        children=[
            MenuItem(name="users", view_name="app:users", extra_context={"label": "Users"}),
            MenuItem(name="settings", view_name="app:settings", extra_context={"label": "Settings"}),
        ]
    ),
])
```

## Icon Integration

### Decision: Use django-easy-icons with Bootstrap Icons

**Rationale**:

- Django-easy-icons already integrated (^0.4.0)
- AdminLTE 4 uses Bootstrap Icons by default
- Provides unified icon syntax across components

**Implementation approach**:

- Menu items specify icon name in `extra_context`
- Cotton menu component uses `<c-icon name="{{ c_icon }}" />`
- Renders as `<i class="nav-icon bi bi-{name}"></i>`
- Falls back gracefully if no icon specified

## URL Resolution

### Decision: Use Django URL Names with flex-menus

**Rationale**:

- Django best practice (URL patterns can change, names are stable)
- django-flex-menus handles resolution automatically
- Supports parameterized URLs

**Implementation approach**:

```python
MenuItem(
    name="detail",
    view_name="app:detail",  # Django URL name
    extra_context={"label": "View Detail"}
)
```

For parameterized URLs, pass context when rendering:

```django
{% render_menu 'AppMenu' renderer='adminlte' pk=object.pk %}
```

## Active State Detection

### Decision: Leverage Django Request Context

**Implementation approach**:

- Custom renderer checks `request.resolver_match.url_name`
- Compares with menu item `view_name`
- Adds `.active` class to matching items
- Adds `.menu-open` class to parent items containing active children

**Pattern**:

```python
def get_context_data(self, item: MenuItem, **kwargs):
    context = super().get_context_data(item, **kwargs)
    request = kwargs.get('request')

    if request:
        current_url_name = request.resolver_match.url_name
        item_url_name = item.view_name.split(':')[-1] if item.view_name else None
        context['archived'] = current_url_name == item_url_name

    return context
```

## Summary of Key Decisions

| Decision | Chosen Approach | Rationale |
|----------|----------------|-----------|
| Menu Library | django-flex-menus | Already integrated, feature-rich, extensible |
| Rendering | Custom BaseRenderer + Cotton components | Combines flex-menus power with Cotton composability |
| Menu Structure | AdminLTE 4 sidebar HTML | Maintains visual consistency, uses AdminLTE JS |
| Menu Storage | Empty `AppMenu` in mvp.menus | Users populate via imports, code-based config |
| Item Ordering | App order + declaration order | Predictable, follows Django conventions |
| Single vs Group | Custom renderer sorting | Meets spec requirement (singles first, groups after) |
| Icons | django-easy-icons with Bootstrap Icons | Already integrated, AdminLTE standard |
| URLs | Django URL names | Best practice, stable references |
| Active State | Request-based detection in renderer | Automatic, requires no manual marking |

## Next Steps

Phase 1 will define:

1. **Data Model**: Menu and MenuItem entity structure, relationships, properties
2. **API Contracts**: Python signatures for Menu, MenuItem, Renderer, template c-vars
3. **Quickstart Guide**: Developer-facing documentation with usage examples
