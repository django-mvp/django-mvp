"""Tests for ``mvp.menus`` — the menu classes and shipped menu singletons.

Mirrors ``mvp/menus.py`` (the testing standard). ``MenuCollapse`` is the only class here
with behaviour of its own: it marks itself collapsible in ``extra_context``.
That is a small surface, and all three of the ways it can go wrong are silent
— a dropped label, a caller's dict changed underneath them, a missing flag —
so each gets an assertion.
"""

import pytest
from bs4 import BeautifulSoup
from django.test import RequestFactory, override_settings
from django.urls import include, path
from flex_menu import Menu, MenuItem

from mvp.menus import (
    AccountCenterMenu,
    MenuCollapse,
    MenuGroup,
    MobileFooterMenu,
)
from mvp.renderers import SidebarRenderer
from mvp.warnings import MVPDeprecationWarning


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
        item = MenuCollapse(
            "reports", "", "", None, None, None, True, {"label": "Reports"}
        )
        assert item.extra_context["label"] == "Reports"
        assert item.extra_context["collapsible"] is True

    def test_leaves_the_callers_dict_alone(self):
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
    @pytest.mark.parametrize("container", [MenuGroup, MenuCollapse])
    def test_an_empty_container_is_not_drawn(self, container):
        html = _sidebar_html(
            container(name="empty", extra_context={"label": "EmptySection"})
        )

        assert "EmptySection" not in html
        assert 'href="None"' not in html

    def test_an_empty_container_does_not_disturb_its_siblings(self):
        html = _sidebar_html(
            MenuGroup(name="empty", extra_context={"label": "EmptySection"}),
            MenuItem(name="home", url="/", extra_context={"label": "Home"}),
        )

        assert "EmptySection" not in html
        assert "Home" in html


class TestTheMobileFooterMenuIsDeprecated:
    def test_processing_it_warns_and_names_the_template_way(self):
        request = RequestFactory().get("/")

        with pytest.warns(MVPDeprecationWarning, match="c-mvp.dock.item"):
            MobileFooterMenu.process(request)


class TestAccountMenuContribution:
    @pytest.fixture(autouse=True)
    def _account_urlconf(self):
        with override_settings(ROOT_URLCONF=ACCOUNT_URLCONF):
            yield

    def _visible_names(self, request):
        processed = AccountCenterMenu.process(request)
        return [child.name for child in processed.visible_children]

    def test_the_entries_appear_alongside_the_landing_page_entry(
        self, testapp_account_entries
    ):
        names = self._visible_names(RequestFactory().get("/"))
        assert names == ["overview", "preferences", "fixture_plain", "fixture_group"]

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


def _divider_before_heading(html, heading):
    """Whether an empty ``<li>``, which DaisyUI draws as a divider, comes
    straight before the group heading reading ``heading``."""
    soup = BeautifulSoup(html, "html.parser")
    title = soup.find("li", class_="menu-title", string=lambda s: s and heading in s)
    before = title.find_previous_sibling("li")
    return before is not None and not before.get_text(strip=True) and not before.find()


class TestAGroupsDividerAboveItsHeading:
    @staticmethod
    def _group(**context):
        return MenuGroup(
            name="admin",
            extra_context={"label": "AdminSection", **context},
            children=[
                MenuItem(name="users", url="/users/", extra_context={"label": "Users"})
            ],
        )

    def test_a_group_draws_a_divider_above_its_heading_by_default(self):
        html = _sidebar_html(self._group())

        assert _divider_before_heading(html, "AdminSection")

    def test_a_group_asking_for_no_divider_draws_its_heading_alone(self):
        html = _sidebar_html(self._group(divider=False))

        assert not _divider_before_heading(html, "AdminSection")
        assert "AdminSection" in html
        assert 'href="/users/"' in html
