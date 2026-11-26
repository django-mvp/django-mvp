"""The reorder demo page and the views that save its lists.

Source: demo/views.py, demo/urls.py
"""

import pytest
from bs4 import BeautifulSoup

from demo.models import Project

pytestmark = pytest.mark.django_db


def task_ids(name):
    return list(
        Project.objects.get(name=f"Reorder demo: {name}").tasks.values_list(
            "pk", flat=True
        )
    )


class TestReorderDemoPage:
    def test_each_of_the_four_lists_has_several_rows(self, client):
        response = client.get("/components/reorder/")

        soup = BeautifulSoup(response.content, "html.parser")
        assert response.status_code == 200
        for section in ("row-set", "in-a-form", "posts-as-it-changes", "on-demand"):
            rows = soup.select(f"section#{section} [data-mvp-reorder-row]")
            assert len(rows) > 2

    def test_the_list_without_buttons_has_rows_and_marks_the_buttons_off(self, client):
        response = client.get("/components/reorder/")

        soup = BeautifulSoup(response.content, "html.parser")
        root = soup.select_one("section#without-buttons [data-mvp-reorder]")
        assert root.has_attr("data-mvp-reorder-hide-buttons")
        assert len(root.select("[data-mvp-reorder-row]")) > 2

    def test_the_form_list_saves_the_order_it_posts(self, client):
        client.get("/components/reorder/")
        ids = task_ids("form")

        response = client.post("/components/reorder/", {"order": ids[::-1]})

        assert response.status_code == 302
        assert task_ids("form") == ids[::-1]

    def test_the_form_list_refuses_an_order_that_leaves_a_task_out(self, client):
        client.get("/components/reorder/")
        ids = task_ids("form")

        response = client.post("/components/reorder/", {"order": ids[1:]})

        assert response.status_code == 400
        assert task_ids("form") == ids


class TestReorderDemoSave:
    def test_a_posted_order_is_saved_and_the_list_drawn_again(self, client):
        client.get("/components/reorder/")
        ids = task_ids("mode")

        response = client.post("/components/reorder/mode/", {"order": ids[::-1]})

        assert response.status_code == 200
        assert task_ids("mode") == ids[::-1]
        assert b'id="mode-tasks"' in response.content

    def test_the_pinned_list_refuses_an_order_that_moves_its_first_task(self, client):
        client.get("/components/reorder/")
        ids = task_ids("live")

        response = client.post("/components/reorder/live/", {"order": ids[::-1]})

        assert response.status_code == 400
        assert task_ids("live") == ids

    def test_the_pinned_list_keeps_an_order_that_leaves_its_first_task_alone(
        self, client
    ):
        client.get("/components/reorder/")
        ids = task_ids("live")
        wanted = [ids[0], ids[2], ids[1], *ids[3:]]

        response = client.post("/components/reorder/live/", {"order": wanted})

        assert response.status_code == 200
        assert task_ids("live") == wanted
