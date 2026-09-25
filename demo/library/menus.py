"""The library app's own menu, drawn in the sidebar on its pages."""

from django.utils.translation import gettext_lazy as _
from flex_menu import Menu, MenuItem

LibraryMenu = Menu(
    "LibraryMenu",
    children=[
        MenuItem(
            name="library-catalogue",
            view_name="library:catalogue",
            extra_context={"label": _("Catalogue"), "icon": "book"},
        ),
        MenuItem(
            name="library-reading-list",
            view_name="library:reading-list",
            extra_context={"label": _("Reading list"), "icon": "list"},
        ),
    ],
)
