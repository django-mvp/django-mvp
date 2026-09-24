"""Tests for the app header's layout (issue #333).

The header reads left to right as "where you are, then what you can do": the
sidebar toggle, the site icon and the breadcrumb trail at the leading edge, the
actions at the trailing edge. The trail used to open the page body instead, on a
row of its own directly above a heading that repeated its last crumb.

Asserted against rendered markup rather than against a screenshot: the questions
here are which element exists, where it sits in the tree, and which classes it
carries, and all three fail loudly in HTML.
"""

import re

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
    """The breadcrumb trail is drawn once, in the app header."""

    def test_the_trail_renders_inside_the_header(self, client):
        soup = _soup(client, PAGE_WITH_TRAIL)
        trail = soup.find("nav", class_="breadcrumbs")
        assert trail is not None, "a page declaring breadcrumbs must render a trail"
        assert trail.find_parent(class_="mvp-header") is not None, (
            "the trail belongs to the app header, not the page body"
        )

    def test_the_page_body_draws_no_second_trail(self, client):
        """One trail per page. The page body used to draw its own, and a second
        copy is what this change exists to remove — so count, rather than
        assert the header's copy exists and stop there."""
        soup = _soup(client, PAGE_WITH_TRAIL)
        assert len(soup.find_all("nav", class_="breadcrumbs")) == 1

    def test_the_trail_carries_the_declared_crumbs(self, client):
        """Moving the trail must not change what a view declares: the crumbs
        are still the view's `get_breadcrumbs()` output, in order."""
        soup = _soup(client, PAGE_WITH_TRAIL)
        crumbs = soup.find("nav", class_="breadcrumbs").find_all("li")
        assert [crumb.get_text(strip=True) for crumb in crumbs] == [
            "Home",
            "Layout Demo",
        ]
        assert crumbs[0].find("a")["href"] == "/"

    def test_a_page_with_no_crumbs_renders_no_landmark(self, client):
        """An empty <nav aria-label="Breadcrumbs"> is a landmark a screen
        reader announces and then finds nothing in. A page that declares no
        trail renders no nav at all."""
        soup = _soup(client, PAGE_WITHOUT_TRAIL)
        assert soup.find("nav", class_="breadcrumbs") is None

    def test_the_heading_is_a_plain_heading_again(self, client):
        """The table view folded its <h1> into the trail's final crumb to save
        a row. With the trail in the header that trade is off: one <h1>, and
        not inside a nav."""
        soup = _soup(client, PAGE_WITH_TRAIL)
        headings = soup.find_all("h1")
        assert len(headings) == 1
        assert headings[0].find_parent("nav", class_="breadcrumbs") is None


@pytest.mark.django_db
class TestTheHeaderLeadingEdge:
    """Sidebar toggle, then the site icon, then the trail."""

    def test_the_site_icon_links_home(self, client):
        soup = _soup(client, PAGE_WITH_TRAIL)
        brand = soup.find("a", class_="mvp-navbar-brand")
        assert brand is not None
        assert brand["href"] == "/"
        assert brand.find("img") is not None, (
            "the header carries the site icon, not the site name as text"
        )

    def test_the_icon_and_the_trail_share_the_leading_edge(self, client):
        soup = _soup(client, PAGE_WITH_TRAIL)
        start = soup.find(class_="navbar-start")
        assert start.find("a", class_="mvp-navbar-brand") is not None
        assert start.find("nav", class_="breadcrumbs") is not None

    def test_the_leading_edge_can_shrink(self, client):
        """A long trail must be allowed to shrink and scroll rather than push
        the actions off the row: a flex item will not shrink below its content
        without min-w-0, and the trail is the item that can be long."""
        soup = _soup(client, PAGE_WITH_TRAIL)
        assert "min-w-0" in soup.find(class_="navbar-start").get("class", [])
        trail = soup.find("nav", class_="breadcrumbs")
        assert "min-w-0" in trail.get("class", [])


@pytest.mark.django_db
class TestTheBrandMarkAppearsOnce:
    """The sidebar header draws the site icon too. Wherever that header is on
    screen, the header's copy stands down — otherwise a desktop page with the
    sidebar open shows the brand mark twice, once in each region."""

    def _brand_classes(self, client):
        soup = _soup(client, PAGE_WITH_TRAIL)
        brand = soup.find("a", class_="mvp-navbar-brand")
        assert brand is not None
        return brand.get("class", [])

    def _toggle_classes(self, client):
        """Scoped to the navbar on purpose: the drawer overlay is also a label
        pointing at `mvp-app-toggle`, and it is not the button under test."""
        soup = _soup(client, PAGE_WITH_TRAIL)
        toggle = soup.find(class_="navbar-start").find(
            "label", attrs={"for": "mvp-app-toggle"}
        )
        assert toggle is not None
        return toggle.get("class", [])

    def test_the_icon_carries_the_sidebar_echo_class(self, client):
        """The stylesheet rule that hides this element under the shell's
        resolved layout (T015 — replaces sidebar_navbar_toggle_class,
        mvp/templatetags/mvp.py) selects on the drawer element's
        data-mvp-breakpoint/data-mvp-collapse attributes rather than a class
        built here. Computed-visibility proof, across every collapse mode
        and breakpoint, lives in
        tests/test_components/test_responsive_visibility.py
        (TestSidebarEchoRegion). What rendered markup can still show is that
        the icon carries the marker class that rule selects on."""
        assert "mvp-sidebar-hidden-only" in self._brand_classes(client)

    def test_the_icon_reflects_a_config_level_collapse_override(
        self, client, monkeypatch
    ):
        """`icons` collapse: the collapsed rail still shows the brand icon, so
        the stylesheet rule needs the resolved collapse mode, not just the
        breakpoint — proved by the drawer element (the shared ancestor the
        rule selects through) carrying it."""
        monkeypatch.setitem(MVP_CONFIG["layout"]["sidebar"], "collapse", "icons")
        content = client.get(PAGE_WITH_TRAIL).content.decode()
        assert 'data-mvp-collapse="icons"' in content
        assert "mvp-sidebar-hidden-only" in self._brand_classes(client)

    def test_the_icon_reflects_a_config_level_breakpoint_override(
        self, client, monkeypatch
    ):
        monkeypatch.setitem(MVP_CONFIG["layout"]["sidebar"], "breakpoint", "md")
        content = client.get(PAGE_WITH_TRAIL).content.decode()
        assert 'data-mvp-breakpoint="md"' in content
        assert "mvp-sidebar-hidden-only" in self._brand_classes(client)

    def test_the_icon_and_the_toggle_share_the_same_visibility_class(self, client):
        """They are the two things the sidebar header duplicates, and they
        appear and disappear on exactly the same condition — the stylesheet
        rule (T015) selects both of them by this one class."""
        assert "mvp-sidebar-hidden-only" in self._brand_classes(client)
        assert "mvp-sidebar-hidden-only" in self._toggle_classes(client)

    def test_the_icon_reflects_a_disabled_breakpoint(self, client, monkeypatch):
        """With no breakpoint the sidebar is an overlay at every width, so its
        header is never sitting beside the navbar and the icon always shows —
        proved end to end in test_responsive_visibility.py
        (TestSidebarEchoRegion::test_shown_at_every_width_when_never)."""
        monkeypatch.setitem(MVP_CONFIG["layout"]["sidebar"], "breakpoint", "never")
        content = client.get(PAGE_WITH_TRAIL).content.decode()
        assert 'data-mvp-breakpoint="never"' in content


@pytest.mark.django_db
class TestTheActionsGiveWayToTheTrail:
    """The trailing edge is hidden below the sidebar breakpoint."""

    def _actions_classes(self, client, url=PAGE_WITH_TRAIL):
        content = client.get(url).content.decode()
        match = re.search(
            r'<div\s+id="mvp-navbar-widgets-desktop"\s+class="([^"]*)"', content
        )
        assert match is not None, "the header's action region must render"
        return match.group(1).split()

    def test_actions_carry_the_wide_only_class(self, client):
        """The visibility rule itself lives in the stylesheet (T015 —
        replaces navbar_wide_only_class), selected by the drawer element's
        resolved breakpoint attribute."""
        classes = self._actions_classes(client)
        assert "mvp-desktop-only" in classes

    def test_the_region_follows_a_config_level_breakpoint_override(
        self, client, monkeypatch
    ):
        """The visibility rule is keyed off `layout.sidebar.breakpoint`, so a
        project that moves the sidebar's breakpoint moves this with it rather
        than being left with a hardcoded `lg` — proved by the drawer element
        (the shared ancestor the stylesheet rule selects through) carrying
        the override."""
        monkeypatch.setitem(MVP_CONFIG["layout"]["sidebar"], "breakpoint", "md")
        content = client.get(PAGE_WITH_TRAIL).content.decode()
        assert 'data-mvp-breakpoint="md"' in content
        assert "mvp-desktop-only" in self._actions_classes(client)

    def test_project_header_content_gives_way_with_the_widgets(self, client):
        """The `right` slot shares the configured widgets' region rather than
        having a visibility rule of its own — a project's own header content is
        an action like any other."""
        soup = _soup(client, PAGE_WITH_TRAIL)
        region = soup.find(id="mvp-navbar-widgets-desktop")
        assert region is not None
        assert region.find_parent(class_="navbar-end") is not None

    def test_the_mobile_region_is_absent_when_nothing_is_configured(
        self, client, monkeypatch
    ):
        """An empty configured list renders no wrapper. A wrapper that is a
        flex item with no children still spends its parent's gap."""
        monkeypatch.setitem(MVP_CONFIG["layout"]["navbar"]["mobile"], "end", [])
        content = client.get(PAGE_WITH_TRAIL).content.decode()
        assert 'id="mvp-navbar-widgets-mobile"' not in content

    def test_the_mobile_region_renders_when_a_widget_is_configured(
        self, client, monkeypatch
    ):
        """`layout.navbar.mobile.end` is the way a control earns its width back
        below the breakpoint, so it must still reach the markup."""
        monkeypatch.setitem(
            MVP_CONFIG["layout"]["navbar"]["mobile"],
            "end",
            ["actions.theme-controller"],
        )
        content = client.get(PAGE_WITH_TRAIL).content.decode()
        match = re.search(
            r'<div\s+id="mvp-navbar-widgets-mobile"\s+class="([^"]*)"', content
        )
        assert match is not None
        classes = match.group(1).split()
        assert "mvp-mobile-only" in classes


@pytest.mark.django_db
class TestTheHeaderShowsWhenHtmxIsWorking:
    """[#397] The header carries one loading spinner that shows while any htmx
    request is in flight, so a project using the package's own htmx
    behaviour, such as the boosted sidebar, needs no indicator of its own."""

    def test_the_header_draws_the_indicator(self, client):
        indicator = _soup(client, PAGE_WITH_TRAIL).find(id="mvp-htmx-indicator")

        assert indicator is not None
        assert indicator.find_parent(class_="mvp-header") is not None
        assert {"htmx-indicator", "loading", "loading-spinner"} <= set(
            indicator["class"]
        )

    def test_the_indicator_sits_at_the_start_of_the_actions(self, client):
        soup = _soup(client, PAGE_WITH_TRAIL)
        actions = soup.find(class_="navbar-end")
        first = actions.find(True)

        assert first["id"] == "mvp-htmx-indicator"

    def test_the_indicator_is_outside_the_width_dependent_regions(self, client):
        """Shown at every width: the desktop and mobile widget regions each
        disappear at one side of the sidebar breakpoint."""
        indicator = _soup(client, PAGE_WITH_TRAIL).find(id="mvp-htmx-indicator")

        assert indicator.find_parent(id="mvp-navbar-widgets-desktop") is None
        assert indicator.find_parent(id="mvp-navbar-widgets-mobile") is None
        assert "mvp-desktop-only" not in indicator["class"]
        assert "mvp-mobile-only" not in indicator["class"]

    def test_every_htmx_request_on_the_page_points_at_it(self, client):
        """``hx-indicator`` is inherited, so declaring it on the body covers
        every htmx element on the page, boosted links included."""
        body = _soup(client, PAGE_WITH_TRAIL).find("body")

        assert body["hx-indicator"] == "#mvp-htmx-indicator"
