"""The sidebar menu for a Sphinx documentation app, read from its build."""

import json
from pathlib import Path

from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from flex_menu import Menu, MenuItem

from mvp.menus import MenuCollapse, MenuGroup

from .navigation import FILENAME


class DocumentationMenu(Menu):
    """A menu whose entries are the pages of a Sphinx build.

    The build's ``navigation.json`` is read again whenever the file changes,
    so rebuilding the docs updates the sidebar without a restart. Each toctree
    caption on the root page becomes a section, and a page that lists pages of
    its own becomes a group that opens on any of them.

    Args:
        name: The menu's name.
        app: The :class:`~mvp.integrations.sphinx_view.mounted.DocumentationApp`
            the menu belongs to.
    """

    def __init__(self, name, app):
        super().__init__(name, children=[])
        self.app = app
        self.stamp = None

    def process(self, request, **kwargs):
        """Refresh the entries from the build, then process them as usual."""
        self.refresh()
        return super().process(request, **kwargs)

    def refresh(self):
        """Rebuild the entries when the navigation file or the docs' address changes."""
        source = Path(self.app.json_build_dir) / FILENAME
        try:
            modified = source.stat().st_mtime
        except FileNotFoundError:
            modified = None
        root = reverse(f"{self.app.namespace}:index")
        if (modified, root) == self.stamp:
            return
        navigation = (
            json.loads(source.read_text(encoding="utf-8")) if modified else {}
        )
        self.children = self.build(navigation, root)
        self.stamp = (modified, root)

    def build(self, navigation, root):
        """Return the menu entries for ``navigation``, with URLs under ``root``."""
        items = [self.link("docs-overview", _("Overview"), root)]
        for number, section in enumerate(navigation.get("sections", [])):
            entries = [
                self.entry(entry, root, f"docs-{number}-{index}")
                for index, entry in enumerate(section["entries"])
            ]
            if section["caption"]:
                items.append(
                    MenuGroup(
                        name=f"docs-section-{number}",
                        extra_context={"label": section["caption"]},
                        children=entries,
                    )
                )
            else:
                items.extend(entries)
        return items

    def entry(self, entry, root, name):
        """Return the item for one page, or a group when it lists pages of its own."""
        url = root + entry["url"]
        if not entry["children"]:
            return self.link(name, entry["title"], url)
        # flex_menu keeps links and groups apart, so the page itself opens its
        # own group, the way the demo's Components group opens on "Overview".
        return MenuCollapse(
            name=name,
            extra_context={"label": entry["title"]},
            children=[
                self.link(f"{name}-overview", _("Overview"), url),
                *(
                    self.entry(child, root, f"{name}-{index}")
                    for index, child in enumerate(entry["children"])
                ),
            ],
        )

    @staticmethod
    def link(name, label, url):
        """Return a plain link entry."""
        return MenuItem(name=name, url=url, extra_context={"label": label})
