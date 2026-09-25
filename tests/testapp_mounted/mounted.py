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

testapp_mounted_staff = MountedApp(
    name="Staff Fixture",
    icon="book",
    menu=TestappMountedMenu,
    urls="tests.testapp_mounted.urls",
    landing="testapp_mounted:index",
    check=lambda request: request.user.is_staff,
)
"""The same pages behind a staff-only check, for a URLconf that mounts it."""
