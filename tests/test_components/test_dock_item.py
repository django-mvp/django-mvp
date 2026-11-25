"""Tests for ``c-mvp.dock.item``: which item holds the current page, and its icon.

A dock declared in a template marks an item current for a whole section of the
site (URL namespaces and view names) and draws a second icon while it is current.

Source: mvp/templates/cotton/mvp/dock/item.html
"""

from django.http import HttpResponse
from django.test import RequestFactory
from django.urls import include, path, resolve

from tests.conftest import urlconf_of


def view(request, **kwargs):
    return HttpResponse("")


SHOP = urlconf_of(
    path("", view, name="home"),
    path("projects/", view, name="project-list"),
    path(
        "projects/",
        include(
            (
                [
                    path("<int:pk>/", view, name="detail"),
                    path("<int:pk>/files/", view, name="files"),
                ],
                "project",
            )
        ),
    ),
)


def render_dock(cotton_render_string_soup, url, item):
    request = RequestFactory().get(url)
    request.resolver_match = resolve(url, urlconf=SHOP)
    soup = cotton_render_string_soup(
        f"<c-dock>{item}</c-dock>", context={"request": request}
    )
    return soup.select_one(".dock > *")


def is_current(element):
    return "dock-active" in element.get("class", [])


class TestACurrentSection:
    def test_an_item_is_current_on_a_view_it_names(self, cotton_render_string_soup):
        item = render_dock(
            cotton_render_string_soup,
            "/projects/",
            '<c-mvp.dock.item href="/projects/" section="project-list" />',
        )

        assert is_current(item)
        assert item["aria-current"] == "page"

    def test_an_item_is_current_on_every_view_of_a_namespace_it_names(
        self, cotton_render_string_soup
    ):
        item = '<c-mvp.dock.item href="/projects/" section="project-list project" />'

        for url in ("/projects/", "/projects/3/", "/projects/3/files/"):
            assert is_current(render_dock(cotton_render_string_soup, url, item))

    def test_an_item_is_not_current_on_another_section(self, cotton_render_string_soup):
        item = render_dock(
            cotton_render_string_soup,
            "/",
            '<c-mvp.dock.item href="/projects/" section="project-list project" />',
        )

        assert not is_current(item)
        assert "aria-current" not in item.attrs

    def test_a_name_that_is_not_a_whole_view_name_does_not_match(
        self, cotton_render_string_soup
    ):
        item = render_dock(
            cotton_render_string_soup,
            "/projects/",
            '<c-mvp.dock.item href="/projects/" section="project" />',
        )

        assert not is_current(item)

    def test_a_list_of_names_is_read_as_well_as_a_string(
        self, cotton_render_string_soup
    ):
        request = RequestFactory().get("/projects/3/")
        request.resolver_match = resolve("/projects/3/", urlconf=SHOP)
        soup = cotton_render_string_soup(
            '<c-dock><c-mvp.dock.item href="/p/" :section="names" /></c-dock>',
            context={"request": request, "names": ["project"]},
        )

        assert is_current(soup.select_one(".dock > *"))

    def test_active_still_marks_an_item_a_section_cannot_express(
        self, cotton_render_string_soup
    ):
        item = render_dock(
            cotton_render_string_soup,
            "/",
            '<c-mvp.dock.item href="/projects/" :active="True" />',
        )

        assert is_current(item)

    def test_a_toggle_item_is_current_for_a_section_and_announces_nothing(
        self, cotton_render_string_soup
    ):
        item = render_dock(
            cotton_render_string_soup,
            "/projects/",
            '<c-mvp.dock.item toggle="mvp-app-toggle" section="project-list" />',
        )

        assert is_current(item)
        assert "aria-current" not in item.attrs

    def test_a_page_with_no_request_matches_no_section(self, cotton_render_string):
        html = cotton_render_string(
            '<c-dock><c-mvp.dock.item href="/p/" section="project" /></c-dock>',
            context={"request": RequestFactory().get("/")},
        )

        assert "dock-active" not in html


class TestTheCurrentIcon:
    ITEM = (
        '<c-mvp.dock.item href="/projects/" section="project-list" '
        'icon="home" current-icon="search" />'
    )

    def icon_of(self, element):
        return element.select_one("svg, i")

    def test_the_current_icon_is_drawn_while_the_item_is_current(
        self, cotton_render_string_soup
    ):
        current = render_dock(cotton_render_string_soup, "/projects/", self.ITEM)
        other = render_dock(cotton_render_string_soup, "/", self.ITEM)

        assert str(self.icon_of(current)) != str(self.icon_of(other))

    def test_an_item_with_no_current_icon_keeps_its_icon_while_current(
        self, cotton_render_string_soup
    ):
        plain = (
            '<c-mvp.dock.item href="/projects/" section="project-list" icon="home" />'
        )

        current = render_dock(cotton_render_string_soup, "/projects/", plain)
        other = render_dock(cotton_render_string_soup, "/", plain)

        assert str(self.icon_of(current)) == str(self.icon_of(other))


class TestEverythingElsePassesThrough:
    def test_class_and_other_attributes_reach_the_element(
        self, cotton_render_string_soup
    ):
        item = render_dock(
            cotton_render_string_soup,
            "/",
            '<c-mvp.dock.item href="/" class="extra" data-hook="x" />',
        )

        assert "extra" in item["class"]
        assert item["data-hook"] == "x"
