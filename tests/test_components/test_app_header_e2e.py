"""The header's breadcrumb trail does not scroll sideways (issue #354).

A rendered-HTML test can only assert which classes sit on which element. The
claim here is about *computed layout* — that the trail's content fits inside
the box it is drawn in, at widths where it used to spill out of it — and only
a browser can settle that. Following tests/test_table_layout_e2e.py.

The overflow condition is asserted as ``scrollWidth <= clientWidth`` rather
than by measuring for a scrollbar directly: headless Chromium draws overlay
scrollbars, so ``offsetHeight - clientHeight`` reports 0 whether or not the
trail overflows, and a test built on that would pass either way. A trail
whose content is wider than its own box is exactly the condition that makes a
real browser draw the bar, regardless of scrollbar style.
"""

import pytest

from tests.conftest import requires_browser
from tests.factories import ProductFactory

pytestmark = [pytest.mark.e2e, requires_browser]

# Three crumbs deep with a long object name in the middle, which is the trail
# the report was filed against: an edit page reached through a list and a
# detail page, for an object whose title is a sentence.
LONG_NAME = "My object title that is really quite a lot longer than it looks"

VIEWPORTS = {
    "desktop": {"width": 1280, "height": 900},
    "wide": {"width": 1920, "height": 1080},
    "narrow": {"width": 900, "height": 900},
    "mobile": {"width": 390, "height": 844},
}

at_every_viewport = pytest.mark.parametrize(
    "viewport", VIEWPORTS.values(), ids=list(VIEWPORTS)
)


def _trail_fit(page, url, viewport):
    page.set_viewport_size(viewport)
    page.goto(url)
    return page.evaluate("""
        () => {
          const trail = document.querySelector('nav.breadcrumbs');
          return {
            trailScrollWidth: trail.scrollWidth,
            trailClientWidth: trail.clientWidth,
          };
        }
    """)


def _crumb_texts(page, url, viewport):
    page.set_viewport_size(viewport)
    page.goto(url)
    return page.evaluate("""
        () => [...document.querySelectorAll('.mvp-breadcrumb-text')].map(el => ({
          text: el.textContent,
          scrollWidth: el.scrollWidth,
          clientWidth: el.clientWidth,
        }))
    """)


@pytest.mark.django_db(transaction=True)
class TestTheTrailDoesNotScroll:
    """Measured in Chromium at 1280/1920/900/390px: the trail's content never
    exceeds its own box at any of these widths, so the browser draws no
    scrollbar at the sizes a real page is actually viewed at."""

    @at_every_viewport
    def test_a_long_trail_fits_the_row(self, page, live_server, viewport):
        product = ProductFactory(name=LONG_NAME)
        fit = _trail_fit(
            page, f"{live_server.url}/products/{product.pk}/edit/", viewport
        )
        assert fit["trailScrollWidth"] <= fit["trailClientWidth"], (
            "the trail overflows its own box, so the browser draws a "
            f"horizontal scrollbar: {fit}"
        )


@pytest.mark.django_db(transaction=True)
class TestALongTrailShrinksInsteadOfScrolling:
    """[#354] At 390px — measured: each crumb's own text is clipped by the
    browser (an ellipsis is showing) while the trail itself still does not
    overflow, and every crumb stays laid out in the row rather than being
    pushed out of it. Below roughly 280px the crumbs and the separators
    between them can no longer shrink any further and the trail does start to
    overflow — the scrollbar is still there for that width, but 390px (an
    ordinary phone viewport) is not it, which is what this test pins."""

    def test_each_crumb_is_visibly_truncated(self, page, live_server):
        product = ProductFactory(name=LONG_NAME)
        crumbs = _crumb_texts(
            page,
            f"{live_server.url}/products/{product.pk}/edit/",
            VIEWPORTS["mobile"],
        )
        assert len(crumbs) == 3
        for crumb in crumbs:
            assert crumb["scrollWidth"] > crumb["clientWidth"], (
                f"crumb {crumb['text']!r} is not clipped — its text fits "
                "without an ellipsis, so this width no longer demonstrates "
                "truncation"
            )

    def test_the_trail_still_does_not_overflow(self, page, live_server):
        product = ProductFactory(name=LONG_NAME)
        fit = _trail_fit(
            page,
            f"{live_server.url}/products/{product.pk}/edit/",
            VIEWPORTS["mobile"],
        )
        assert fit["trailScrollWidth"] <= fit["trailClientWidth"], (
            f"shrinking gave out before scrolling should have to: {fit}"
        )

    def test_every_crumb_stays_in_the_row(self, page, live_server):
        """Truncation must not come at the cost of a later crumb being pushed
        out of the row — each one still renders with real width, however
        small, rather than collapsing to nothing or being clipped out of the
        flex row entirely."""
        product = ProductFactory(name=LONG_NAME)
        crumbs = _crumb_texts(
            page,
            f"{live_server.url}/products/{product.pk}/edit/",
            VIEWPORTS["mobile"],
        )
        for crumb in crumbs:
            assert crumb["clientWidth"] > 0, (
                f"crumb {crumb['text']!r} has no width left at all — it was "
                "pushed out of the row rather than merely truncated"
            )
