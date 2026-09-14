"""AppConfig for a card-only fixture app with no menu entry (US-3, T024).

Proves FR-020: an app that contributes a card without adding an entry to
``AccountCenterMenu`` is still collected by ``AccountCenterView``. Activated
per test with ``override_settings(INSTALLED_APPS=...)`` alongside its
sibling, ``tests.testapp_card_with_menu`` — never installed globally, so
``TestAccountCenterView.test_signed_in_request_shows_no_cards`` (US-1) stays
green (ARC-001).
"""

from django.apps import AppConfig


class TestAppCardNoMenuConfig(AppConfig):
    """A minimal installed app contributing a card and nothing else."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "tests.testapp_card_no_menu"
    label = "testapp_card_no_menu"
    verbose_name = "Test App Card Fixture (no menu)"

    account_center_card_template = "testapp_card_no_menu/card.html"

    def account_center_card_context(self, request):
        return {"testapp_card_no_menu_label": "No Menu Card"}
