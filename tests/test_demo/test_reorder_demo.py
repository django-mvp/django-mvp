"""The reorder demo page and the views that save its lists.

Source: demo/views.py, demo/urls.py
"""

import pytest

from demo.views import ReorderDemoData

pytestmark = pytest.mark.django_db


def task_ids(name):
    """The ids of one list's tasks in their saved order, seeding the list if new."""
    return [task.pk for task in ReorderDemoData().tasks(name)]


class TestReorderDemoPage:
    def test_the_form_list_saves_the_order_it_posts(self, client):
        ids = task_ids("form")

        response = client.post("/components/reorder/", {"order": ids[::-1]})

        assert response.status_code == 302
        assert task_ids("form") == ids[::-1]

    def test_the_form_list_refuses_an_order_that_leaves_a_task_out(self, client):
        ids = task_ids("form")

        response = client.post("/components/reorder/", {"order": ids[1:]})

        assert response.status_code == 400
        assert task_ids("form") == ids


class TestReorderDemoSave:
    def test_a_posted_order_is_saved_and_the_list_drawn_again(self, client):
        ids = task_ids("mode")

        response = client.post("/components/reorder/mode/", {"order": ids[::-1]})

        assert response.status_code == 200
        assert task_ids("mode") == ids[::-1]
        assert b'id="mode-tasks"' in response.content

    def test_the_pinned_list_refuses_an_order_that_moves_its_first_task(self, client):
        ids = task_ids("live")

        response = client.post("/components/reorder/live/", {"order": ids[::-1]})

        assert response.status_code == 400
        assert task_ids("live") == ids

    def test_the_pinned_list_keeps_an_order_that_leaves_its_first_task_alone(
        self, client
    ):
        ids = task_ids("live")
        wanted = [ids[0], ids[2], ids[1], *ids[3:]]

        response = client.post("/components/reorder/live/", {"order": wanted})

        assert response.status_code == 200
        assert task_ids("live") == wanted
