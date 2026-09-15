"""
Test-specific Django settings.

The full application configuration (INSTALLED_APPS, MIDDLEWARE, TEMPLATES,
EASY_ICONS, FLEX_MENUS, …) lives in ``demo/settings.py`` and is inherited here.
This module only *pins* the handful of ``MVP_CONFIG`` values the test suite
asserts on, so experimenting with the demo (``demo/settings.py``) can never
break the tests.
"""

from demo.settings import *

# The demo's own Account Center card (US-3, T025, demo/account_showcase/): shown
# only when browsing the demo project directly, so a human sees a populated card
# region (G9). Filtered back out of the inherited INSTALLED_APPS here — not
# appended, removed — so the test suite's card counts stay deterministic and
# TestAccountCenterView.test_signed_in_request_shows_no_cards (US-1) stays green
# regardless of what the demo showcases (D16).
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "demo.account_showcase"]

# The Account Center fixture app (US-2, tests/testapp_account/): proves a page
# outside mvp can add a menu entry and a page. Appended here rather than in
# demo/settings.py because it exists only to be exercised by the test suite.
INSTALLED_APPS = [*INSTALLED_APPS, "tests.testapp_account"]

# django-mvp layout config the test suite asserts on. Defined here — NOT read
# from demo/settings.py — so visual tweaks to the demo don't ripple into tests.
# See tests/test_components/test_layout_config.py.
MVP_CONFIG = {
    "layout": {
        "navbar": {
            "end": [
                "actions.theme-controller",
                "actions.language-switcher",
            ],
        },
    },
}
