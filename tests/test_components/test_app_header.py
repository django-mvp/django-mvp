"""Tests for the app header's layout (issue #333).

The header reads left to right as "where you are, then what you can do": the
sidebar toggle, the site icon and the breadcrumb trail at the leading edge, the
actions at the trailing edge. The trail used to open the page body instead, on a
row of its own directly above a heading that repeated its last crumb.

Asserted against rendered markup rather than against a screenshot: the questions
here are which element exists, where it sits in the tree, and which classes it
carries, and all three fail loudly in HTML.
"""

import pytest

from mvp.config import MVP_CONFIG
from mvp.fixtures import _beautiful_soup

# A demo page that declares a trail (DemoTemplateView.get_breadcrumbs), and one
# that declares none (the home view renders the landing/dashboard templates).
PAGE_WITH_TRAIL = "/layout/"
PAGE_WITHOUT_TRAIL = "/"


def _soup(client, url):
    return _beautiful_soup()(client.get(url).content.decode(), "html.parser")


@pytest.mark.django_db
class TestTheTrailLivesInTheHeader:
    def test_the_trail_renders_inside_the_header(self, client):
        soup = _soup(client, PAGE_WITH_TRAIL)
        trail = soup.find("nav", class_="mvp-crumbs")
        assert trail is not None, "a page declaring breadcrumbs must render a trail"
        assert trail.find_parent(class_="mvp-header") is not None, (
            "the trail belongs to the app header, not the page body"
        )

    def test_a_page_with_no_crumbs_renders_no_landmark(self, client):
        soup = _soup(client, PAGE_WITHOUT_TRAIL)
        assert soup.find("nav", class_="mvp-crumbs") is None


@pytest.mark.django_db
class TestTheHeaderLeadingEdge:
    def test_the_site_icon_links_home(self, client):
        soup = _soup(client, PAGE_WITH_TRAIL)
        brand = soup.find("a", class_="mvp-navbar-brand")
        assert brand is not None
        assert brand["href"] == "/"


@pytest.mark.django_db
class TestTheSidebarToggleOnMobile:
    def _toggle_classes(self, client):
        soup = _soup(client, PAGE_WITH_TRAIL)
        toggle = soup.find(class_="navbar-start").find(
            "label", attrs={"for": "mvp-app-toggle"}
        )
        assert toggle is not None
        return toggle.get("class", [])

    def test_the_toggle_gives_way_below_the_breakpoint_by_default(self, client):
        assert "mvp-desktop-only" in self._toggle_classes(client)

    def test_the_toggle_is_not_tied_to_the_desktop_when_the_setting_is_on(
        self, client, monkeypatch
    ):
        monkeypatch.setitem(
            MVP_CONFIG["layout"]["navbar"]["mobile"], "sidebar_toggle", True
        )
        assert "mvp-desktop-only" not in self._toggle_classes(client)

    def test_the_dock_still_carries_a_toggle_when_the_header_gives_its_own_up(
        self, client
    ):
        soup = _soup(client, PAGE_WITH_TRAIL)
        assert soup.find(class_="dock").find("label", attrs={"for": "mvp-app-toggle"})


@pytest.mark.django_db
class TestTheHeaderShowsWhenHtmxIsWorking:
    def test_the_header_draws_the_indicator(self, client):
        indicator = _soup(client, PAGE_WITH_TRAIL).find(id="mvp-htmx-indicator")

        assert indicator is not None
        assert indicator.find_parent(class_="mvp-header") is not None
        assert indicator["aria-hidden"] == "true"


@pytest.mark.django_db
class TestTheSiteNameBesideTheIcon:
    TITLE = "Example Portal"

    def brand_of(self, client, monkeypatch, title=TITLE, **mobile):
        monkeypatch.setitem(MVP_CONFIG["layout"]["sidebar"], "title", title)
        for key, value in mobile.items():
            monkeypatch.setitem(MVP_CONFIG["layout"]["navbar"]["mobile"], key, value)
        return _soup(client, PAGE_WITH_TRAIL).find("a", class_="mvp-navbar-brand")

    def test_the_header_shows_only_the_icon_by_default(self, client, monkeypatch):
        brand = self.brand_of(client, monkeypatch)

        assert self.TITLE not in brand.get_text()

    def test_the_header_shows_the_sidebar_title_beside_the_icon_when_asked(
        self, client, monkeypatch
    ):
        brand = self.brand_of(client, monkeypatch, site_name=True)

        assert brand.get_text(strip=True) == self.TITLE

    def test_no_sidebar_title_means_no_name_to_show(self, client, monkeypatch):
        brand = self.brand_of(client, monkeypatch, title=None, site_name=True)

        assert brand.get_text(strip=True) == ""
