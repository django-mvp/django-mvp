"""Real-browser test for the link a ``<c-card>`` can take (issue #685).

The title's link is stretched over the card by a stylesheet rule, and the
controls inside are lifted above it by another. Only a browser shows that a
click lands on the right one, so this renders the demo's Link section.
"""

import pytest
from playwright.sync_api import expect

from tests.conftest import requires_browser

pytestmark = [pytest.mark.e2e, requires_browser]

PAGE = "/components/card/"


class TestCardLinkInTheBrowser:
    def test_a_click_on_the_body_opens_the_link(self, page, live_server):
        page.goto(f"{live_server.url}{PAGE}")

        body = page.locator("#linked_card .card-body").bounding_box()
        page.mouse.click(body["x"] + 40, body["y"] + 10)

        assert page.url.endswith("#opened")

    def test_a_button_in_the_card_does_its_own_thing(self, page, live_server):
        page.goto(f"{live_server.url}{PAGE}")

        page.locator("#linked_card_button").click()

        assert not page.url.endswith("#opened")
        expect(page.locator("#linked_card_button")).to_have_attribute(
            "data-pressed", "yes"
        )

    def test_the_card_has_one_tab_stop_for_its_link(self, page, live_server):
        page.goto(f"{live_server.url}{PAGE}")

        stops = page.evaluate(
            """() => [...document.querySelectorAll(
                '#linked_card a[href], #linked_card [tabindex]')].length"""
        )

        assert stops == 1
