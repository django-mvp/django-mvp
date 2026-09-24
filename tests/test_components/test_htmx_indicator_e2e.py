"""The header's htmx indicator shows while a request is in flight (#397).

The rendered-markup tests in test_app_header.py prove the spinner and the
body's ``hx-indicator`` exist. Whether htmx actually lights the spinner up
depends on attribute inheritance and on the stylesheet htmx injects, and only a
browser can settle that. Each test holds the request open until the spinner
has been seen on screen, then lets it finish and waits for it to go away.
"""

import pytest
from playwright.sync_api import expect

from mvp.config import MVP_CONFIG
from tests.conftest import requires_browser

pytestmark = [pytest.mark.e2e, requires_browser]

DESKTOP = {"width": 1280, "height": 800}
MOBILE = {"width": 375, "height": 812}


def _hold(page, pattern):
    """Intercept requests matching ``pattern`` and leave them pending."""
    held = []
    page.route(pattern, lambda route: held.append(route))
    return held


@pytest.mark.django_db
class TestTheIndicatorShowsDuringARequest:
    def test_a_boosted_sidebar_link_shows_the_spinner(
        self, page, live_server, monkeypatch
    ):
        monkeypatch.setitem(MVP_CONFIG["layout"]["sidebar"], "boost", True)
        page.set_viewport_size(DESKTOP)
        page.goto(live_server.url)
        indicator = page.locator("#mvp-htmx-indicator")
        expect(indicator).to_be_hidden()

        held = _hold(page, "**/layout/")
        page.locator('[hx-boost="true"] a[href="/layout/"]').first.click()

        expect(indicator).to_be_visible()
        expect(indicator).to_have_css("opacity", "1")
        held[0].continue_()
        expect(page).to_have_url(f"{live_server.url}/layout/")
        expect(page.locator("#mvp-htmx-indicator")).to_be_hidden()

    @pytest.mark.parametrize("viewport", [DESKTOP, MOBILE], ids=["desktop", "mobile"])
    def test_the_spinner_shows_at_every_width(self, page, live_server, viewport):
        """The widget regions beside it each disappear at one side of the
        sidebar breakpoint, and the spinner must not go with them. A request
        sent from the body lights it up with or without ``hx-indicator``,
        so the boosted-link test above is the one that proves the attribute."""
        page.set_viewport_size(viewport)
        page.goto(live_server.url)
        indicator = page.locator("#mvp-htmx-indicator")
        expect(indicator).to_be_hidden()

        held = _hold(page, "**/layout/")
        # Not returned: htmx.ajax's promise settles only once the held
        # request completes, and evaluate would wait for it.
        page.evaluate("() => { htmx.ajax('GET', '/layout/', {swap: 'none'}); }")

        expect(indicator).to_be_visible()
        expect(indicator).to_have_css("opacity", "1")
        held[0].continue_()
        expect(indicator).to_be_hidden()
