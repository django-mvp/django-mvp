# Menus — reference

Navigation for a project that installs django-mvp: the two menus the app shell renders, the
classes you build them from, the `extra_context` keys each renderer reads, and the rules
for active state and visibility.

## The model

Menus are declared in Python, at import time, in an app's `menus.py`. The app shell
renders `AppMenu` in the sidebar and `MobileFooterMenu` in the mobile dock, each through a
renderer you register by name in settings. `MobileFooterMenu` is not empty: it ships with
two items already attached, a sidebar-toggle item (`name="sidebar_toggle"`) and a home
link (`name="home"`, `view_name="home"`).

Everything is built on [django-flex-menus](https://github.com/SamuelJennings/django-flex-menus).
django-mvp supplies the renderers, the templates and two `MenuItem` subclasses.

## Settings

```python
# settings.py
FLEX_MENUS = {
    "renderers": {
        "sidebar": "mvp.renderers.SidebarRenderer",            # AppMenu
        "dock": "mvp.renderers.MobileFooterNavRenderer",       # MobileFooterMenu
    },
    # Optional. When true, a menu item whose view_name cannot be reversed logs a
    # warning to the "flex_menu.menu" logger. Defaults to settings.DEBUG.
    "log_url_failures": DEBUG,
}
```

The `"sidebar"` and `"dock"` keys are the ones the shell asks for by name. If a key is
missing, the render raises `ValueError` listing the renderers you did register. An
unstyled or blank region is a different problem (see common mistakes).

## Loading your `menus.py`

Two mechanisms, either is enough:

1. **Autodiscovery.** flex-menus' own `AppConfig.ready()` calls Django's
   `autodiscover_modules("menus")`, so a `menus.py` in any installed app is imported at
   startup with no wiring from you.
2. **Explicit import** in your own `AppConfig.ready()`:

```python
# myapp/apps.py
class MyAppConfig(AppConfig):
    name = "myapp"

    def ready(self):
        from . import menus  # noqa: F401
```

Import errors are **not** swallowed. Django's autodiscovery only ignores the case where
the app has no `menus` submodule at all. If the module exists and raises on import, that
exception propagates and startup fails with a traceback, rather than leaving a silently
empty menu. The usual causes of a missing menu are that the app is not in `INSTALLED_APPS`,
or that the `extend()` call sits inside a function that nothing calls.

## Classes

```python
# myapp/menus.py
from flex_menu import MenuItem
from mvp.menus import AppMenu, MobileFooterMenu, MenuCollapse, MenuGroup
```

| Class | From | What it is |
|---|---|---|
| `MenuItem` | `flex_menu` | One node: a link (has a URL) **or** a container (has children), never both. |
| `MenuGroup` | `mvp.menus` | `MenuItem` subclass. A non-clickable section heading with its children listed below it. |
| `MenuCollapse` | `mvp.menus` | `MenuItem` subclass. An expandable group. Sets `extra_context["collapsible"] = True` for you. |
| `AppMenu` | `mvp.menus` | The sidebar menu instance. Ships empty. |
| `MobileFooterMenu` | `mvp.menus` | The mobile dock menu instance. Ships with the two items above. |

`MenuItem`, `MenuGroup` and `MenuCollapse` share one signature:

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

**Constructor argument or `extra_context` key?** `view_name`, `url`, `params`, `check`,
`children` and `parent` are constructor arguments. `label`, `icon`, `badge` and `toggle`
are `extra_context` keys. Passing `label="Home"` as a constructor argument does not fail
loudly. It lands on the node as an arbitrary attribute and nothing renders it.

`params` is only appended to a static `url=` string, and is ignored for `view_name` and for
callable URLs. Passing both a URL (`view_name` or `url`) and `children` raises `ValueError`
at import.

## `extra_context` keys, by renderer

These are the keys the shipped templates read. Anything else you put in `extra_context` is
available to a template of your own but is ignored by the package.

| Key | Sidebar leaf | Sidebar parent | Dock item |
|---|---|---|---|
| `label` | Link text, and the hover tip when the sidebar is collapsed to icons | Heading text / group title | Text under the icon |
| `icon` | Yes (django-easy-icons name) | Only when the group is collapsible. The parent template passes the icon through, but the group component renders it inside its collapsible branch alone, so a `MenuGroup` shows its label text and drops the icon silently. `MenuCollapse` draws it | Yes |
| `badge` | Yes — small badge beside the label | **Not passed by the parent template.** Treat a badge on a group as unsupported | No |
| `collapsible` | — | Yes. `True` makes the group expandable, otherwise it renders as a plain section heading. `MenuCollapse` sets it | No |
| `toggle` | No | No | Yes — the id of a drawer toggle to flip instead of navigating |

`label` defaults to the item's `name` when absent, so an item with no `label` shows its
identifier.

## Active state

The rule is **exact string equality between the item's resolved URL and `request.path`**.
There is no prefix matching and no view-name comparison.

Consequences you have to design around:

- A detail page does not highlight its list item. `/products/` and `/products/12/` are
  different strings, so browsing to a product leaves "Products" unhighlighted.
- A URL carrying a querystring never matches. `request.path` excludes the query, so an
  item built with `params={...}` — or a hard-coded `url` containing `?` — can never be
  active.
- A parent becomes active when any of its visible descendants is active. This propagates
  all the way up the chain, and it is what makes a `MenuCollapse` render open on the page
  its child points at.

## Visibility — `check`

`check` takes either a plain boolean or a callable `check(request, **kwargs) -> bool`. It
is evaluated at render time, once per request per menu (the processed tree is cached on the
request object), and it receives the `request` plus any keyword arguments passed to
`{% render_menu %}`. An item that fails the check is dropped, along with its subtree.

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

`flex_menu.checks` also ships `user_is_superuser`, `user_is_anonymous`, `user_is_active`,
`user_in_any_group(*groups)`, `user_has_any_permission(*perms)`, `debug_mode_only`,
`combine_checks(*checks, operator="and")` and `negate_check(check)`, among others.

## Nesting

`MenuGroup` is a heading. `MenuCollapse` is an expandable group. Both take `children`, and
they nest inside each other freely.

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

Always pass `extra_context` as a keyword argument, as above. `MenuCollapse` reads it by
keyword when it injects `collapsible`, so a positional `extra_context` is not retained.

Use `AppMenu.extend([...])` or `AppMenu.append(item)`. `AppMenu.children` is a tuple —
`AppMenu.children.extend([...])` raises `AttributeError`. Assigning
`AppMenu.children = [...]` replaces the whole list, and `AppMenu.pop("name")` detaches one
child.

## The mobile dock

Items reach the dock by being attached to `MobileFooterMenu`, exactly as with `AppMenu`:

```python
# myapp/menus.py
MobileFooterMenu.append(
    MenuItem(name="inbox", view_name="inbox",
             extra_context={"label": "Inbox", "icon": "envelope"})
)
```

Three item shapes render, in this order of precedence: a `toggle` key produces a control
that flips the drawer with that element id (the shipped `sidebar_toggle` uses
`"mvp-app-toggle"`, the sidebar's drawer), a resolvable URL produces a navigation link,
and neither produces an inert placeholder.

The dock's own visibility is **hard-coded to hide from the `md` breakpoint up**. It does
not follow `MVP_CONFIG["layout"]["sidebar"]["breakpoint"]`. If you need a different
threshold, override the `cotton/app/dock.html` template in your project.

To drop the pre-seeded items, assign `MobileFooterMenu.children = [ ...yours... ]` or pop
them by name. The shipped `home` item points at a URL named `home`. In a project that has
no such URL name it silently disappears, because a leaf whose URL will not resolve is
hidden.

## Rendering a menu elsewhere

```django
{% load flex_menu %}
{% render_menu "AppMenu" renderer="sidebar" %}
{% render_menu project_menu renderer="sidebar" project=project pk=project.pk %}
```

`{% render_menu menu renderer=... include_media=True **kwargs %}` takes a menu name or a
menu instance, a renderer name or instance (required), and arbitrary keyword arguments
that are forwarded to every `check` callable and to URL resolution. An unknown menu name
raises `TemplateSyntaxError`. Inside a renderer template of your own,
`{% render_item child renderer=renderer %}` renders one child, and `{% process_menu %}`
returns the processed tree without rendering it.

To point the sidebar at a different menu, pass its name to the shell component:
`<c-app.sidebar menu="AdminMenu" />`.

`SidebarRenderer` and `MobileFooterNavRenderer` are the only renderers the package
ships. For horizontal navigation, build it from the `c-menu` components directly or
write a renderer of your own.

## Common mistakes

- **Item never appears.** The module was never imported (app missing from
  `INSTALLED_APPS`, or the `extend()` call sits inside a function), or the item was
  constructed without a `parent` and never attached — a bare `MenuItem(...)` defaults to
  flex-menus' global root, not to `AppMenu`. Run `python manage.py render_menu` to print
  the whole registered tree, or `--name AppMenu` for one menu.
- **Sidebar renders but is empty.** Every item was filtered out. A leaf whose `view_name`
  will not reverse is hidden, a leaf whose `check` returns false is hidden, and a container
  left with no visible children hides itself. Set `FLEX_MENUS["log_url_failures"] = True`
  to see the reversal failures.
- **`view_name` does not resolve.** The name is wrong, unnamespaced (`"user-list"` where
  the app defines `"users:list"`), or the pattern needs arguments. Pass those arguments as
  keyword arguments to `{% render_menu %}`. They are filtered down to the ones the pattern
  captures.
- **`ValueError` at import.** An item was given both a URL and children. Make it a
  container and add the link as its first child.

---

Back to [SKILL.md](../SKILL.md).
