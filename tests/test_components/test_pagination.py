"""``<c-pagination>``'s ``label`` names the navigation landmark it draws.

The ``<nav>`` element comes from ``<c-pagination.wrapper>``, which reads
``label`` into ``aria-label`` and defaults it to "Navigation page results".
``<c-pagination>`` declared a ``label`` of its own and never forwarded it,
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
    """Page two of three, so every branch of the component draws."""
    return Paginator(list(range(30)), 10).page(2)


class TestPaginationLabel:
    def test_the_landmark_has_a_default_name(
        self, cotton_render_string_soup, page_obj
    ):
        soup = cotton_render_string_soup(
            '<c-pagination :page_obj="page_obj" />', context={"page_obj": page_obj}
        )

        assert soup.find("nav")["aria-label"] == "Navigation page results"

    def test_a_caller_names_the_landmark(self, cotton_render_string_soup, page_obj):
        soup = cotton_render_string_soup(
            '<c-pagination label="Search results pages" :page_obj="page_obj" />',
            context={"page_obj": page_obj},
        )

        assert soup.find("nav")["aria-label"] == "Search results pages"

    def test_the_landmark_is_named_once(self, cotton_render_string_soup, page_obj):
        """A second ``aria-label`` would be dropped by the browser in silence."""
        html = cotton_render_string_soup(
            '<c-pagination label="Search results pages" :page_obj="page_obj" />',
            context={"page_obj": page_obj},
        ).decode()

        opening_tag = html[html.index("<nav") : html.index(">", html.index("<nav")) + 1]
        assert opening_tag.count("aria-label") == 1
