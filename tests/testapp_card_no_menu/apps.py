"""AppConfig for a card-only fixture app with no menu entry (US-3, T024).

Proves FR-020: an app that contributes a card without adding an entry to
``AccountCenterMenu`` still gets its card. Activated per test with
``override_settings(INSTALLED_APPS=...)`` alongside its sibling,
``tests.testapp_card_with_menu`` — never installed globally, so
``TestAccountCenterView.test_signed_in_request_shows_no_cards`` (US-1) stays
green (ARC-001).

Contributes by shipping its own ``mvp/account/overview.html``
(``templates/mvp/account/overview.html``), extending the package's template
of the same name and adding to ``{% block account.cards %}`` through
``{{ block.super }}`` (Refined 2026-09-14). No application-configuration
attribute is declared for it.
"""

from django.apps import AppConfig


class TestAppCardNoMenuConfig(AppConfig):
    """A minimal installed app contributing a card and nothing else."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "tests.testapp_card_no_menu"
    label = "testapp_card_no_menu"
    verbose_name = "Test App Card Fixture (no menu)"
