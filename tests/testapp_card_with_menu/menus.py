"""Fixture menu entry for ``tests.testapp_card_with_menu`` (US-3, T024).

Built fresh by :func:`build_entries` rather than appended at import time —
the same reasoning as ``tests/testapp_account/menus.py`` (ARC-001):
``AccountCenterMenu`` is a session-wide singleton, and an entry attached from
``ready()`` would outlive the test that installed this app. Points at
``testapp_account:plain`` — an existing fixture page (US-2) — so this app
needs no view or URL of its own just to prove it has a resolvable entry.
"""

from flex_menu import MenuItem


def build_entries():
    """Return a fresh list of entries, applied and detached per test the same
    way ``tests/conftest.py``'s ``testapp_account_entries`` fixture handles
    ``tests/testapp_account``'s entries."""
    return [
        MenuItem(
            name="testapp_card_with_menu_entry",
            view_name="testapp_account:plain",
            extra_context={"label": "Card With Menu Fixture"},
        ),
    ]
