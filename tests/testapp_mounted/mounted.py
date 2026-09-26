"""The mounted fixture app's declaration.

A host mounts it with ``mount("mounted/", testapp_mounted)``. Declared once,
here, the way a package ships its own ``mounted.py``: a class holding the
declaration and an instance for the host to mount.
"""

from mvp.mounted import MountedApp

from .menus import TestappMountedMenu


class MountedFixtureApp(MountedApp):
    """The fixture app, as a package declares it."""

    name = "Mounted Fixture"
    icon = "book"
    menu = TestappMountedMenu
    urls = "tests.testapp_mounted.urls"
    landing = "testapp_mounted:index"


class StaffFixtureApp(MountedFixtureApp):
    """The same pages behind a staff-only check, for a URLconf that mounts it."""

    name = "Staff Fixture"

    def check(request):  # noqa: N805 - a plain function, called with the request alone
        return request.user.is_staff


testapp_mounted = MountedFixtureApp()
testapp_mounted_staff = StaffFixtureApp()
