"""Fixture menu entries proving US-2's contribution surface from outside ``mvp``.

Built fresh by :func:`build_entries` on every call rather than declared as
module-level singletons: a ``MenuItem`` belongs to one parent at a time, and
``AccountCenterMenu`` (``mvp/menus.py``) is itself a singleton every test in
the session shares. A real installed app appends once, from its own
``AppConfig.ready()``, the same way ``demo/menus.py`` extends ``AppMenu`` —
this fixture app's entries are applied per test and detached afterwards
instead (``tests/conftest.py``'s ``testapp_account_entries`` fixture), because
a globally-appended entry would outlive the test that added it and turn
``tests/test_menus.py::TestAccountCenterMenu``'s exact-count assertion red
(ARC-001).

Four entries, one per capability US-2 claims for a contributing app (FR-008,
FR-009, FR-010):

- ``fixture_plain`` — an ordinary entry pointing at a page of its own.
- ``fixture_group`` — a labelled ``MenuGroup`` (imported from ``mvp.menus``,
  the package's own public menu-authoring surface — not from
  django-accounts-center) wrapping one entry, ``fixture_grouped_item``.
- ``fixture_checked`` — carries a per-request check reading
  ``request.GET[CHECKED_FLAG]``, so a test can turn its visibility on and off
  without touching auth.
- ``fixture_unresolvable`` — points at a view name nothing registers, proving
  FR-010's drop-without-disturbing-the-rest behaviour.
"""

from flex_menu import MenuItem

from mvp.menus import MenuGroup

#: GET parameter ``fixture_checked``'s check reads to decide visibility.
CHECKED_FLAG = "show_fixture_checked"


def build_entries():
    """Return a fresh list of top-level entries for ``AccountCenterMenu``.

    Called by the ``testapp_account_entries`` fixture in ``tests/conftest.py``
    — never at import time and never from an ``AppConfig.ready()``.
    """
    return [
        MenuItem(
            name="fixture_plain",
            view_name="testapp_account:plain",
            extra_context={"label": "Fixture Plain"},
        ),
        MenuGroup(
            name="fixture_group",
            extra_context={"label": "Fixture Group"},
            children=[
                MenuItem(
                    name="fixture_grouped_item",
                    view_name="testapp_account:grouped",
                    extra_context={"label": "Fixture Grouped Item"},
                ),
            ],
        ),
        MenuItem(
            name="fixture_checked",
            view_name="testapp_account:plain",
            check=lambda request, **kwargs: request.GET.get(CHECKED_FLAG) == "1",
            extra_context={"label": "Fixture Checked"},
        ),
        MenuItem(
            name="fixture_unresolvable",
            view_name="testapp_account:does-not-exist",
            extra_context={"label": "Fixture Unresolvable"},
        ),
    ]
