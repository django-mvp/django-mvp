"""The list row demo page and the two views its htmx actions call.

Source: demo/views.py, demo/urls.py, demo/templates/demo/components/list-row.html
"""

import pytest
from bs4 import BeautifulSoup
from django.urls import reverse

pytestmark = pytest.mark.django_db


@pytest.fixture
def soup(client):
    """Return the parsed list row page."""
    response = client.get(reverse("component-doc", kwargs={"slug": "list-row"}))
    assert response.status_code == 200
    return BeautifulSoup(response.content, "html.parser")


class TestListRowDemoPage:
    def test_the_page_is_listed_with_the_components(self, client):
        response = client.get("/components/")

        assert response.status_code == 200
        assert b'href="/components/list-row/"' in response.content

    def test_the_actionable_list_has_rows_with_and_without_actions(self, soup):
        rows = soup.select("section#actions [data-mvp-row]")
        plain = soup.select("section#actions ul.list > li:not([data-mvp-row])")

        assert len(rows) >= 4
        assert len(plain) >= 1

    def test_every_action_is_drawn_once(self, soup):
        ids = [tag["id"] for tag in soup.select("[data-mvp-row-action][id]")]

        assert len(ids) >= 4
        assert len(ids) == len(set(ids))

    def test_a_row_has_at_most_one_main_action(self, soup):
        for row in soup.select("[data-mvp-row]"):
            assert len(row.select("[data-mvp-row-main]")) <= 1

    def test_the_page_has_a_row_with_a_main_action(self, soup):
        assert soup.select("[data-mvp-row] [data-mvp-row-main]")

    def test_the_two_htmx_actions_leave_and_call_the_demo_views(self, soup):
        answer = soup.select_one("[hx-post='/components/list-row/answer/']")
        failure = soup.select_one("[hx-post='/components/list-row/fail/']")

        assert answer.has_attr("data-mvp-row-leaves")
        assert failure.has_attr("data-mvp-row-leaves")

    def test_a_form_action_names_a_form_on_the_page(self, soup):
        action = soup.select_one("[data-mvp-row-action][form]")

        assert soup.select_one(f"form#{action['form']}")

    def test_a_second_list_can_be_switched_off_and_on(self, soup):
        assert soup.select("section#switching-swiping-off [data-mvp-row]")
        assert soup.select_one(
            "section#switching-swiping-off [data-mvp-rows-switch='off']"
        )
        assert soup.select_one(
            "section#switching-swiping-off [data-mvp-rows-switch='on']"
        )


class TestListRowDemoViews:
    def test_the_answering_view_answers_with_nothing_to_draw(self, client):
        response = client.post("/components/list-row/answer/")

        assert response.status_code == 200
        assert response.content == b""

    def test_the_failing_view_answers_with_a_server_error(self, client):
        response = client.post("/components/list-row/fail/")

        assert response.status_code >= 500

    @pytest.mark.parametrize("url", ["answer", "fail"])
    def test_neither_view_answers_a_get(self, client, url):
        response = client.get(f"/components/list-row/{url}/")

        assert response.status_code == 405
