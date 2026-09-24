# Navigation

django-mvp renders three menus from Python definitions, using
[django-flex-menus](https://github.com/SamuelJennings/django-flex-menus):

- **`AppMenu`** — the sidebar navigation.
- **`MobileFooterMenu`** — the bottom dock on small screens (pre-populated with a
  sidebar toggle).
- **`AccountCenterMenu`** — the [Account Center](account-center.md)'s own navigation,
  rendered beside its pages. Ships with the entry for its own landing page; extend it
  the same way as `AppMenu`.

Each is a tree of nodes built at import time and turned into markup by a renderer
registered under `FLEX_MENUS["renderers"]` in settings.

## Menu classes

```python
from flex_menu import MenuItem
from mvp.menus import AppMenu, MobileFooterMenu, MenuCollapse, MenuGroup
```

| Class | From | What it is |
| --- | --- | --- |
| `MenuItem` | `flex_menu` | One node: a link (has a URL) **or** a container (has children), never both. |
| `MenuGroup` | `mvp.menus` | `MenuItem` subclass. A non-clickable section heading with its children listed below it. |
| `MenuCollapse` | `mvp.menus` | `MenuItem` subclass. An expandable group. Sets `extra_context["collapsible"] = True` for you. |
| `AppMenu` | `mvp.menus` | The sidebar menu instance. Ships empty. |
| `MobileFooterMenu` | `mvp.menus` | The mobile dock menu instance. Ships with the sidebar-toggle item. |
| `AccountCenterMenu` | `mvp.menus` | The Account Center's own navigation. Ships with the entry for its own landing page. |

`MenuItem`, `MenuGroup` and `MenuCollapse` share one constructor:

```python
MenuItem(
    name,               # str, required. Unique id, and the fallback label.
    view_name="",       # str. Django URL name, resolved with reverse().
    url="",             # str, or callable(request, *args, **kwargs) -> str.
    params=None,        # dict. Query params appended to a *static* url= string only.
    parent=None,        # MenuItem. Omitted attaches to flex-menus' global root.
    children=None,      # list[MenuItem]. Mutually exclusive with view_name/url.
    check=True,         # bool, or callable(request, **kwargs) -> bool.
    extra_context=None, # dict. Keys handed to the renderer templates.
)
```

`AppMenu` and `MobileFooterMenu` are `Menu` instances —
`Menu(name, children=None, check=True, extra_context=None)`. A `Menu` always attaches
itself to the global root and never carries a URL.

`view_name`, `url`, `params`, `check`, `children` and `parent` are constructor
arguments; `label`, `icon` and `badge` are `extra_context` keys instead. Passing
`label="Home"` as a constructor argument does not fail loudly — it lands on the node
as a plain attribute and nothing renders it, so keep display data inside
`extra_context`. `params` is appended to a static `url=` string only; it is ignored
for `view_name` and for callable URLs.

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

Then make sure the module is imported at startup. flex-menus' own app config already
calls Django's `autodiscover_modules("menus")`, so a `menus.py` in any installed app is
picked up with no wiring from you. If you would rather be explicit — or your app
doesn't follow the autodiscovery convention — import it yourself:

```python
# myapp/apps.py
class MyappConfig(AppConfig):
    name = "myapp"

    def ready(self):
        from . import menus  # noqa: F401
```

Either way, an import error in `menus.py` is not swallowed: it propagates and startup
fails with a traceback, rather than leaving a silently empty menu.

### Item options (`extra_context`)

| Key | Effect |
| --- | --- |
| `label` | display text |
| `icon` | [easy-icons](getting-started.md#configure-icons) icon name |
| `badge` | badge text next to the label |

`view_name` (a `MenuItem` constructor argument, not `extra_context`) is resolved with
`reverse()`; pass `url` instead for external or hard-coded links. `label` defaults to
the item's `name` when absent, so an item with no `label` shows its identifier.

These three keys aren't read the same way everywhere. A `MenuGroup` heading (a
non-collapsible parent) shows its `label` but drops `icon` and `badge` — the sidebar's
group template only renders the icon and badge inside the `<details>` branch used by
collapsible groups, so `MenuCollapse` draws both and a plain `MenuGroup` draws neither.
In the mobile dock, `icon` and `label` render but `badge` does not.

## Active state

Active-state detection is automatic, and the rule behind it is **exact string equality
between the item's resolved URL and `request.path`** — there is no prefix matching and
no view-name comparison. In the [icon-rail collapse mode](layout.md#sidebar-collapse-mode)
each item's label also becomes its hover tooltip regardless of active state.

Consequences worth designing around:

- A detail page does not highlight its list item. `/products/` and `/products/12/` are
  different strings, so browsing to a product leaves "Products" unhighlighted.
- A URL carrying a querystring never matches. `request.path` excludes the query, so an
  item built with `params={...}` — or a hard-coded `url` containing `?` — can never be
  active.
- A parent becomes active when any of its visible descendants is active. This
  propagates all the way up the chain, and it is what makes a `MenuCollapse` render
  open on the page its child points at.

## Visibility — `check`

`check` takes either a plain boolean or a callable `check(request, **kwargs) -> bool`.
It is evaluated at render time, once per request per menu (the processed tree is
cached on the request object), and it receives the `request` plus any keyword
arguments passed to `{% render_menu %}`. An item that fails the check is dropped,
along with its subtree.

```python
# myapp/menus.py
from flex_menu.checks import user_is_authenticated

AppMenu.extend([
    MenuItem(name="dashboard", view_name="dashboard", check=user_is_authenticated,
             extra_context={"label": "Dashboard", "icon": "home"}),
    MenuItem(name="audit", view_name="audit", check=lambda request, **kw: request.user.is_staff,
             extra_context={"label": "Audit log", "icon": "list"}),
])
```

`flex_menu.checks` also ships `user_is_superuser`, `user_is_anonymous`,
`user_is_active`, `user_in_any_group(*groups)`, `user_has_any_permission(*perms)`,
`debug_mode_only`, `combine_checks(*checks, operator="and")` and
`negate_check(check)`, among others.

## Nesting

`MenuGroup` and `MenuCollapse` both take `children`, and they nest inside each other
freely:

```python
# myapp/menus.py
AppMenu.extend([
    MenuGroup(name="admin", extra_context={"label": "Administration"}, children=[
        MenuItem(name="users", view_name="user-list",
                 extra_context={"label": "Users", "icon": "people"}),
        MenuCollapse(name="reports", extra_context={"label": "Reports", "icon": "graph-up"},
                     children=[
            MenuItem(name="sales", view_name="report-sales",
                     extra_context={"label": "Sales"}),
        ]),
    ]),
])
```

A `MenuGroup` or `MenuCollapse` with no visible children is left out of the menu, whether it
was declared empty or every child is hidden by its `check`. You can declare a section before
its first page exists, and it appears once a page is added to it.

Use `AppMenu.extend([...])` or `AppMenu.append(item)` to attach items. `AppMenu.children`
is a tuple, so `AppMenu.children.extend([...])` raises `AttributeError`. Assigning
`AppMenu.children = [...]` replaces the whole list, and `AppMenu.pop("name")` detaches
one child.

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

Three item shapes render, in this order of precedence: a `toggle` key produces a
control that flips a drawer element by id (the shipped `sidebar_toggle` item uses
`"mvp-app-toggle"`, the sidebar's drawer), a resolvable URL produces a navigation link,
and neither produces an inert placeholder button.

An `attrs` key is handed straight to the rendered element, the same pass-through every
other component supports — an Alpine directive to open a modal, an `aria-label`
override, a `data-*` hook:

```python
MenuItem(name="log-episode", extra_context={
    "label": "Log episode", "icon": "plus",
    "attrs": {"x-on:click": "modalOpen = true"},
})
```

The dock's own visibility follows `MVP_CONFIG["layout"]["sidebar"]["breakpoint"]`, the
same setting the desktop header widgets key off. If you need a different threshold,
override the `cotton/app/dock.html` template in your project.

To drop the pre-seeded sidebar-toggle item, assign
`MobileFooterMenu.children = [ ...yours... ]` or pop it by name, the same way described
for `AppMenu` above.

## Rendering menus elsewhere

Any registered menu can be rendered with a flex-menus renderer:

```html
{% load flex_menu %}
{% render_menu "AppMenu" renderer="sidebar" %}
```

An unknown menu name raises `TemplateSyntaxError`.

Renderers shipped by django-mvp (`mvp.renderers`): `SidebarRenderer` and
`MobileFooterNavRenderer` — the only renderers the package ships. Register them (plus
any of your own) in settings — the app shell expects the `"sidebar"` and `"dock"`
keys:

```python
FLEX_MENUS = {
    "renderers": {
        "sidebar": "mvp.renderers.SidebarRenderer",
        "dock": "mvp.renderers.MobileFooterNavRenderer",
    },
    # Optional. When true, a menu item whose view_name cannot be reversed logs a
    # warning to the "flex_menu.menu" logger. Defaults to settings.DEBUG.
    "log_url_failures": DEBUG,
}
```

If a key you asked for is missing, resolving that renderer raises `ValueError` listing
the renderers you did register. An unstyled or blank region is a different problem
(see common mistakes, below).

Renderers map menu nodes onto the `c-menu.*` / dock templates, so a custom renderer or
template override changes the markup without touching your Python menu definitions.
Inside a renderer template of your own, `{% render_item child renderer=renderer %}`
renders one child, and `{% process_menu %}` returns the processed tree without
rendering it.

For fully hand-built menus, use the [`c-menu` components](components.md#navigation)
directly. To point the sidebar at a different menu, pass its name to the shell
component instead: `<c-app.sidebar menu="AdminMenu" />`.

## A menu's accessible name

The sidebar renderer's container renders `c-menu`, which is a `<ul role="navigation">` —
a landmark a screen reader announces by name. That name comes from the menu's own
`extra_context["label"]`, so a project rendering a second menu through the sidebar
renderer gives it one, the same way `AppMenu` and `AccountCenterMenu` already do:

```python
# myapp/menus.py
from flex_menu import Menu
from django.utils.translation import gettext_lazy as _

AdminMenu = Menu("AdminMenu", extra_context={"label": _("Administration")})
```

Two landmarks with the same name — or no name at all — leave a screen reader user
unable to tell them apart. A `label` passed directly to `{% render_menu %}` overrides
the menu's own, for the one call that needs it.

## Common mistakes

- **Item never appears.** The module was never imported (app missing from
  `INSTALLED_APPS`, or the `extend()` call sits inside a function nothing calls), or
  the item was constructed without a `parent` and never attached — a bare
  `MenuItem(...)` defaults to flex-menus' global root, not to `AppMenu`. Run
  `python manage.py render_menu` to print the whole registered tree, or
  `--name AppMenu` for one menu.
- **Sidebar renders but is empty.** Every item was filtered out. A leaf whose
  `view_name` will not reverse is hidden, a leaf whose `check` returns false is
  hidden, and a container with no visible children hides itself. Set
  `FLEX_MENUS["log_url_failures"] = True` to see the reversal failures.
- **`view_name` does not resolve.** The name is wrong, unnamespaced (`"user-list"`
  where the app defines `"users:list"`), or the pattern needs arguments. Pass those
  arguments as keyword arguments to `{% render_menu %}` — they are filtered down to
  the ones the pattern captures.
- **`ValueError` at import.** An item was given both a URL and children. Make it a
  container and add the link as its first child.
