# API Contract: Cotton Menu Components

**Feature**: 004-site-navigation
**Date**: January 7, 2026
**Purpose**: Define Cotton component c-vars and template interfaces for menu rendering

## Overview

Django-mvp provides Cotton components for rendering AdminLTE 4 sidebar menus. These components receive context from the AdminLTE renderer and generate semantic HTML with proper AdminLTE CSS classes.

## Component Locations

```
mvp/templates/cotton/app/sidebar/
├── menu.html          # Container component (optional wrapper)
├── menu.item.html     # Single or parent menu item
└── menu-header.html   # Section header
```

**Note**: The primary templates used by the renderer are in `mvp/templates/menus/` (renderer templates). Cotton components in `cotton/app/sidebar/` can be used for custom template implementations or direct usage.

## Container Component

### File: `cotton/app/sidebar/menu.html`

**Purpose**: Optional wrapper for menu list (if needed for custom layouts)

**c-vars**:

```python
c_label: str = "Main navigation"  # ARIA label for navigation
c_classes: str = ""                # Additional CSS classes for <ul>
c_id: str = "navigation"           # ID for <ul> element
```

**Template Structure**:

```html
<nav class="mt-2">
  <ul class="nav sidebar-menu flex-column"
      data-lte-toggle="treeview"
      role="navigation"
      aria-label="{{ c_label }}"
      id="{{ c_id }}"
      class="{{ c_classes }}">
    <c-slot />
  </ul>
</nav>
```

**Usage** (if wrapping menu items manually):

```django
<c-app.sidebar.menu c_label="Application Menu">
  <c-app.sidebar.menu.item c_label="Home" c_url="/" c_icon="house" />
  <c-app.sidebar.menu.item c_label="Profile" c_url="/profile" c_icon="person" />
</c-app.sidebar.menu>
```

## Menu Item Component

### File: `cotton/app/sidebar/menu.item.html`

**Purpose**: Renders single menu item or parent item with children

**c-vars**:

| c-var | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `c_label` | str | Yes | N/A | Display text for menu item |
| `c_url` | str | No | `"#"` | Link URL (use "#" for non-clickable) |
| `c_icon` | str | No | `None` | Icon name for django-easy-icons |
| `c_icon_set` | str | No | `"bi"` | Icon set (Bootstrap Icons by default) |
| `c_classes` | str | No | `""` | Additional classes for `<li class="nav-item">` |
| `c_link_classes` | str | No | `""` | Additional classes for `<a class="nav-link">` |
| `c_archived` | bool | No | `False` | Whether item is current page |
| `c_is_open` | bool | No | `False` | Whether parent is expanded (has active child) |
| `c_badge` | str | No | `None` | Badge text/number |
| `c_badge_classes` | str | No | `"text-bg-secondary"` | Badge styling classes |
| `c_has_children` | bool | No | `False` | Whether item has nested children |
| `c_submenu_label` | str | No | `"{c_label} submenu"` | ARIA label for nested list |

**Template Structure**:

```html
<li class="nav-item {% if c_is_open %}menu-open{% endif %} {{ c_classes }}">
  <a href="{{ c_url }}" class="nav-link {% if c_archived %}active{% endif %} {{ c_link_classes }}">
    {% if c_icon %}
      <c-icon name="{{ c_icon }}" set="{{ c_icon_set }}" class="nav-icon" />
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
    <ul class="nav nav-treeview" role="navigation" aria-label="{{ c_submenu_label }}">
      <c-slot name="children" />
    </ul>
  {% endif %}
</li>
```

**Usage Examples**:

#### Single Item (Leaf)

```django
<c-app.sidebar.menu.item
  c_label="Dashboard"
  c_url="/dashboard/"
  c_icon="speedometer"
  c_archived="{{ request.path == '/dashboard/' }}"
/>
```

**Expected output**:

```html
<li class="nav-item">
  <a href="/dashboard/" class="nav-link active">
    <i class="nav-icon bi bi-speedometer"></i>
    <p>Dashboard</p>
  </a>
</li>
```

#### Parent Item with Children

```django
<c-app.sidebar.menu.item
  c_label="Administration"
  c_icon="gear"
  c_has_children="True"
  c_is_open="{{ has_active_admin }}">
  <c-slot name="children">
    <c-app.sidebar.menu.item c_label="Users" c_url="/admin/users/" c_icon="people" />
    <c-app.sidebar.menu.item c_label="Settings" c_url="/admin/settings/" c_icon="sliders" />
  </c-slot>
</c-app.sidebar.menu.item>
```

**Expected output**:

```html
<li class="nav-item menu-open">
  <a href="#" class="nav-link">
    <i class="nav-icon bi bi-gear"></i>
    <p>
      Administration
      <i class="nav-arrow bi bi-chevron-right"></i>
    </p>
  </a>
  <ul class="nav nav-treeview" role="navigation" aria-label="Administration submenu">
    <li class="nav-item">
      <a href="/admin/users/" class="nav-link">
        <i class="nav-icon bi bi-people"></i>
        <p>Users</p>
      </a>
    </li>
    <li class="nav-item">
      <a href="/admin/settings/" class="nav-link">
        <i class="nav-icon bi bi-sliders"></i>
        <p>Settings</p>
      </a>
    </li>
  </ul>
</li>
```

#### Item with Badge

```django
<c-app.sidebar.menu.item
  c_label="Messages"
  c_url="/messages/"
  c_icon="envelope"
  c_badge="3"
  c_badge_classes="text-bg-danger"
/>
```

**Expected output**:

```html
<li class="nav-item">
  <a href="/messages/" class="nav-link">
    <i class="nav-icon bi bi-envelope"></i>
    <p>
      Messages
      <span class="nav-badge badge text-bg-danger">3</span>
    </p>
  </a>
</li>
```

## Menu Header Component

### File: `cotton/app/sidebar/menu-header.html`

**Purpose**: Renders section header for menu groups

**c-vars**:

| c-var | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `c_label` | str | Yes | N/A | Header text (will be uppercased) |
| `c_classes` | str | No | `""` | Additional CSS classes |

**Template Structure**:

```html
<li class="nav-header {{ c_classes }}">{{ c_label|upper }}</li>
```

**Usage**:

```django
<c-app.sidebar.menu-header c_label="Admin Tools" />
<c-app.sidebar.menu.item c_label="Users" c_url="/admin/users/" />
<c-app.sidebar.menu.item c_label="Settings" c_url="/admin/settings/" />
```

**Expected output**:

```html
<li class="nav-header">ADMIN TOOLS</li>
<li class="nav-item">
  <a href="/admin/users/" class="nav-link">
    <p>Users</p>
  </a>
</li>
<li class="nav-item">
  <a href="/admin/settings/" class="nav-link">
    <p>Settings</p>
  </a>
</li>
```

## Renderer Template Integration

The AdminLTE renderer uses **renderer templates** in `mvp/templates/menus/` that internally use Cotton components or replicate their structure. This ensures proper integration with django-flex-menus' rendering pipeline.

### Renderer Template: `menus/container.html`

**Context variables**:

- `menu`: Menu instance
- `children`: Pre-rendered HTML of menu items (string)

**Template**:

```django
<nav class="mt-2">
  <ul class="nav sidebar-menu flex-column"
      data-lte-toggle="treeview"
      role="navigation"
      aria-label="Main navigation"
      id="navigation">
    {{ children|safe }}
  </ul>
</nav>
```

### Renderer Template: `menus/single-item.html`

**Context variables**:

- From `extra_context`: label, icon, icon_set, classes, link_classes
- From renderer: url, archived, has_icon, depth

**Template**:

```django
<li class="nav-item {{ classes }}">
  <a href="{{ url }}" class="nav-link {% if archived %}active{% endif %} {{ link_classes }}">
    {% if has_icon %}
      <c-icon name="{{ icon }}" set="{{ icon_set }}" class="nav-icon" />
    {% endif %}
    <p>{{ label }}</p>
  </a>
</li>
```

### Renderer Template: `menus/parent-item.html`

**Context variables**:

- From `extra_context`: label, icon, group_header, badge, badge_classes, classes
- From renderer: is_open, has_icon, has_badge, has_children
- `children`: Pre-rendered HTML of nested items (string)

**Template**:

```django
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

### Renderer Template: `menus/nested-item.html`

**Context variables**: Same as `single-item.html`

**Template**: Same as `single-item.html`, but typically uses `.bi-circle` icon for visual consistency:

```django
<li class="nav-item {{ classes }}">
  <a href="{{ url }}" class="nav-link {% if archived %}active{% endif %} {{ link_classes }}">
    <i class="nav-icon bi bi-circle"></i>
    <p>{{ label }}</p>
  </a>
</li>
```

### Renderer Template: `menus/nested-parent.html`

**Context variables**: Same as `parent-item.html`, without `group_header`

**Template**: Similar to `parent-item.html`, but no header:

```django
<li class="nav-item {% if is_open %}menu-open{% endif %} {{ classes }}">
  <a href="#" class="nav-link {{ link_classes }}">
    <i class="nav-icon bi bi-circle"></i>
    <p>
      {{ label }}
      <i class="nav-arrow bi bi-chevron-right"></i>
    </p>
  </a>
  <ul class="nav nav-treeview" role="navigation" aria-label="{{ label }} submenu">
    {{ children|safe }}
  </ul>
</li>
```

## CSS Classes Reference

### AdminLTE 4 Classes Used

| Class | Element | Purpose |
|-------|---------|---------|
| `.nav` | `<ul>` | Base nav list |
| `.sidebar-menu` | `<ul>` | Sidebar-specific menu styling |
| `.flex-column` | `<ul>` | Vertical layout |
| `.nav-item` | `<li>` | Menu item container |
| `.nav-link` | `<a>` | Menu link styling |
| `.nav-icon` | `<i>` | Icon styling and spacing |
| `.nav-arrow` | `<i>` | Expand/collapse indicator |
| `.nav-badge` | `<span>` | Badge container |
| `.nav-header` | `<li>` | Section header styling |
| `.nav-treeview` | `<ul>` | Nested menu list |
| `.active` | `.nav-link` | Current page indicator |
| `.menu-open` | `.nav-item` | Expanded parent item |

### Bootstrap Classes Used

| Class | Purpose |
|-------|---------|
| `.badge` | Badge base styling |
| `.text-bg-*` | Badge color variants (primary, secondary, danger, etc.) |
| `.bi` | Bootstrap Icons base class |
| `.bi-*` | Specific icon names (bi-house, bi-gear, etc.) |

## Accessibility Requirements

### ARIA Attributes

**Navigation landmark**:

```html
<nav role="navigation" aria-label="Main navigation">
```

**Nested navigation**:

```html
<ul role="navigation" aria-label="{{ label }} submenu">
```

### Keyboard Navigation

- **Tab**: Move between menu items
- **Enter/Space**: Activate link or toggle parent
- **Arrow keys**: Navigate up/down menu (AdminLTE JS handles this)

### Screen Reader Considerations

- Icons must have text labels (achieved via `<p>` tags)
- Expand/collapse state communicated via `aria-expanded` (AdminLTE JS)
- Current page indicated by `.active` class and visually distinct

## Testing Contract

### Component Tests Required

```python
def test_menu_item_renders_with_label():
    """Menu item displays label text."""

def test_menu_item_renders_icon():
    """Icon rendered when c_icon provided."""

def test_menu_item_applies_active_class():
    """Active class applied when c_archived=True."""

def test_menu_item_renders_children():
    """Parent item renders nested ul with children."""

def test_menu_header_uppercases_label():
    """Header text rendered in uppercase."""

def test_menu_item_renders_badge():
    """Badge displayed when c_badge provided."""
```

### Integration Tests Required

```python
def test_full_menu_renders_from_appmenu():
    """Complete menu renders with singles first, groups after."""

def test_nested_menu_renders_correctly():
    """Multi-level nesting produces correct HTML structure."""

def test_active_state_highlights_current_page():
    """Current page menu item has active class."""
```

## Summary

The Cotton component API defines:

1. **menu.html**: Optional container wrapper (c_label, c_classes, c_id)
2. **menu.item.html**: Single or parent item (c_label, c_url, c_icon, c_has_children, etc.)
3. **menu-header.html**: Section header (c_label)
4. **Renderer templates**: Direct templates used by AdminLTERenderer in `menus/` directory
5. **CSS classes**: AdminLTE 4 + Bootstrap classes for proper styling
6. **Accessibility**: ARIA labels, keyboard navigation, screen reader support

Components receive context from AdminLTERenderer via `get_context_data()` method and produce semantic AdminLTE 4-compatible HTML.
