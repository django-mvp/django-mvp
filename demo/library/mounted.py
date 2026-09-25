"""The library app's declaration.

The demo mounts it in ``demo/urls.py`` with ``mount("library/", library)`` and
adds its entries to ``AppMenu`` and the dock in ``demo/menus.py``.
"""

from django.utils.translation import gettext_lazy as _

from mvp.mounted import MountedApp

from .menus import LibraryMenu

library = MountedApp(
    name=_("Library"),
    icon="book",
    menu=LibraryMenu,
    urls="demo.library.urls",
    landing="library:catalogue",
)
