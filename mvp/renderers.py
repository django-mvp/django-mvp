"""Custom menu renderers for django-mvp navigation."""

from __future__ import annotations

from typing import Any

from flex_menu.renderers import BaseRenderer


class MobileFooterNavRenderer(BaseRenderer):
    """Renderer for the mobile footer navigation bar (daisyUI dock).

    Renders each registered MenuItem as a dock item (see c-dock.item):
    - items with a ``toggle`` in extra_context become a <label for="..."> that
      flips a drawer checkbox (e.g. "mvp-app-toggle" opens the sidebar);
    - items with a URL become an <a href> navigation link;
    - items with neither render as an inert <button> placeholder.

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
