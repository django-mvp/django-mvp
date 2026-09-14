"""The menus a project builds its navigation from.

Navigation is a tree of ``MenuItem`` objects held in three singletons this module
exports. A project imports them, appends its own items, and a renderer turns
the tree into markup. The renderers live in :mod:`mvp.renderers` and are
registered under ``FLEX_MENUS["renderers"]``.

- ``AppMenu`` — the sidebar tree. Ships empty.
- ``MobileFooterMenu`` — the mobile dock. Ships with the sidebar toggle only.
- ``AccountCenterMenu`` — the Account Center's own navigation, rendered beside
  its pages by ``<c-account.nav>``. Ships with the entry for its own landing
  page. An app that wants a page in the area appends to it the same way it
  extends ``AppMenu``::

      from flex_menu import MenuItem

      from mvp.menus import AccountCenterMenu

      AccountCenterMenu.append(
          MenuItem(
              name="notifications",
              view_name="yourapp:notifications",
              extra_context={"label": "Notifications", "icon": "bell"},
          )
      )

Each item carries its display data in ``extra_context``: ``label`` and ``icon``
are read by every renderer, ``badge`` by the sidebar templates, and ``toggle``
by the dock. An item resolves its URL from ``view_name`` or ``url``, and an
item whose URL will not resolve is dropped from the rendered menu, so a project
adding an item is responsible for the URL name existing.

An ``AccountCenterMenu`` entry is also where section membership is declared,
for :func:`get_active_section` and the trail ``AccountPageMixin``
(:mod:`mvp.views.account`) builds from it. An entry that is itself a section
root names the URL-name prefixes of the pages below it in
``extra_context["url_names"]``, a tuple::

    AccountCenterMenu.append(
        MenuItem(
            name="notifications",
            view_name="yourapp:notifications",
            extra_context={
                "label": "Notifications",
                "icon": "bell",
                "url_names": ("yourapp:notifications",),
            },
        )
    )

A request whose URL name starts with one of those prefixes resolves to that
entry's section even when the request isn't the entry's own page — this is
how ``yourapp:notifications-detail`` still names "Notifications" in the trail.
An entry with no ``url_names`` is only ever its own section, never a page
below it.

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

from django.utils.translation import gettext_lazy as _
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

#: The Account Center's own navigation, rendered beside its pages by
#: ``<c-account.nav>``. Ships with only the entry for its own landing page
#: (FR-007) — everything else belongs to whichever app adds to it.
AccountCenterMenu = Menu(
    "AccountCenterMenu",
    children=[
        MenuItem(
            name="overview",
            view_name="account-center",
            extra_context={"label": _("Overview"), "icon": "overview"},
        ),
    ],
)


def _iter_leaves(item):
    """Yield ``item``'s leaf descendants, descending through processed groups.

    Only called on an already-:meth:`~flex_menu.menu.MenuItem.process`-ed
    tree, so ``visible_children`` — not the static ``children`` — is what
    each level descends through: a group with no visible children yields
    nothing, and one whose children were filtered by a check yields only
    the survivors.
    """
    children = item.visible_children
    if children:
        for child in children:
            yield from _iter_leaves(child)
    else:
        yield item


def get_active_section(request):
    """Return the ``AccountCenterMenu`` section ``request`` belongs to.

    Processes the menu for ``request`` and looks at its leaf entries —
    descending through any grouped entry, since a group is not itself a
    section. Returns ``{"label": …, "url": …, "is_current": bool}``:
    ``is_current`` is ``True`` when the request is the section's own page
    (render its crumb as plain text) and ``False`` when the request is a page
    below it, resolved through the entry's declared ``url_names`` prefixes
    (render the crumb as a link). Returns ``None`` on the area's own landing
    page or a page no entry names — the caller renders the area alone.

    The entry named ``"overview"`` — the area's own landing page — is
    excluded from consideration: it names the area, not a section within it.
    """
    processed = AccountCenterMenu.process(request)
    leaves = [
        item
        for item in _iter_leaves(processed)
        if item.visible and item.name != "overview"
    ]

    for item in leaves:
        if item.selected:
            return {
                "label": item.extra_context.get("label", item.name),
                "url": item.url,
                "is_current": True,
            }

    url_name = getattr(request.resolver_match, "url_name", None)
    if url_name:
        for item in leaves:
            for prefix in item.extra_context.get("url_names", ()):
                if url_name.startswith(prefix):
                    return {
                        "label": item.extra_context.get("label", item.name),
                        "url": item.url,
                        "is_current": False,
                    }
    return None
