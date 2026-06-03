"""Custom menu renderers for django-mvp navigation."""

from __future__ import annotations

from typing import Any

from flex_menu.menu import MenuItem
from flex_menu.renderers import BaseRenderer


class MobileFooterNavRenderer(BaseRenderer):
    """Renderer for the mobile footer navigation bar.

    Produces flat BS5 .nav-item > .nav-link HTML for each registered MenuItem.
    Sidebar toggle items are rendered as <button data-lte-toggle="sidebar">
    rather than anchor links.

    Config:
        FLEX_MENUS["renderers"]["dock"] = "mvp.renderers.MobileFooterNavRenderer"
    """

    templates = {
        0: {"default": "menus/dock/index.html"},
        "default": {
            "parent": "menus/dock/item.html",
            "leaf": "menus/dock/item.html",
        },
    }


class AdminLTERenderer(BaseRenderer):
    """Renderer for AdminLTE 4 sidebar navigation.

    This renderer transforms django-flex-menus MenuItem objects into context data
    for AdminLTE-compatible templates. It provides:

    - MenuItem and MenuCollapse items maintain declaration order
    - MenuGroup items (section headers) sorted to bottom
    - Depth-based template selection for hierarchical menus
    - Active state detection based on current URL matching
    - Icon and badge rendering via extra_context
    - Bootstrap 5 compatible CSS classes and structure

    Templates are selected based on item depth and whether the item has children:
    - Depth 0: Container template (menus/container.html)
    - Depth 1+: Parent/leaf templates based on children presence

    Active state detection compares:
    1. Current request URL with menu item URL
    2. Current view name with menu item view_name
    3. Hierarchical active states for parent menu expansion
    """

    templates: dict[Any, Any] = {
        # Depth 0: Container (root menu)
        0: {"default": "menus/container.html"},
        # Depth 1+: Nested items (fallback)
        "default": {
            "parent": "menus/parent.html",
            "leaf": "menus/item.html",
        },
    }

    def get_context_data(self, item: MenuItem, **kwargs: Any) -> dict[str, Any]:
        """Build template context for rendering a menu item.

        BaseRenderer already provides: label, url, selected, depth, visible, children
        BaseRenderer merges item.extra_context into context (icon, badge, classes, etc.)

        We only add:
        - component_type for template selection
        - Child sorting (MenuGroup to bottom)
        """
        context = super().get_context_data(item, **kwargs)

        # Sort children: MenuGroup to bottom, others in declaration order
        # Only sort at depth 0 (root menu container)
        children = context.get("children")
        if item.depth == 0 and children:
            menu_groups = []
            other_items = []

            for child in children:
                component_type = child.extra_context.get("component_type")
                if component_type == "menu.group":
                    menu_groups.append(child)
                else:
                    other_items.append(child)

            context["children"] = other_items + menu_groups

        return context


class SidebarRenderer(BaseRenderer):
    """Renderer for sidebar navigation.

    Generates semantic menu markup for use inside the sidebar drawer.
    Supports leaf items, section headers (MenuGroup) and collapsible groups
    (MenuCollapse) via the ``<details>/<summary>`` pattern.

    Templates:
    - Depth 0: ``menus/sidebar/container.html``
    - Leaf items: ``menus/sidebar/item.html``
    - Parent items: ``menus/sidebar/parent.html``

    Config:
        FLEX_MENUS["renderers"]["sidebar"] = "mvp.renderers.SidebarRenderer"
    """

    templates: dict[Any, Any] = {
        0: {"default": "menus/sidebar/container.html"},
        "default": {
            "parent": "menus/sidebar/parent.html",
            "leaf": "menus/sidebar/item.html",
        },
    }

    def get_context_data(self, item: MenuItem, **kwargs: Any) -> dict[str, Any]:
        """Build template context.

        Inherits all BaseRenderer context (label, url, selected, depth, visible,
        children, extra_context fields). Additionally sorts MenuGroup children to
        the bottom at depth 0 to match AdminLTERenderer behaviour.
        """
        context = super().get_context_data(item, **kwargs)

        children = context.get("children")
        if item.depth == 0 and children:
            groups, others = [], []
            for child in children:
                if child.extra_context.get("component_type") == "menu.group":
                    groups.append(child)
                else:
                    others.append(child)
            context["children"] = others + groups

        return context


class NavRenderer(BaseRenderer):
    """Renderer for navigation menus.

    Maps menu item types to their corresponding navigation templates.
    Supports regular links, dropdowns with headers and items.
    """

    templates = {
        0: {"default": "menus/nav/wrapper.html"},
        1: {
            "parent": "menus/nav/wrapper.html",
            "leaf": "menus/nav/link.html",
        },
    }


# class NavbarRenderer(BaseRenderer):
#     """Renderer for desktop navbar navigation.

#     Maps menu item types to their corresponding navbar templates.
#     Supports regular links, dropdowns with headers and items.
#     """

#     templates = {
#         0: {"default": "menus/navbar/menu.html"},
#         1: {
#             "parent": "menus/navbar/nav_dropdown.html",
#             "leaf": "menus/navbar/nav_link.html",
#         },
#         "default": {
#             "parent": "menus/navbar/nav_dropdown.html",
#             "leaf": "menus/navbar/dropdown_item.html",
#         },
#     }


# class SidebarRenderer(BaseRenderer):
#     """Renderer for sidebar/detail page menus.

#     Used for plugin menus in detail views with categorized sections.
#     """

#     templates = {
#         0: {"default": "menus/sidebar/menu.html"},
#         1: {
#             "parent": "menus/sidebar/section.html",
#             "leaf": "menus/sidebar/item.html",
#         },
#         "default": {
#             "parent": "menus/sidebar/section.html",
#             "leaf": "menus/sidebar/item.html",
#         },
#     }


# class DropdownRenderer(BaseRenderer):
#     """Renderer for dropdown menus.

#     Used for dropdown-style navigation elements.
#     """

#     templates = {
#         0: {"default": "menus/dropdown/menu.html"},
#         1: {
#             "parent": "menus/dropdown/dropdown.html",
#             "leaf": "menus/dropdown/item.html",
#         },
#         "default": {
#             "parent": "menus/dropdown/dropdown.html",
#             "leaf": "menus/dropdown/item.html",
#         },
#     }
