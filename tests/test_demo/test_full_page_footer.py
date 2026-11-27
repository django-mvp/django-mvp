"""A full-page demo page drops the footer, and an ordinary page keeps it."""

import pytest

FILL_PAGE = "/layout/full-page/"
ORDINARY_PAGE = "/layout/store/"


@pytest.mark.django_db
class TestTheFooter:
    def test_a_full_page_has_no_footer(self, client):
        response = client.get(FILL_PAGE)

        assert response.status_code == 200
        assert "<footer" not in response.content.decode()

    def test_an_ordinary_page_has_one(self, client):
        response = client.get(ORDINARY_PAGE)

        assert response.status_code == 200
        assert response.content.decode().count("<footer") == 1
