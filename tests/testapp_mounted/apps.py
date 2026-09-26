"""App config for the mounted-app fixture (FS-032)."""

from django.apps import AppConfig


class TestAppMountedConfig(AppConfig):
    """A minimal installed app a host project can mount.

    Declares no menu entries into ``AppMenu`` and imports nothing at ready
    time: the tests prove a mounted app never writes into the host's menus.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "tests.testapp_mounted"
    label = "testapp_mounted"
    verbose_name = "Test App Mounted Fixture"
