# Navigation

django-mvp renders two menus from Python definitions, using
[django-flex-menus](https://github.com/SamuelJennings/django-flex-menus):

- **`AppMenu`** — the sidebar navigation.
- **`MobileFooterMenu`** — the bottom dock on small screens (pre-populated with a
  sidebar toggle).

## Defining the sidebar menu

Create `menus.py` in your app and extend `AppMenu`:

```python
# myapp/menus.py
from flex_menu import MenuItem

from mvp.menus import AppMenu, MenuCollapse, MenuGroup

AppMenu.extend([
    # Single item
    MenuItem(
        name="dashboard",
        view_name="dashboard",           # resolved with reverse()
        extra_context={"label": "Dashboard", "icon": "home"},
    ),

    # Section with a header
    MenuGroup(
        name="admin_section",
        extra_context={"label": "Administration"},
        children=[
            MenuItem(name="users", view_name="user-list",
                     extra_context={"label": "Users", "icon": "people"}),
            MenuItem(name="settings", view_name="settings",
                     extra_context={"label": "Settings", "icon": "settings",
                                    "badge": "3"}),
        ],
    ),

    # Collapsible group (<details> element)
    MenuCollapse(
        name="reports",
        extra_context={"label": "Reports", "icon": "graph-up"},
        children=[
            MenuItem(name="sales", view_name="report-sales",
                     extra_context={"label": "Sales"}),
        ],
    ),
])
```

Then make sure the module is imported at startup:

```python
# myapp/apps.py
class MyappConfig(AppConfig):
    name = "myapp"

    def ready(self):
        from . import menus  # noqa: F401
```

### Item options (`extra_context`)

| Key | Effect |
| --- | --- |
| `label` | display text |
| `icon` | [easy-icons](getting-started.md#configure-icons) icon name |
| `badge` | badge text next to the label |

`view_name` (a `MenuItem` constructor argument, not `extra_context`) is resolved with
`reverse()`; pass `url` instead for external or hard-coded links. Active-state detection
is automatic — the item matching the current URL gets the highlight, and in the
[icon-rail collapse mode](layout.md#sidebar-collapse-mode) each item's label becomes its
hover tooltip.

## The mobile dock

Below the sidebar breakpoint, `<c-app.dock>` renders `MobileFooterMenu` as a bottom
navigation bar. It ships with a single item that toggles the sidebar drawer; extend it
the same way as `AppMenu`:

```python
from mvp.menus import MobileFooterMenu

MobileFooterMenu.extend([
    MenuItem(name="home", view_name="home",
             extra_context={"label": "Home", "icon": "home"}),
])
```

## Rendering menus elsewhere

Any registered menu can be rendered with a flex-menus renderer:

```html
{% load flex_menu %}
{% render_menu "AppMenu" renderer="sidebar" %}
```

Renderers shipped by django-mvp (`mvp.renderers`): `SidebarRenderer`,
`MobileFooterNavRenderer`, and `NavRenderer`. Register them (plus any of your own) in
settings — the app shell expects the `"sidebar"` and `"dock"` keys:

```python
FLEX_MENUS = {
    "renderers": {
        "sidebar": "mvp.renderers.SidebarRenderer",
        "dock": "mvp.renderers.MobileFooterNavRenderer",
    },
}
```

Renderers map menu nodes onto the `c-menu.*` / dock templates, so a custom renderer or
template override changes the markup without touching your Python menu definitions.

For fully hand-built menus, use the [`c-menu` components](components.md#navigation)
directly.
