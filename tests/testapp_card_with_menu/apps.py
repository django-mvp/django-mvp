"""AppConfig for a card-contributing fixture app that also has a menu entry
(US-3, T024).

Its sibling, ``tests.testapp_card_no_menu``, has no menu entry at all — the
pair proves FR-020's contrast: having a menu entry does not change how an
app's card is collected. Activated per test with
``override_settings(INSTALLED_APPS=...)``, never globally (ARC-001).
"""

from django.apps import AppConfig


class TestAppCardWithMenuConfig(AppConfig):
    """A minimal installed app contributing both a card and a menu entry."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "tests.testapp_card_with_menu"
    label = "testapp_card_with_menu"
    verbose_name = "Test App Card Fixture (with menu)"

    account_center_card_template = "testapp_card_with_menu/card.html"

    def account_center_card_context(self, request):
        return {"testapp_card_with_menu_label": "With Menu Card"}
