"""A pager can carry its page number in a query parameter other than ``page``.

A page that shows several paged tables at once gives each table its own parameter,
such as django-tables2's ``table.prefixed_page_field``, so that moving through one table
leaves the others where they are.
"""

from urllib.parse import parse_qs, urlsplit

import pytest
from django.core.paginator import Paginator
from django.test import RequestFactory


@pytest.fixture
def context():
    return {
        "page_obj": Paginator(list(range(30)), 10).page(2),
        "request": RequestFactory().get("/items/?o=name&other-page=3"),
    }


def queries(soup):
    hrefs = [a["href"] for a in soup.find_all("a")]
    hrefs += [option["value"] for option in soup.find_all("option")]
    return [parse_qs(urlsplit(href).query) for href in hrefs]


class TestPaginationParam:
    @pytest.mark.parametrize(
        "source",
        [
            '<c-mvp.pagination.link :page="2" text="2" param="mine-page" />',
            '<c-mvp.pagination :page_obj="page_obj" param="mine-page" />',
            '<c-mvp.pagination.compact :page_obj="page_obj" param="mine-page" />',
            '<c-mvp.page.list.footer :page_obj="page_obj" param="mine-page" />',
        ],
    )
    def test_every_link_sets_the_named_parameter_and_keeps_the_rest(
        self, cotton_render_string_soup, context, source
    ):
        found = queries(cotton_render_string_soup(source, context=context))

        assert found
        for query in found:
            assert set(query) == {"o", "other-page", "mine-page"}
            assert query["other-page"] == ["3"]
            assert query["o"] == ["name"]

    def test_without_a_param_the_page_number_goes_in_page(
        self, cotton_render_string_soup, context
    ):
        found = queries(
            cotton_render_string_soup(
                '<c-mvp.pagination :page_obj="page_obj" />', context=context
            )
        )

        assert found
        assert all("page" in query and "mine-page" not in query for query in found)
