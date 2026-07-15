# Menu patterns (sidebar + mobile dock)

django-mvp renders two Python-defined menus via
[django-flex-menus](https://github.com/SamuelJennings/django-flex-menus):

- **`AppMenu`** — the sidebar, rendered by `mvp.renderers.SidebarRenderer` (`"sidebar"` key).
- **`MobileFooterMenu`** — the mobile bottom dock, rendered by
  `mvp.renderers.MobileFooterNavRenderer` (`"dock"` key); pre-populated with a
  sidebar-toggle item.

Import the building blocks from `mvp.menus`:

```python
from flex_menu import MenuItem
from mvp.menus import AppMenu, MobileFooterMenu, MenuGroup, MenuCollapse
```

## Flat menu

```python
AppMenu.extend([
    MenuItem(name="home", view_name="home",
             extra_context={"label": "Home", "icon": "home"}),
    MenuItem(name="products", view_name="product-list",
             extra_context={"label": "Products", "icon": "box-seam"}),
])
```

## Section header — `MenuGroup`

Renders a non-clickable label followed by its children.

```python
AppMenu.extend([
    MenuGroup(name="admin", extra_context={"label": "Administration"}, children=[
        MenuItem(name="users", view_name="user-list",
                 extra_context={"label": "Users", "icon": "people"}),
        MenuItem(name="settings", view_name="settings",
                 extra_context={"label": "Settings", "icon": "settings"}),
    ]),
])
```

## Collapsible group — `MenuCollapse`

Renders as a `<details>` element: a clickable parent that expands/collapses its children.

```python
AppMenu.extend([
    MenuCollapse(name="reports", extra_context={"label": "Reports", "icon": "graph-up"},
                 children=[
        MenuItem(name="sales", view_name="report-sales",
                 extra_context={"label": "Sales"}),
        MenuItem(name="export", view_name="report-export",
                 extra_context={"label": "Export", "icon": "download"}),
    ]),
])
```

Groups and collapses nest arbitrarily (a `MenuGroup` may contain a `MenuCollapse`, etc.).

## Item options

| Where | Key | Effect |
|---|---|---|
| `MenuItem(...)` arg | `view_name` | resolved with `reverse()` |
| `MenuItem(...)` arg | `url` | external / hard-coded link (use instead of `view_name`) |
| `MenuItem(...)` arg | `check` | visibility callable (see below) |
| `extra_context` | `label` | display text |
| `extra_context` | `icon` | easy-icons name |
| `extra_context` | `badge` | badge text beside the label |

`reverse_lazy` is fine for `url=` when building items at import time.

## Active state

Automatic — the renderer highlights the item whose URL matches the current request, and
expands the ancestor groups. In `collapse="icons"` (icon-rail) mode each item's `label`
becomes its hover tooltip. No manual `active` handling needed.

## Visibility checks

Pass a `check` callable to hide items conditionally:

```python
from flex_menu.checks import (
    user_is_authenticated, user_is_staff, user_is_superuser,
    user_in_any_group, user_has_any_permission,
)

MenuItem(name="dashboard", view_name="home", check=user_is_authenticated,
         extra_context={"label": "Dashboard", "icon": "home"})

# Custom callable — receives the request
MenuItem(name="beta", view_name="beta",
         check=lambda request, **kw: request.user.profile.is_beta_tester,
         extra_context={"label": "Beta"})
```

## Mobile dock

`MobileFooterMenu` renders below the sidebar breakpoint via `<c-app.dock>`. It ships with
a sidebar-toggle item (a `<label for="mvp-app-toggle">` that flips the drawer checkbox).
Extend it like `AppMenu`:

```python
MobileFooterMenu.extend([
    MenuItem(name="home", view_name="home",
             extra_context={"label": "Home", "icon": "home"}),
])
```

To drop the default toggle, reassign `MobileFooterMenu.children = [ ...your items... ]`.

## Loading the module

Either mechanism works:

1. `flex_menu`'s `FlexMenuConfig.ready()` autodiscovers `menus.py` in every installed app.
2. Explicitly import it in your `AppConfig.ready()`: `from . import menus  # noqa: F401`.

Requirements: the app is in `INSTALLED_APPS`, `menus.py` exists, `AppMenu.extend([...])`
runs at module level (not inside a function), and the module imports without error (import
errors during autodiscover are silently swallowed).

## Rendering a menu elsewhere

```django
{% load flex_menu %}
{% render_menu "AppMenu" renderer="sidebar" %}
```

Renderers shipped by `mvp.renderers`: `SidebarRenderer`, `MobileFooterNavRenderer`,
`NavRenderer`. Register the ones you use in `FLEX_MENUS["renderers"]`. For fully
hand-built menus, use the `c-menu.*` components directly instead of a Python menu.
