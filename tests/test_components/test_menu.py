"""Tests for the sidebar's menu entries and the container around them.

The menu, its entries and its groups are daisy-cotton's. What the package still
promises is what it does with them: the entry for the current page is marked,
a group holding it opens, an entry's label sits where the icon rail's
stylesheet can hide it, and the navigation landmark the sidebar draws around
the menu is named by the label the menu declares.

Sources: mvp/templates/menus/sidebar/
"""

from bs4 import BeautifulSoup
from django.template.loader import render_to_string
from django.test import RequestFactory
from flex_menu import Menu, MenuItem

from mvp.menus import MenuCollapse, MenuGroup
from mvp.renderers import SidebarRenderer


def sidebar(*items, path="/"):
    """Draw ``items`` through the sidebar renderer on a request for ``path``."""
    menu = Menu("SidebarEntriesTestMenu", children=list(items))
    request = RequestFactory().get(path)
    return BeautifulSoup(SidebarRenderer().render(menu.process(request)), "html.parser")


def page(name, url, **context):
    """A menu entry pointing at ``url``."""
    return MenuItem(name=name, url=url, extra_context={"label": name, **context})


class TestSidebarEntry:
    def test_an_entry_links_to_its_url(self):
        soup = sidebar(page("reports", "/reports/"))

        assert soup.select_one("a")["href"] == "/reports/"

    def test_an_entry_without_a_url_draws_a_button_with_no_href(self):
        soup = sidebar(MenuItem(name="act", extra_context={"label": "Act"}))

        button = soup.select_one("li > button")
        assert button is not None
        assert not button.has_attr("href")

    def test_the_entry_for_the_current_page_is_marked_current(self):
        soup = sidebar(
            page("home", "/"), page("reports", "/reports/"), path="/reports/"
        )

        current = soup.select("[aria-current='page']")
        assert [link["href"] for link in current] == ["/reports/"]

    def test_the_label_sits_in_a_span_the_icon_rail_can_hide(self):
        soup = sidebar(page("reports", "/reports/"))

        assert soup.select_one("a > span").get_text(strip=True) == "reports"

    def test_the_entry_names_itself_for_the_rail_tooltip(self):
        soup = sidebar(page("reports", "/reports/"))

        assert soup.select_one("a")["data-tip"] == "reports"

    def test_a_badge_is_drawn_inside_the_entry(self):
        soup = sidebar(page("inbox", "/inbox/", badge="3"))

        assert soup.select_one("a > .badge").get_text(strip=True) == "3"


class TestSidebarCollapsibleGroup:
    def group(self, path):
        return sidebar(
            MenuCollapse(
                name="tools",
                extra_context={"label": "Tools"},
                children=[page("sales", "/sales/"), page("stock", "/stock/")],
            ),
            path=path,
        )

    def test_a_group_holding_the_current_page_opens(self):
        soup = self.group("/stock/")

        assert soup.select_one("li > details[open]") is not None

    def test_a_group_not_holding_the_current_page_stays_closed(self):
        soup = self.group("/elsewhere/")

        details = soup.select_one("li > details")
        assert details is not None
        assert not details.has_attr("open")

    def test_the_label_sits_in_a_span_the_icon_rail_can_hide(self):
        soup = self.group("/elsewhere/")

        assert (
            soup.select_one("details > summary > span").get_text(strip=True) == "Tools"
        )

    def test_the_children_are_entries_of_the_group(self):
        soup = self.group("/elsewhere/")

        links = soup.select("details > ul a")
        assert [link["href"] for link in links] == ["/sales/", "/stock/"]


class TestSidebarStaticGroup:
    def test_the_children_follow_a_heading_and_a_separator(self):
        soup = sidebar(
            MenuGroup(
                name="tools",
                extra_context={"label": "Tools"},
                children=[page("sales", "/sales/")],
            )
        )

        assert soup.select_one("li.menu-title").get_text(strip=True) == "Tools"
        assert soup.select_one("details") is None
        assert [a["href"] for a in soup.select("ul > li > a")] == ["/sales/"]


class TestSidebarContainerTakesItsNameFromContext:
    def test_the_label_comes_from_context_not_a_fixed_string(self):
        html = render_to_string(
            "menus/sidebar/container.html",
            {"children": [], "renderer": None, "label": "Reports"},
        )
        soup = BeautifulSoup(html, "html.parser")

        assert soup.find("nav")["aria-label"] == "Reports"

    def test_the_menu_sits_inside_the_named_navigation_landmark(self):
        html = render_to_string(
            "menus/sidebar/container.html",
            {"children": [], "renderer": None, "label": "Reports"},
        )
        soup = BeautifulSoup(html, "html.parser")

        assert soup.select_one("nav[aria-label='Reports'] > ul.menu") is not None


class TestDockItemForwardsAttrs:
    def test_button_variant_forwards_attrs(self):
        html = render_to_string(
            "menus/dock/item.html",
            {
                "label": "Log episode",
                "icon": "plus",
                "url": None,
                "selected": False,
                "toggle": None,
                "attrs": {"x-on:click": "modalOpen = true"},
            },
        )
        assert 'x-on:click="modalOpen = true"' in html
