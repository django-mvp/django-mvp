# Data Model: Configurable Site Navigation Menu System

**Feature**: 004-site-navigation
**Date**: January 7, 2026
**Purpose**: Define entity structure, relationships, and properties for menu system

## Overview

The menu system uses django-flex-menus' tree-based structure (via anytree) without database backing. All menu configuration is code-defined and assembled at runtime during Django app initialization.

## Entity Definitions

### AppMenu (Menu Instance)

The root menu container that holds all top-level navigation items.

**Properties**:

- `name`: str - Unique identifier for the menu (e.g., "AppMenu")
- `children`: List[MenuItem] - Top-level menu items (initially empty list `[]`, can be modified by user apps)
- `parent`: None - Root menus have no parent

**Relationships**:

- **Has many** MenuItem (as children)
- **Provides to** Custom renderer for processing and template selection

**State**:

- **Initialization**: Empty list of children
- **Runtime**: Populated as Django apps import and add items
- **Rendering**: Processed by custom renderer, sorted into singles and groups

**Validation Rules**:

- Name must be unique within application
- Children must be MenuItem instances
- Circular references prevented by anytree validation

**Lifecycle**:

1. Created during `mvp` app initialization
2. Extended by user apps during their initialization
3. Processed during template rendering via `{% render_menu %}` tag
4. Remains in memory for request duration (thread-safe via django-flex-menus)

---

### MenuItem

Represents a single navigation item (link, parent with children, or group item).

**Properties**:

- `name`: str - Unique identifier within parent scope (e.g., "home", "admin_users")
- `view_name`: str | None - Django URL name (e.g., "app:view_name", or "#" for non-clickable parents)
- `extra_context`: dict - Custom data for rendering (label, icon, CSS classes, badge, group_header, etc.)
- `children`: List[MenuItem] | None - Nested menu items (for hierarchical menus)
- `parent`: Menu | MenuItem - Reference to parent container
- `depth`: int - Nesting level (0 for root, 1+ for nested), automatically managed by anytree
- `template_name`: str | None - Override template for this specific item (optional)

**Common extra_context Keys**:

- `label`: str - Display text (e.g., "Dashboard", "User Management")
- `icon`: str - Icon name for django-easy-icons (e.g., "house", "gear")
- `icon_set`: str - Icon set override (default: Bootstrap Icons)
- `classes`: str - Additional CSS classes for `<li>` element
- `link_classes`: str - Additional CSS classes for `<a>` element
- `badge`: str - Badge text/number to display
- `badge_classes`: str - Badge styling classes
- `group_header`: str - Header text if this item starts a group (e.g., "ADMIN TOOLS")
- `permission`: str | None - Required permission to display item
- `url_params`: dict - Static URL parameters (for items with parameterized URLs)

**Relationships**:

- **Belongs to** Menu or MenuItem (as parent)
- **Has many** MenuItem (as children, optional)
- **Used by** Custom renderer to select templates and provide context

**State**:

- **Definition**: Created with name, view_name, and extra_context
- **Hierarchy**: Parent/child relationships established via `children` parameter
- **Rendering**: Classified as single (no children) or parent (has children)

**Validation Rules**:

- Name must be unique within parent's children
- view_name should be valid Django URL name (or "#" for non-clickable items)
- extra_context must be serializable dictionary
- Circular parent-child relationships prevented by anytree

**Types** (determined at runtime):

- **Single Item**: No children, renders as clickable link, appears at top of menu
- **Parent Item**: Has children, renders with arrow indicator, children in nested list
- **Group Item**: Parent item with `group_header` in extra_context, renders header before item

---

### AdminLTERenderer (Custom Renderer)

Bridges django-flex-menus with Cotton components for AdminLTE 4 sidebar rendering.

**Properties**:

- `templates`: dict - Maps depth and item type to template paths
- `request`: HttpRequest - Current request (for active state detection)
- `context`: dict - Template rendering context

**Relationships**:

- **Processes** AppMenu to generate rendered HTML
- **Selects** templates based on depth and item type (parent vs leaf)
- **Provides** context to Cotton components via c-vars

**State**:

- **Initialization**: Receives menu instance and render kwargs
- **Processing**: Walks tree structure, categorizes items
- **Sorting**: Separates singles from groups
- **Rendering**: Applies templates in order

**Template Selection Logic**:

```
Depth 0 (Container):
  → menus/container.html (renders top-level <nav> and <ul>)

Depth 1 (Top-level items):
  - Leaf (no children) → menus/single-item.html
  - Parent (has children) → menus/parent-item.html
    - If group_header in extra_context → inject menus/group-header.html before item

Depth 2+ (Nested items):
  - Leaf → menus/nested-item.html
  - Parent → menus/nested-parent.html
```

**Context Data Enrichment**:

- Adds `archived` flag (compares current URL with item view_name)
- Adds `has_children` boolean
- Adds `has_icon` boolean
- Adds `has_badge` boolean
- Passes through all extra_context keys as c-vars
- Provides parent context for menu-open state detection

---

## Entity Relationships Diagram

```
AppMenu (root)
├── name: "AppMenu"
├── children: [MenuItem, MenuItem, ...]
│
├─► MenuItem (single item, depth=1)
│   ├── name: "home"
│   ├── view_name: "app:home"
│   ├── extra_context: {label: "Home", icon: "house"}
│   ├── children: []
│   └── parent: AppMenu
│
├─► MenuItem (group parent, depth=1)
│   ├── name: "admin"
│   ├── view_name: "#"
│   ├── extra_context: {label: "Administration", group_header: "ADMIN"}
│   ├── children: [MenuItem, MenuItem]
│   │   │
│   │   ├─► MenuItem (nested, depth=2)
│   │   │   ├── name: "users"
│   │   │   ├── view_name: "app:admin_users"
│   │   │   ├── extra_context: {label: "Users", icon: "people"}
│   │   │   └── parent: admin MenuItem
│   │   │
│   │   └─► MenuItem (nested, depth=2)
│   │       ├── name: "settings"
│   │       ├── view_name: "app:admin_settings"
│   │       ├── extra_context: {label: "Settings", icon: "gear"}
│   │       └── parent: admin MenuItem
│   │
│   └── parent: AppMenu
│
└─► MenuItem (single item, depth=1)
    ├── name: "profile"
    ├── view_name: "app:profile"
    ├── extra_context: {label: "Profile", icon: "person-circle"}
    ├── children: []
    └── parent: AppMenu
```

## Data Flow

### Menu Assembly Flow

```
1. Django App Initialization
   ↓
2. mvp.menus module loads
   → AppMenu = Menu("AppMenu", children=[])
   ↓
3. User apps import AppMenu
   → from mvp.menus import AppMenu
   ↓
4. User apps add MenuItems
   → AppMenu.children.append(MenuItem(...))
   → AppMenu.children.extend([MenuItem(...), ...])
   ↓
5. Template rendering triggered
   → {% render_menu 'AppMenu' renderer='adminlte' %}
   ↓
6. django-flex-menus processes menu
   → Walks tree structure
   → Resolves view_name to URLs
   ↓
7. AdminLTERenderer sorts items
   → singles = [items without children]
   → groups = [items with children]
   ↓
8. Renderer selects templates
   → Depth 0 → container
   → Depth 1 singles → single-item.html
   → Depth 1 groups → parent-item.html with group-header.html
   → Depth 2+ → nested templates
   ↓
9. Templates receive context
   → c_label, c_url, c_icon, c_classes, etc.
   ↓
10. Cotton components render HTML
    → <nav><ul class="sidebar-menu">...</ul></nav>
```

### Active State Detection Flow

```
1. Request arrives
   ↓
2. Django resolves URL
   → request.resolver_match.url_name set
   ↓
3. Menu rendering begins
   → {% render_menu %} called with request in context
   ↓
4. Renderer processes each item
   → get_context_data(item, request=request)
   ↓
5. Compare URLs
   → current = request.resolver_match.url_name
   → item_name = item.view_name.split(':')[-1]
   ↓
6. Set active flag
   → context['archived'] = (current == item_name)
   ↓
7. Check parent chain
   → If any child is active, parent.is_open = True
   ↓
8. Templates apply classes
   → <a class="nav-link {% if archived %}active{% endif %}">
   → <li class="nav-item {% if is_open %}menu-open{% endif %}">
```

## Extension Points

### Adding Custom Context Data

Users can add arbitrary data to `extra_context`:

```python
MenuItem(
    name="reports",
    view_name="app:reports",
    extra_context={
        "label": "Reports",
        "icon": "file-text",
        "badge": "New",
        "badge_classes": "text-bg-warning",
        "data_attrs": {"toggle": "tooltip", "title": "View reports"},
    }
)
```

### Custom Template Override

Individual items can override their template:

```python
MenuItem(
    name="custom",
    view_name="app:custom",
    template_name="menus/custom-widget.html",
    extra_context={"label": "Custom Widget"}
)
```

### Permission-Based Visibility

While not implemented in Phase 1, the structure supports it:

```python
MenuItem(
    name="admin_only",
    view_name="app:admin_panel",
    extra_context={
        "label": "Admin Panel",
        "permission": "app.can_admin"
    }
)
```

Future renderer can filter items based on `request.user.has_perm()`.

## Storage and Persistence

**No Database Storage**: Menus are defined in Python code, not stored in database.

**Advantages**:

- Version controlled with application code
- No migrations required
- Faster (no database queries)
- Easier testing (no fixtures needed)

**Trade-offs**:

- No runtime menu modification
- Application restart required for menu changes
- Not suitable for user-customizable menus

This trade-off aligns with django-mvp's configuration-driven philosophy and the spec requirement for code-based menu definition.

## Summary

The data model uses django-flex-menus' tree structure with three key entities:

1. **AppMenu**: Root container, initially empty, populated by user apps
2. **MenuItem**: Tree nodes with view_name, extra_context, and optional children
3. **AdminLTERenderer**: Processes tree, sorts singles/groups, selects templates

The structure supports unlimited nesting, permission-based visibility (future), and arbitrary custom data while maintaining simplicity and following Django/AdminLTE conventions.
