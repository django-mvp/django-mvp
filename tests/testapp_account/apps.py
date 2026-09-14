"""App config for the Account Center's outside-the-package fixture (US-2)."""

from django.apps import AppConfig


class TestAppAccountConfig(AppConfig):
    """A minimal installed app proving US-2 from outside ``mvp``.

    Deliberately does not import ``menus`` here. ``AccountCenterMenu`` is a
    module-level singleton (``mvp/menus.py``) shared by the whole test
    session, and an entry appended from ``ready()`` — the way ``demo/menus.py``
    appends to ``AppMenu`` — would survive every test after the one that added
    it, turning ``tests/test_menus.py::TestAccountCenterMenu``'s exact-count
    assertion red (ARC-001). ``tests/conftest.py``'s ``testapp_account_entries``
    fixture calls ``menus.build_entries()`` and applies/detaches them per test
    instead.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "tests.testapp_account"
    label = "testapp_account"
    verbose_name = "Test App Account Fixture"
