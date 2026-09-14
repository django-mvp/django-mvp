"""Tests for ``mvp.menus`` — the menu classes and shipped menu singletons.

Mirrors ``mvp/menus.py`` (Article X). ``MenuCollapse`` is the only class here
with behaviour of its own: it marks itself collapsible in ``extra_context``.
That is a small surface, and all three of the ways it can go wrong are silent
— a dropped label, a caller's dict changed underneath them, a missing flag —
so each gets an assertion.
"""

from mvp.menus import AccountCenterMenu, MenuCollapse, MobileFooterMenu


class TestMenuCollapse:
    """``MenuCollapse`` marks itself collapsible without disturbing its input."""

    def test_marks_itself_collapsible(self):
        item = MenuCollapse(name="reports", extra_context={"label": "Reports"})
        assert item.extra_context["collapsible"] is True

    def test_keeps_context_passed_as_a_keyword(self):
        item = MenuCollapse(
            name="reports", extra_context={"label": "Reports", "icon": "chart"}
        )
        assert item.extra_context["label"] == "Reports"
        assert item.extra_context["icon"] == "chart"

    def test_keeps_context_passed_positionally(self):
        """``extra_context`` is the eighth positional parameter of ``MenuItem``.

        Passing it there used to leave the item with an empty context, so the
        label and icon vanished with no error.
        """
        item = MenuCollapse(
            "reports", "", "", None, None, None, True, {"label": "Reports"}
        )
        assert item.extra_context["label"] == "Reports"
        assert item.extra_context["collapsible"] is True

    def test_leaves_the_callers_dict_alone(self):
        """The caller keeps its own dict, so one shared literal can seed
        several items."""
        context = {"label": "Reports"}
        MenuCollapse(name="reports", extra_context=context)
        assert context == {"label": "Reports"}

    def test_works_without_any_context(self):
        item = MenuCollapse(name="reports")
        assert item.extra_context == {"collapsible": True}


class TestShippedMenus:
    """What the package puts in the two menu singletons before a project
    touches them."""

    def test_the_packaged_dock_item_needs_no_url_from_the_project(self):
        """The toggle is the one item the package can pre-populate.

        Anything else would point at a URL name the project may not define,
        and a menu item whose URL will not resolve is dropped from the render
        without a message. Asserted on the first child rather than on the
        whole list because this suite runs with ``demo`` installed, and
        ``demo/menus.py`` appends its own item behind it.
        """
        packaged = MobileFooterMenu.children[0]
        assert packaged.name == "sidebar_toggle"
        assert not packaged.view_name
        assert not packaged.url

    def test_the_sidebar_toggle_flips_the_drawer_checkbox(self):
        toggle = MobileFooterMenu.children[0]
        assert toggle.extra_context["toggle"] == "mvp-app-toggle"


class TestAccountCenterMenu:
    """``AccountCenterMenu`` ships carrying only its own landing-page entry
    (FR-007) — everything else belongs to whichever app adds to it (US-2)."""

    def test_ships_exactly_one_child(self):
        """Asserted as an exact count, not "at least one": a second packaged
        entry would be a page the area itself decided to add, which is the
        job left to an installed app."""
        assert len(AccountCenterMenu.children) == 1

    def test_the_one_child_is_named_overview(self):
        assert AccountCenterMenu.children[0].name == "overview"

    def test_the_overview_child_points_at_the_landing_page(self):
        assert AccountCenterMenu.children[0].view_name == "account-center"
