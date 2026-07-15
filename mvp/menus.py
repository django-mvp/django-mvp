"""Menu definitions for django-mvp application.

This module provides the core menu infrastructure for django-mvp's navigation system.
It exports the main AppMenu instance and helper classes that developers use to
define their application's site navigation menu structure.

The menu system is built on django-flex-menus and provides:
- Hierarchical menu structure with unlimited nesting
- Active state detection and menu expansion
- Icon and badge support via Bootstrap Icons
- AdminLTE 4 compatible rendering
- Multi-app menu composition

Example usage in your app's menus.py:

    from mvp.menus import AppMenu, MenuGroup, MenuCollapse
    from flex_menu import MenuItem

    # Add single menu items
    AppMenu.children.extend([
        MenuItem(
            name="dashboard",
            view_name="yourapp:dashboard",
            extra_context={"label": "Dashboard", "icon": "speedometer"}
        ),
    ])

    # Add menu sections with headers
    MenuGroup(
        name="section_header",
        extra_context={"label": "ADMINISTRATION", "component_type": "menu.group"},
        ,
        children=[
            MenuItem(name="users", view_name="admin:users"),
            MenuItem(name="settings", view_name="admin:settings"),
        ]
    )

    # Add collapsible menu groups
    MenuCollapse(
        name="reports",
        extra_context={"label": "Reports", "icon": "chart-bar", "component_type": "menu.collapse"},
        ,
        children=[
            MenuItem(name="sales", view_name="reports:sales"),
        ]
    )

Architecture:
    - AppMenu: Root menu container (singleton instance)
    - MenuGroup: Section headers that create visual groupings
    - MenuCollapse: Expandable/collapsible menu sections
    - MenuItem: Individual menu items (imported from django-flex-menus)

Active State:
    Menu items automatically detect and display active state based on:
    - Current URL matching menu item URL
    - Current view name matching menu item view_name
    - Parent menus expand when children are active

Rendering:
    Menus are rendered using the custom AdminLTERenderer which provides:
    - Bootstrap 5 compatible HTML structure
    - AdminLTE 4 CSS classes and layout
    - Cotton component integration
    - Badge and icon rendering support
"""

from flex_menu import Menu, MenuItem


class MenuGroup(MenuItem):
    """MenuItem subclass for section headers with items below.

    Renders as a non-clickable section header (nav-header) followed by its children.
    Used for grouping related menu items under a labeled section.

    Example:
        MenuGroup(
            name="user_management",
            extra_context={"label": "USER MANAGEMENT"},
            children=[
                MenuItem(name="users", view_name="users:list"),
                MenuItem(name="roles", view_name="roles:list"),
            ]
        )
    """


class MenuCollapse(MenuItem):
    """MenuItem subclass for expandable dropdown menus.

    Renders as a clickable parent item that expands/collapses to show/hide children.
    Includes chevron icon and AdminLTE treeview behavior.

    Example:
        MenuCollapse(
            name="reports",
            extra_context={"label": "Reports", "icon": "chart-bar"},
            children=[
                MenuItem(name="sales", view_name="reports:sales"),
                MenuItem(name="inventory", view_name="reports:inventory"),
            ]
        )
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inject component_type into extra_context
        if "extra_context" not in kwargs:
            self.extra_context = {}
        self.extra_context["collapsible"] = True


# Global menu instance for application navigation
# Initially empty - users extend by importing and adding MenuItem instances
AppMenu = Menu("AppMenu", children=[])

# Mobile footer navigation menu — pre-populated with sidebar toggle item.
# Developers may append additional MenuItem instances to this singleton.
# Example:
#     from mvp.menus import MobileFooterMenu
#     MobileFooterMenu.children.append(MenuItem(name="home", ...))
MobileFooterMenu = Menu(
    "MobileFooterMenu",
    extra_context={
        "text": "Mobile Navigation",
        "type": "underline",
        "fill": True,
        "gap": 0,
    },
    children=[
        MenuItem(
            name="sidebar_toggle",
            extra_context={
                "label": "Menu",
                "icon": "menu",
                # Renders as a <label for="mvp-app-toggle"> that flips the
                # daisyUI drawer checkbox — same mechanism as the navbar
                # hamburger. The value is the drawer toggle's element id
                # (c-layout.sidebar id="mvp-app" -> checkbox id "mvp-app-toggle").
                "toggle": "mvp-app-toggle",
            },
        ),
        MenuItem(
            name="home",
            view_name="home",
            extra_context={
                "label": "Home",
                "icon": "home",
            },
        ),
        # Uncomment to test more mobile nav-items
        # MenuItem(
        #     name="sidebar_toggle",
        #     extra_context={
        #         "label": "Menu",
        #         "icon": "menu",
        #         "show_text": True,
        #         "attrs": {
        #             "data-lte-toggle": "sidebar",
        #         },
        #         "sidebar_toggle": True,
        #     },
        # ),
        # MenuItem(
        #     name="sidebar_toggle",
        #     extra_context={
        #         "label": "Menu",
        #         "icon": "menu",
        #         "attrs": {
        #             "data-lte-toggle": "sidebar",
        #         },
        #         "sidebar_toggle": True,
        #     },
        # ),
    ],
)
