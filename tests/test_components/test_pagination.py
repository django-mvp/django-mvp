"""``<c-mvp.pagination>``'s ``label`` names the navigation landmark it draws.

The ``<nav>`` element comes from ``<c-mvp.pagination.wrapper>``, which reads
``label`` into ``aria-label`` and defaults it to "Navigation page results".
``<c-mvp.pagination>`` declared a ``label`` of its own and never forwarded it,
and declaring a name is what removes it from the attribute pass-through — so
a caller naming the landmark got the default anyway, with nothing to show the
value had been discarded.

A page with more than one paginated region is the case that needs this: two
identical landmark names give a screen-reader user no way to tell them apart.
"""

import pytest
from django.core.paginator import Paginator


@pytest.fixture
def page_obj():
    return Paginator(list(range(30)), 10).page(2)


class TestPaginationLabel:
    def test_the_landmark_has_a_default_name(self, cotton_render_string_soup, page_obj):
        soup = cotton_render_string_soup(
            '<c-mvp.pagination :page_obj="page_obj" />', context={"page_obj": page_obj}
        )

        assert soup.find("nav")["aria-label"].strip()

    def test_a_caller_names_the_landmark(self, cotton_render_string_soup, page_obj):
        soup = cotton_render_string_soup(
            '<c-mvp.pagination label="Search results pages" :page_obj="page_obj" />',
            context={"page_obj": page_obj},
        )

        assert soup.find("nav")["aria-label"] == "Search results pages"

    def test_the_landmark_is_named_once(self, cotton_render_string_soup, page_obj):
        html = cotton_render_string_soup(
            '<c-mvp.pagination label="Search results pages" :page_obj="page_obj" />',
            context={"page_obj": page_obj},
        ).decode()

        opening_tag = html[html.index("<nav") : html.index(">", html.index("<nav")) + 1]
        assert opening_tag.count("aria-label") == 1


def _pager_texts(cotton_render_string_soup, number, pages):
    page_obj = Paginator(list(range(pages)), 1).page(number)
    soup = cotton_render_string_soup(
        '<c-mvp.pagination :page_obj="page_obj" page_window="1" show_first_and_last />',
        context={"page_obj": page_obj},
    )
    return [
        el.get_text(strip=True) for el in soup.find("nav").find_all(["a", "button"])
    ]


class TestPaginationGaps:
    def test_a_gap_of_several_pages_is_an_ellipsis(self, cotton_render_string_soup):
        texts = _pager_texts(cotton_render_string_soup, number=6, pages=11)

        numbers = [text for text in texts if text.isdigit()]
        assert numbers == ["1", "5", "6", "7", "11"]

    def test_a_gap_of_one_page_shows_that_page(self, cotton_render_string_soup):
        texts = _pager_texts(cotton_render_string_soup, number=4, pages=7)

        numbers = [text for text in texts if text.isdigit()]
        assert numbers == ["1", "2", "3", "4", "5", "6", "7"]

    def test_first_and_last_pages_are_always_reachable(self, cotton_render_string_soup):
        texts = _pager_texts(cotton_render_string_soup, number=1, pages=9)

        numbers = [text for text in texts if text.isdigit()]
        assert numbers == ["1", "2", "9"]


class TestCompactPagination:
    def _render(self, cotton_render_string_soup, number, pages=4, query=""):
        from django.test import RequestFactory

        page_obj = Paginator(list(range(pages)), 1).page(number)
        return cotton_render_string_soup(
            '<c-mvp.pagination.compact :page_obj="page_obj" />',
            context={
                "page_obj": page_obj,
                "request": RequestFactory().get(f"/products/{query}"),
            },
        )

    def test_every_page_is_an_option_holding_its_own_address(
        self, cotton_render_string_soup
    ):
        soup = self._render(cotton_render_string_soup, number=2, query="?q=lamp")

        options = soup.find("select").find_all("option")
        assert [option.get_text(strip=True) for option in options] == [
            "1",
            "2",
            "3",
            "4",
        ]
        assert options[2]["value"] == "?q=lamp&page=3"

    def test_the_current_page_is_the_selected_option(self, cotton_render_string_soup):
        soup = self._render(cotton_render_string_soup, number=3)

        selected = [
            o for o in soup.find("select").find_all("option") if o.has_attr("selected")
        ]
        assert [option.get_text(strip=True) for option in selected] == ["3"]

    def test_one_page_draws_nothing(self, cotton_render_string_soup):
        soup = self._render(cotton_render_string_soup, number=1, pages=1)

        assert soup.find("nav") is None


class TestListFooterSpacing:
    def test_the_footer_spacing_does_not_reach_the_pager_buttons(
        self, cotton_render_string_soup
    ):
        from django.test import RequestFactory

        soup = cotton_render_string_soup(
            '<c-mvp.page.list.footer :page_obj="page_obj" class="px-4" />',
            context={
                "page_obj": Paginator(list(range(30)), 10).page(2),
                "request": RequestFactory().get("/products/"),
            },
        )

        assert "px-4" in soup.find(class_="mvp-list-footer")["class"]
        for control in soup.find_all(["a", "button", "nav", "select"]):
            assert "px-4" not in control.get("class", [])
