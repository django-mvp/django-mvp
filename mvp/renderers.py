"""Custom menu renderers for django-mvp navigation."""

from __future__ import annotations

from typing import Any

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
