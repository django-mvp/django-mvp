"""The site search's results page fits a phone screen, in a real browser (issue #676).

Whether a page is wider than the window is computed layout, so only a browser
settles it. The page is narrowed to one kind with six pages of results, the
case whose pager pushed the page past a 390px screen.

Source: mvp/templates/mvp/search/results.html
"""

import pytest

from mvp.search import registry as registry_module
from mvp.search.kinds import Result
from mvp.search.registry import SearchRegistry
from tests.conftest import requires_browser

pytestmark = [pytest.mark.e2e, requires_browser]

VIEWPORTS = {
    "desktop": {"width": 1440, "height": 900},
    "mobile": {"width": 390, "height": 844},
}

at_every_viewport = pytest.mark.parametrize(
    "viewport", VIEWPORTS.values(), ids=list(VIEWPORTS)
)


def pages(query, request):
    """Find 120 pages for any query: six pages of results at twenty a page."""
    return [
        Result(title=f"Page {n}", url=f"/components/?hit={n}", where="Pages")
        for n in range(120)
    ]


@pytest.fixture(autouse=True)
def search_site(settings, monkeypatch):
    """Serve the search at ``search/`` with one kind of six pages registered."""
    search_registry = SearchRegistry()
    monkeypatch.setattr(registry_module, "default_registry", search_registry)
    settings.ROOT_URLCONF = "tests.urls_search"
    search_registry.register(pages, name="pages", label="Pages", icon="file")


class TestNarrowedResultsPage:
    @at_every_viewport
    @pytest.mark.parametrize("number", [1, 3, 6])
    def test_the_page_is_no_wider_than_the_window(
        self, page, live_server, viewport, number
    ):
        page.set_viewport_size(viewport)
        page.goto(f"{live_server.url}/search/?q=heat&kind=pages&page={number}")

        widths = page.evaluate(
            "() => [document.documentElement.scrollWidth, window.innerWidth]"
        )

        assert widths[0] <= widths[1]

    @at_every_viewport
    def test_a_visible_link_reaches_the_next_page(self, page, live_server, viewport):
        page.set_viewport_size(viewport)
        page.goto(f"{live_server.url}/search/?q=heat&kind=pages&page=3")

        page.locator("nav a:visible", has_text="Next").click()

        assert page.url.endswith("page=4")
