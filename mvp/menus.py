"""The menus a project builds its navigation from.

Navigation is a tree of ``MenuItem`` objects held in two singletons this module
exports. A project imports them, appends its own items, and a renderer turns
the tree into markup. The renderers live in :mod:`mvp.renderers` and are
registered under ``FLEX_MENUS["renderers"]``.

- ``AppMenu`` — the sidebar tree. Ships empty.
- ``MobileFooterMenu`` — the mobile dock. Ships with the sidebar toggle only.

Each item carries its display data in ``extra_context``: ``label`` and ``icon``
are read by every renderer, ``badge`` by the sidebar templates, and ``toggle``
by the dock. An item resolves its URL from ``view_name`` or ``url``, and an
item whose URL will not resolve is dropped from the rendered menu, so a project
adding an item is responsible for the URL name existing.

Example, in your app's ``menus.py``::

    from flex_menu import MenuItem

    from mvp.menus import AppMenu, MenuCollapse, MenuGroup

    AppMenu.extend(
        [
            MenuItem(
                name="dashboard",
                view_name="yourapp:dashboard",
                extra_context={"label": "Dashboard", "icon": "speedometer"},
            ),
            MenuGroup(
                name="administration",
                extra_context={"label": "Administration"},
                children=[
                    MenuItem(name="users", view_name="admin:users"),
                    MenuItem(name="settings", view_name="admin:settings"),
                ],
            ),
            MenuCollapse(
                name="reports",
                extra_context={"label": "Reports", "icon": "chart-bar"},
                children=[
                    MenuItem(name="sales", view_name="reports:sales"),
                ],
            ),
        ]
    )

Import that module from your app config's ``ready()`` so the items are
registered before the first request.

An item marks itself active when the current URL or view name matches it, and
a parent expands when one of its children is active.
"""

from flex_menu import Menu, MenuItem


class MenuGroup(MenuItem):
    """A labelled section header with items beneath it.

    Renders as non-clickable text followed by its children, which is how a
    long sidebar gets divided into named sections.

    Example::

        MenuGroup(
            name="user_management",
            extra_context={"label": "User management"},
            children=[
                MenuItem(name="users", view_name="users:list"),
                MenuItem(name="roles", view_name="roles:list"),
            ],
        )
    """


class MenuCollapse(MenuItem):
    """A parent item that expands and collapses to reveal its children.

    Renders through the ``<details>``/``<summary>`` pair, so it needs no
    JavaScript. Setting ``collapsible`` is the whole difference from a plain
    parent item, and this class exists so a project never has to know that
    key's name.

    Example::

        MenuCollapse(
            name="reports",
            extra_context={"label": "Reports", "icon": "chart-bar"},
            children=[
                MenuItem(name="sales", view_name="reports:sales"),
                MenuItem(name="inventory", view_name="reports:inventory"),
            ],
        )
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # A fresh dict rather than a write into the one that arrived: callers
        # reuse context literals across items, and the flag belongs to this
        # item alone.
        self.extra_context = {**self.extra_context, "collapsible": True}


#: The sidebar navigation tree. Empty until a project extends it.
AppMenu = Menu("AppMenu", children=[])

#: The mobile dock, shown below the small-screen breakpoint.
#:
#: Ships with the sidebar toggle alone, because that is the only item whose
#: destination the package can know. Append your own::
#:
#:     from flex_menu import MenuItem
#:
#:     from mvp.menus import MobileFooterMenu
#:
#:     MobileFooterMenu.append(
#:         MenuItem(
#:             name="home",
#:             view_name="home",
#:             extra_context={"label": "Home", "icon": "home"},
#:         )
#:     )
MobileFooterMenu = Menu(
    "MobileFooterMenu",
    children=[
        MenuItem(
            name="sidebar_toggle",
            extra_context={
                "label": "Menu",
                "icon": "menu",
                # Renders as a <label for="mvp-app-toggle"> that flips the
                # drawer checkbox — the same mechanism as the navbar
                # hamburger. The value is the drawer toggle's element id
                # (c-layout.sidebar id="mvp-app" -> checkbox id "mvp-app-toggle").
                "toggle": "mvp-app-toggle",
            },
        ),
    ],
)
