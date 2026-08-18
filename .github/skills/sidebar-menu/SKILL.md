---
name: sidebar-menu
description: Guide for building the sidebar navigation menu in django-mvp by adding items to the AppMenu. Use when creating, modifying, or extending the sidebar menu — adding links, collapsible groups, section headers, badges, icons, or conditional visibility checks. Covers MenuItem, MenuGroup, MenuCollapse, the AppMenu global, and extra_context options.
---

# Sidebar Menu Construction

The sidebar menu is built by extending the global `AppMenu` instance in a `menus.py` file. The flex_menu app auto-discovers all `menus.py` modules at startup.

## Imports

```python
from flex_menu import MenuItem
from mvp.menus import AppMenu, MenuGroup, MenuCollapse
```

## Three Menu Item Types

### 1. MenuItem — Leaf link (navigates to a URL)

```python
MenuItem(
    name="dashboard",               # Unique identifier (required)
    view_name="myapp:dashboard",    # Django URL name (preferred over url=)
    extra_context={
        "label": "Dashboard",       # Display text in sidebar
        "icon": "speedometer",      # Bootstrap Icon name
    },
)
```

### 2. MenuGroup — Section header (non-clickable, uppercase label)

Groups items under a visual header. Sorted to the bottom of the menu automatically.

```python
MenuGroup(
    name="admin_section",
    extra_context={"label": "ADMINISTRATION"},
    children=[
        MenuItem(name="users", view_name="admin:users",
                 extra_context={"label": "Users", "icon": "people"}),
        MenuItem(name="settings", view_name="admin:settings",
                 extra_context={"label": "Settings", "icon": "gear"}),
    ],
)
```

### 3. MenuCollapse — Expandable/collapsible treeview

Creates a parent item with a chevron that expands to show children.

```python
MenuCollapse(
    name="reports",
    extra_context={"label": "Reports", "icon": "bar-chart"},
    children=[
        MenuItem(name="sales", view_name="reports:sales",
                 extra_context={"label": "Sales", "icon": "circle"}),
        MenuItem(name="analytics", view_name="reports:analytics",
                 extra_context={"label": "Analytics", "icon": "circle"}),
    ],
)
```

## Adding Items to AppMenu

Always use `AppMenu.extend([...])` in your app's `menus.py`:

```python
# myapp/menus.py
from flex_menu import MenuItem
from mvp.menus import AppMenu, MenuGroup, MenuCollapse

AppMenu.extend([
    MenuItem(
        name="home",
        view_name="home",
        extra_context={"label": "Home", "icon": "home"},
    ),
    MenuGroup(
        name="tools_section",
        extra_context={"label": "TOOLS"},
        children=[
            MenuCollapse(
                name="reporting",
                extra_context={"label": "Reporting", "icon": "graph-up"},
                children=[
                    MenuItem(name="weekly", view_name="reports:weekly",
                             extra_context={"label": "Weekly", "icon": "circle"}),
                ],
            ),
        ],
    ),
])
```

No imports or registration needed beyond this file — `flex_menu.apps.FlexMenuConfig.ready()` calls `autodiscover_modules("menus")` automatically.

## extra_context Reference

`extra_context` is spread directly into the template context. Supported keys:

| Key | Type | Default | Purpose |
|---|---|---|---|
| `label` | str | item `name` | Display text |
| `icon` | str | `"circle"` | Bootstrap Icon name (without `bi-` prefix) |
| `badge` | str | `""` | Badge text (e.g. "New", "3") |

## URL Resolution

Two ways to set a menu item's URL:

```python
# By Django URL name (preferred — auto-resolves, active state detection works)
MenuItem(name="home", view_name="home", ...)

# By static URL (for external links)
MenuItem(name="github", url="https://github.com/...", ...)
```

A MenuItem cannot have both a URL and children — it is either a leaf (link) or a parent (container).

## Conditional Visibility (check parameter)

Control item visibility per-request using `check`:

```python
from flex_menu.checks import user_is_staff, user_is_authenticated

# Only visible to staff
MenuItem(name="admin", view_name="admin:index", check=user_is_staff, ...)

# Only visible to authenticated users
MenuItem(name="profile", view_name="profile", check=user_is_authenticated, ...)

# Custom check function — signature: (request, **kwargs) -> bool
def has_feature_flag(request, **kwargs):
    return getattr(request, "feature_flags", {}).get("new_dashboard", False)

MenuItem(name="new_dash", view_name="new_dashboard", check=has_feature_flag, ...)
```

Available built-in checks from `flex_menu.checks`:

- `user_is_authenticated` / `user_is_anonymous`
- `user_is_staff` / `user_is_superuser`
- `user_in_any_group("editors", "admins")` / `user_in_all_groups(...)`
- `user_has_any_permission("app.view_model")` / `user_has_all_permissions(...)`
- `combine(check1, check2, operator="and"|"or")`
- `invert(check)` — negates a check

When a parent item has no visible children after checks, it hides itself automatically.

## Active State

Active state is automatic:

- Leaf items: `selected = True` when the current request URL matches the resolved item URL.
- Parent items (MenuCollapse): auto-expand when any descendant is active.

## Ordering Rules

- MenuItems and MenuCollapse items render in **declaration order**.
- MenuGroup items are automatically **sorted to the bottom** of the menu by the AdminLTERenderer.
- Within a MenuGroup, children render in declaration order.

## Menu Manipulation

```python
# Add items after initial extend
AppMenu.add(MenuItem(name="late_item", view_name="late", extra_context={...}))

# Insert at a specific position
AppMenu.insert(0, MenuItem(name="first", view_name="first", extra_context={...}))

# Insert after a named sibling
AppMenu.insert_after("home", MenuItem(name="after_home", ...))

# Remove an item
AppMenu.remove("old_item")

# Find an item by name
item = AppMenu.get("dashboard")
```

## Complete Example

```python
"""myapp/menus.py"""
from flex_menu import MenuItem
from flex_menu.checks import user_is_authenticated, user_is_staff

from mvp.menus import AppMenu, MenuCollapse, MenuGroup

AppMenu.extend([
    MenuItem(
        name="home",
        view_name="home",
        extra_context={"label": "Home", "icon": "home"},
    ),
    MenuItem(
        name="dashboard",
        view_name="dashboard",
        check=user_is_authenticated,
        extra_context={
            "label": "Dashboard",
            "icon": "speedometer",
            "badge": "New",
        },
    ),
    MenuCollapse(
        name="content",
        extra_context={"label": "Content", "icon": "folder"},
        children=[
            MenuItem(name="pages", view_name="pages:list",
                     extra_context={"label": "Pages", "icon": "file-earmark"}),
            MenuItem(name="media", view_name="media:list",
                     extra_context={"label": "Media", "icon": "image"}),
        ],
    ),
    MenuGroup(
        name="admin_section",
        extra_context={"label": "ADMIN"},
        children=[
            MenuItem(name="users", view_name="admin:users",
                     check=user_is_staff,
                     extra_context={"label": "Users", "icon": "people"}),
            MenuItem(name="site_settings", view_name="admin:settings",
                     check=user_is_staff,
                     extra_context={"label": "Settings", "icon": "gear"}),
        ],
    ),
    MenuGroup(
        name="resources",
        extra_context={"label": "RESOURCES"},
        children=[
            MenuItem(name="docs", url="https://docs.example.com",
                     extra_context={"label": "Documentation", "icon": "book"}),
        ],
    ),
])
```
