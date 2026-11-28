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
    def test_the_two_htmx_actions_leave_and_call_the_demo_views(self, soup):
        answer = soup.select_one("[hx-post='/components/list-row/answer/']")
        failure = soup.select_one("[hx-post='/components/list-row/fail/']")

        assert answer.has_attr("data-mvp-row-leaves")
        assert failure.has_attr("data-mvp-row-leaves")

    def test_a_form_action_names_a_form_on_the_page(self, soup):
        action = soup.select_one("[data-mvp-row-action][form]")

        assert soup.select_one(f"form#{action['form']}")


class TestListRowDemoViews:
    def test_the_answering_view_answers_with_nothing_to_draw(self, client):
        response = client.post("/components/list-row/answer/")

        assert response.status_code == 200
        assert response.content == b""

    def test_the_failing_view_answers_with_a_server_error(self, client):
        response = client.post("/components/list-row/fail/")

        assert response.status_code >= 500
