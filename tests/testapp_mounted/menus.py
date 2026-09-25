"""The mounted fixture app's own menu: one entry per page."""

from flex_menu import Menu, MenuItem

TestappMountedMenu = Menu(
    "TestappMountedMenu",
    children=[
        MenuItem(
            name="testapp_mounted_index",
            view_name="testapp_mounted:index",
            extra_context={"label": "Mounted Index", "icon": "house"},
        ),
        MenuItem(
            name="testapp_mounted_detail",
            view_name="testapp_mounted:detail",
            extra_context={"label": "Mounted Detail", "icon": "file-text"},
        ),
    ],
)
