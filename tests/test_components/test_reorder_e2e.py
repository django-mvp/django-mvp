"""The reorderable list in a real browser: dragging, the buttons, the destinations.

Whether a row follows the pointer and which rows make room is computed layout
and event behaviour, so only a browser can settle it. Each case loads a
test-only page, ``/reorder-test/``, drawn at desktop width.
"""

import pytest
from django.http import HttpResponse
from django.template import engines
from django.urls import path
from django_cotton.compiler_regex import CottonCompiler

from demo import urls as demo_urls
from tests.conftest import requires_browser, urlconf_of

pytestmark = [pytest.mark.e2e, requires_browser]

VIEWPORT = {"width": 1280, "height": 900}

PAGE = """
{% extends "mvp/base.html" %}
{% block content %}
<c-mvp.reorder id="steps" label="Steps">
  <c-mvp.reorder.row value="a" label="Alpha">Alpha</c-mvp.reorder.row>
  <c-mvp.reorder.row value="b" label="Beta">Beta</c-mvp.reorder.row>
  <c-mvp.reorder.row value="c" label="Gamma">Gamma</c-mvp.reorder.row>
</c-mvp.reorder>
{% endblock %}
"""


def reorder_test_page(request):
    """Draw the test page."""
    template = engines["django"].from_string(CottonCompiler().process(PAGE))
    return HttpResponse(template.render({}, request))


@pytest.fixture(autouse=True)
def reorder_test_urls(settings):
    settings.ROOT_URLCONF = urlconf_of(
        path("reorder-test/", reorder_test_page), *demo_urls.urlpatterns
    )


def open_page(page, live_server):
    page.set_default_timeout(5000)
    page.set_viewport_size(VIEWPORT)
    page.goto(f"{live_server.url}/reorder-test/")
    page.wait_for_function("window.Alpine !== undefined")


def values(page, root="#steps"):
    """The rows' identifiers in document order."""
    return page.eval_on_selector_all(
        f"{root} [data-mvp-reorder-row]",
        "rows => rows.map(row => row.dataset.mvpReorderValue)",
    )


def drag(page, source, target, below=True, grab="[data-mvp-reorder-handle]"):
    """Drag the row ``source`` by ``grab`` until it is over the row ``target``."""
    start = page.locator(f'#steps [data-mvp-reorder-value="{source}"] {grab}')
    end = page.locator(f'#steps [data-mvp-reorder-value="{target}"]').bounding_box()
    box = start.bounding_box()
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.down()
    y = end["y"] + end["height"] * (0.75 if below else 0.25)
    page.mouse.move(box["x"] + box["width"] / 2, y, steps=12)
    page.mouse.up()


class TestDraggingARow:
    def test_dragging_a_row_by_its_handle_moves_it_and_the_rows_it_passed(
        self, page, live_server
    ):
        open_page(page, live_server)

        drag(page, "a", "c")

        assert values(page) == ["b", "c", "a"]

    def test_dragging_from_outside_the_handle_starts_nothing(self, page, live_server):
        open_page(page, live_server)

        drag(page, "a", "c", grab="div")

        assert values(page) == ["a", "b", "c"]


class TestMoveButtons:
    def test_the_down_button_swaps_a_row_with_the_next_one(self, page, live_server):
        open_page(page, live_server)

        page.locator(
            '#steps [data-mvp-reorder-value="a"] [data-mvp-reorder-down]'
        ).click()

        assert values(page) == ["b", "a", "c"]

    def test_the_up_button_swaps_a_row_with_the_previous_one(self, page, live_server):
        open_page(page, live_server)

        page.locator(
            '#steps [data-mvp-reorder-value="c"] [data-mvp-reorder-up]'
        ).click()

        assert values(page) == ["a", "c", "b"]

    def test_the_first_rows_up_button_does_nothing(self, page, live_server):
        open_page(page, live_server)

        page.locator(
            '#steps [data-mvp-reorder-value="a"] [data-mvp-reorder-up]'
        ).dispatch_event("click")

        assert values(page) == ["a", "b", "c"]

    def test_the_controls_show_once_the_list_is_active(self, page, live_server):
        open_page(page, live_server)

        hidden = page.eval_on_selector_all(
            "#steps [data-mvp-reorder-up], #steps [data-mvp-reorder-handle]",
            "els => els.map(el => el.hidden)",
        )

        assert hidden == [False] * 6
