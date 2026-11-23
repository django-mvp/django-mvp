"""The reorder demo page in a real browser: each list keeps the order it was given.

Moving a row, submitting or waiting for a post, and loading the page again are
browser and server behaviour together, so the case drives the demo's own page.
"""

import pytest
from playwright.sync_api import expect

from tests.conftest import requires_browser

pytestmark = [pytest.mark.e2e, requires_browser]

ORDER = """rows => rows.map(row => row.dataset.mvpReorderValue
  ?? row.querySelector('input[name$="-title"]').value)"""

LISTS = {
    "set": {"section": "row-set", "save": "submit"},
    "form": {"section": "in-a-form", "save": "submit"},
    "live": {"section": "posts-as-it-changes", "save": "/components/reorder/live/"},
    "mode": {"section": "on-demand", "save": "/components/reorder/mode/"},
}


def saved_order(section):
    return section.locator("[data-mvp-reorder-row]").evaluate_all(ORDER)


class TestReorderDemoPage:
    @pytest.mark.parametrize("width", [390, 1280])
    @pytest.mark.parametrize("name", list(LISTS))
    def test_a_moved_row_is_in_its_new_place_after_the_page_loads_again(
        self, page, live_server, name, width
    ):
        page.set_default_timeout(5000)
        page.set_viewport_size({"width": width, "height": 900})
        page.goto(f"{live_server.url}/components/reorder/")
        page.wait_for_function("window.Alpine !== undefined")
        section = page.locator(f"section#{LISTS[name]['section']}")
        before = saved_order(section)
        assert len(before) > 2
        if name == "mode":
            section.locator("[data-mvp-reorder-start]").click()
        row = section.locator("[data-mvp-reorder-row]").nth(2)

        if LISTS[name]["save"] == "submit":
            row.locator("[data-mvp-reorder-up]:visible").click()
            with page.expect_navigation():
                section.locator("button[type=submit]").click()
        else:
            with page.expect_response(
                lambda response: response.url.endswith(LISTS[name]["save"])
            ):
                row.locator("[data-mvp-reorder-up]:visible").click()
        page.reload()
        page.wait_for_function("window.Alpine !== undefined")

        after = saved_order(page.locator(f"section#{LISTS[name]['section']}"))
        assert after == [before[0], before[2], before[1], *before[3:]]

    def test_an_order_that_moves_the_pinned_task_is_refused_and_undone(
        self, page, live_server
    ):
        page.set_default_timeout(5000)
        page.set_viewport_size({"width": 1280, "height": 900})
        page.goto(f"{live_server.url}/components/reorder/")
        page.wait_for_function("window.Alpine !== undefined")
        section = page.locator("section#posts-as-it-changes")
        before = saved_order(section)

        with page.expect_response(
            lambda response: response.url.endswith("/components/reorder/live/")
        ) as response:
            section.locator("[data-mvp-reorder-down]:visible").first.click()

        assert response.value.status == 400
        expect(section.locator("[data-mvp-reorder-alert]")).to_be_visible()
        assert saved_order(section) == before


class TestReorderDemoLoadsLocally:
    def test_no_script_is_fetched_from_a_remote_origin(self, page, live_server):
        remote = []

        def record(request):
            if request.resource_type == "script" and not request.url.startswith(
                live_server.url
            ):
                remote.append(request.url)

        page.on("request", record)
        page.goto(f"{live_server.url}/components/reorder/", wait_until="networkidle")

        assert remote == []
