"""Custom menu renderers for django-mvp navigation."""

from __future__ import annotations

from typing import Any

from flex_menu.renderers import BaseRenderer

from mvp.config import MVP_CONFIG


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

    def get_context_data(self, item, **kwargs):
        """Add ``mvp_config`` so the dock template can pass ``layout.dock.class``.

        Menus render with ``render_to_string`` and no request, so the context
        processor that puts ``mvp_config`` in every page's context never runs.
        """
        return {**super().get_context_data(item, **kwargs), "mvp_config": MVP_CONFIG}


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


class LocalNavigationRenderer(BaseRenderer):
    """Renderer for a record's local navigation: one row of links under the header.

    A record with several pages of its own (an overview, its parts, its
    settings) lists them as a row of underlined tabs, the current page marked.
    The row never wraps: on a narrow screen it scrolls sideways, with no
    scrollbar drawn. Put it in ``{% block app.header.tray %}``, or give a view
    ``local_menu`` in its context and the shell puts it there.

    Templates:
    - Depth 0: ``menus/local/container.html``
    - Items: ``menus/local/item.html``

    Config:
        FLEX_MENUS["renderers"]["local"] = "mvp.renderers.LocalNavigationRenderer"
    """

    templates: dict[Any, Any] = {
        0: {"default": "menus/local/container.html"},
        "default": {
            "parent": "menus/local/item.html",
            "leaf": "menus/local/item.html",
        },
    }
