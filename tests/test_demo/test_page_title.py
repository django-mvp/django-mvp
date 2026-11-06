"""Tests for the demo's Page Title page, ``/layout/title/``.

The page draws the title in the layout named by ``?title_layout=``, so the demo can
show each one; the same query string works on the demo's other pages.

Source: demo/views.py, demo/urls.py
"""

import pytest
from bs4 import BeautifulSoup

from mvp.utils import TITLE_LAYOUTS

URL = "/layout/title/"


def title_markup(client, query=""):
    """The page's response and the markup of the title it drew."""
    response = client.get(f"{URL}{query}")
    soup = BeautifulSoup(response.content, "html.parser")
    return response, str(soup.select_one("main h1").find_parent(class_="page-title"))


@pytest.mark.django_db
class TestPageTitleDemoPage:
    @pytest.mark.parametrize("layout", TITLE_LAYOUTS)
    def test_the_layout_in_the_query_string_draws_the_title(self, client, layout):
        response, _title = title_markup(client, f"?title_layout={layout}")

        assert response.status_code == 200
        assert response.context["page"]["title_layout"] == layout

    def test_each_layout_draws_the_title_differently(self, client):
        drawn = {
            layout: title_markup(client, f"?title_layout={layout}")[1]
            for layout in TITLE_LAYOUTS
        }

        assert len(set(drawn.values())) == len(TITLE_LAYOUTS)

    def test_an_unknown_layout_is_ignored(self, client):
        response, title = title_markup(client, "?title_layout=no_such_layout")
        plain_response, plain_title = title_markup(client)

        assert response.status_code == 200
        assert (
            response.context["page"]["title_layout"]
            == (plain_response.context["page"]["title_layout"])
        )
        assert title == plain_title

    def test_the_form_lists_every_layout_and_marks_the_current_one(self, client):
        response = client.get(f"{URL}?title_layout=centred")

        options = BeautifulSoup(response.content, "html.parser").select(
            "select[name=title_layout] option"
        )
        assert [option["value"] for option in options] == list(TITLE_LAYOUTS)
        assert [o["value"] for o in options if o.has_attr("selected")] == ["centred"]
