"""AppConfig for a card-contributing fixture app that also has a menu entry
(US-3, T024).

Its sibling, ``tests.testapp_card_no_menu``, has no menu entry at all — the
pair proves FR-020's contrast: having a menu entry does not change how an
app's card is contributed. Activated per test with
``override_settings(INSTALLED_APPS=...)``, never globally (ARC-001).

Contributes by shipping its own ``mvp/account/overview.html``
(``templates/mvp/account/overview.html``), extending the package's template
of the same name and adding to ``{% block account.cards %}`` through
``{{ block.super }}`` (Refined 2026-09-14). No application-configuration
attribute is declared for it.
"""

from django.apps import AppConfig


class TestAppCardWithMenuConfig(AppConfig):
    """A minimal installed app contributing both a card and a menu entry."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "tests.testapp_card_with_menu"
    label = "testapp_card_with_menu"
    verbose_name = "Test App Card Fixture (with menu)"
