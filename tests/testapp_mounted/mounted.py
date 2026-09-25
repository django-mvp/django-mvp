"""The mounted fixture app's declaration.

A host mounts it with ``mount("mounted/", testapp_mounted)``. Declared once,
here, the way a package ships its own ``mounted.py``.
"""

from mvp.mounted import MountedApp

from .menus import TestappMountedMenu

testapp_mounted = MountedApp(
    name="Mounted Fixture",
    icon="book",
    menu=TestappMountedMenu,
    urls="tests.testapp_mounted.urls",
    landing="testapp_mounted:index",
)
