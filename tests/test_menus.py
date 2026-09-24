"""Tests for ``mvp.menus`` — the menu classes and shipped menu singletons.

Mirrors ``mvp/menus.py`` (Article X). ``MenuCollapse`` is the only class here
with behaviour of its own: it marks itself collapsible in ``extra_context``.
That is a small surface, and all three of the ways it can go wrong are silent
— a dropped label, a caller's dict changed underneath them, a missing flag —
so each gets an assertion.
"""

import pytest
from django.test import RequestFactory, override_settings
from django.urls import include, path

from flex_menu import Menu, MenuItem

from mvp.menus import (
    AccountCenterMenu,
    AppMenu,
    MenuCollapse,
    MenuGroup,
    MobileFooterMenu,
)
from mvp.renderers import SidebarRenderer
from tests.testapp_account.menus import CHECKED_FLAG


def _urlconf():
    """``mvp.urls`` (so the landing-page entry still resolves) plus the
    fixture app's own URLs, mounted independently of ``demo/urls.py``."""
    patterns = [
        path("", include("mvp.urls")),
        path("testapp-account/", include("tests.testapp_account.urls")),
    ]
    return type("_URLConf", (), {"urlpatterns": patterns})


ACCOUNT_URLCONF = _urlconf()


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


def _sidebar_html(*items):
    """Process ``items`` in a throwaway menu and draw it through the sidebar
    renderer, the way ``{% render_menu %}`` does for ``AppMenu``."""
    menu = Menu("EmptyContainerMenu", children=list(items))
    request = RequestFactory().get("/")
    return SidebarRenderer().render(menu.process(request))


class TestAContainerWithNoChildrenIsHidden:
    """[#380] A ``MenuGroup`` or ``MenuCollapse`` declared with no children
    used to fall through to the leaf template and draw as an inert
    ``<button href="None">``. A section that has no pages yet is left out of
    the sidebar until its first page is added."""

    @pytest.mark.parametrize("container", [MenuGroup, MenuCollapse])
    def test_an_empty_container_is_not_drawn(self, container):
        html = _sidebar_html(
            container(name="empty", extra_context={"label": "EmptySection"})
        )

        assert "EmptySection" not in html
        assert 'href="None"' not in html

    @pytest.mark.parametrize("container", [MenuGroup, MenuCollapse])
    def test_a_container_whose_children_are_all_hidden_is_not_drawn(
        self, container
    ):
        html = _sidebar_html(
            container(
                name="hidden",
                extra_context={"label": "HiddenSection"},
                children=[MenuItem(name="page", url="/page/", check=False)],
            )
        )

        assert "HiddenSection" not in html

    @pytest.mark.parametrize("container", [MenuGroup, MenuCollapse])
    def test_a_container_with_a_child_is_drawn(self, container):
        html = _sidebar_html(
            container(
                name="filled",
                extra_context={"label": "FilledSection"},
                children=[
                    MenuItem(
                        name="page", url="/page/", extra_context={"label": "Page"}
                    )
                ],
            )
        )

        assert "FilledSection" in html
        assert 'href="/page/"' in html

    def test_an_empty_container_does_not_disturb_its_siblings(self):
        html = _sidebar_html(
            MenuGroup(name="empty", extra_context={"label": "EmptySection"}),
            MenuItem(name="home", url="/", extra_context={"label": "Home"}),
        )

        assert "EmptySection" not in html
        assert "Home" in html


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


class TestShippedMenusCarryAHumanName:
    """[#343] Every menu the sidebar renderer draws reads its accessible name
    from ``extra_context["label"]`` now, so the two menus this package ships
    need a real, translated one — otherwise the default is the internal menu
    name (``AppMenu``, ``AccountCenterMenu``), not something a screen reader
    should announce."""

    def test_app_menu_has_a_translated_label(self):
        assert str(AppMenu.extra_context["label"]) == "Main navigation"

    def test_account_center_menu_has_a_translated_label(self):
        assert str(AccountCenterMenu.extra_context["label"]) == "Account navigation"


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


class TestAccountMenuContribution:
    """An installed app's contribution to ``AccountCenterMenu`` (US-2, FR-008,
    FR-009, FR-010) — proved through the fixture app in
    ``tests/testapp_account/``, applied and detached per test (ARC-001)."""

    @pytest.fixture(autouse=True)
    def _account_urlconf(self):
        """Scoped to this class alone, so the entry-count assertions above —
        which run under the suite's default URLconf — are undisturbed."""
        with override_settings(ROOT_URLCONF=ACCOUNT_URLCONF):
            yield

    def _visible_names(self, request):
        processed = AccountCenterMenu.process(request)
        return [child.name for child in processed.visible_children]

    def test_the_entries_appear_alongside_the_landing_page_entry(
        self, testapp_account_entries
    ):
        """No check flag set, so the checked entry stays hidden and the
        unresolvable one stays dropped — three visible top-level entries,
        counted exactly."""
        names = self._visible_names(RequestFactory().get("/"))
        assert names == ["overview", "fixture_plain", "fixture_group"]

    def test_a_grouped_entry_renders_under_its_label(self, testapp_account_entries):
        processed = AccountCenterMenu.process(RequestFactory().get("/"))
        group = next(
            child
            for child in processed.visible_children
            if child.name == "fixture_group"
        )
        assert group.extra_context["label"] == "Fixture Group"
        assert [child.name for child in group.visible_children] == [
            "fixture_grouped_item"
        ]

    def test_an_entry_whose_check_answers_no_is_absent(self, testapp_account_entries):
        names = self._visible_names(RequestFactory().get("/"))
        assert "fixture_checked" not in names

    def test_the_same_entry_is_present_for_a_request_the_check_answers_yes_for(
        self, testapp_account_entries
    ):
        names = self._visible_names(RequestFactory().get("/", {CHECKED_FLAG: "1"}))
        assert "fixture_checked" in names

    def test_an_unresolvable_entry_is_omitted_without_disturbing_the_rest(
        self, testapp_account_entries
    ):
        names = self._visible_names(RequestFactory().get("/"))
        assert "fixture_unresolvable" not in names
        assert names == ["overview", "fixture_plain", "fixture_group"]

    def test_an_app_can_reorder_the_entries(self, testapp_account_entries):
        """FR-008's other half: reordering is django-flex-menus' own
        ``children`` assignment, not anything this package adds."""
        reordered = [
            testapp_account_entries["fixture_plain"],
            *[
                child
                for child in AccountCenterMenu.children
                if child.name != "fixture_plain"
            ],
        ]
        AccountCenterMenu.children = reordered
        assert AccountCenterMenu.children[0].name == "fixture_plain"

    def test_an_app_can_remove_an_entry_it_does_not_want(self, testapp_account_entries):
        AccountCenterMenu.pop("fixture_unresolvable")
        assert AccountCenterMenu.get("fixture_unresolvable") is None
        names = self._visible_names(RequestFactory().get("/"))
        assert "fixture_unresolvable" not in names
