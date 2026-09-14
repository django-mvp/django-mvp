"""AppConfig for the demo's own Account Center card (US-3, T025, G9).

A separate small app from ``demo``'s own ``DemoConfig`` so ``tests/settings.py``
can exclude it from the test suite's ``INSTALLED_APPS`` without touching the
``demo`` app the rest of the suite depends on for its models and views (D16).
``demo`` itself never declares ``account_center_card_template`` — a human
browsing the demo project sees a populated card region only because this app
is installed alongside it (``demo/settings.py``); the test suite's card
counts (``tests/test_views/test_account.py``) stay deterministic because it
never is (``tests/settings.py``).
"""

from django.apps import AppConfig


class DemoAccountShowcaseConfig(AppConfig):
    """Contributes one card to the Account Center's landing page."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "demo.account_showcase"
    label = "demo_account_showcase"
    verbose_name = "Demo Account Center Showcase"

    account_center_card_template = "account_showcase/card.html"
