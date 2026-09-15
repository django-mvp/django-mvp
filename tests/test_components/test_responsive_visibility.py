"""Characterisation tests for FS-029 US-3 T013.

Written against the package **as it is today**, before `navbar_wide_only_class`,
`navbar_narrow_only_class` and `sidebar_navbar_toggle_class`
(``mvp/templatetags/mvp.py``) are replaced by static stylesheet rules (T015).
Green now, they must stay green, unmodified, once the substitution lands —
that is the whole proof the substitution changed no behaviour (plan.md "How
the substitution is proved").

**Article XIV exception.** This repository's habit is to assert the class
string a tag produces in rendered HTML. That cannot prove this substitution:
the class strings are the mechanism being replaced, so an assertion on them
either pins the old mechanism (and breaks when the tags are deleted, ceasing
to be a regression test) or pins the new one (and says nothing about
whether the old behaviour survived). Equivalence across six breakpoint
settings and two collapse modes is not expressible from rendered HTML once
visibility moves into the stylesheet, so these tests instead assert
**computed visibility in a real browser** — the resolved ``display`` of each
governed region — which is indifferent to how visibility is achieved.

The four governed regions (mvp/templates/cotton/app/header/navbar.html and
mvp/templates/mvp/account/base.html):

1. the navbar's mobile widget list (``navbar_narrow_only_class``)
2. the navbar's desktop widget list and ``right`` slot (``navbar_wide_only_class``)
3. the navbar's sidebar-toggle button and site icon (``sidebar_navbar_toggle_class``)
4. the account layout's collapsed navigation control (``navbar_narrow_only_class``)
   and persistent card (``navbar_wide_only_class``)

One fixture page (``tests/responsive_visibility_regions.html``, rendered by
``_RegionsView`` below) extends the account layout inside the full shell, so
a single page load exercises all four regions for one breakpoint/collapse
combination. Widths are exercised by resizing the viewport rather than
reloading: every rule under test is pure CSS (media queries, and — for the
sidebar-toggle region in ``offcanvas`` mode — the drawer checkbox's current
state), so a resize alone changes what a media query matches without
disturbing anything else.

Per decisions.md D11: wait for conditions, never for durations — a page
under test here never needs a wait at all, since nothing asserted depends on
the deferred JavaScript bundle finishing (the drawer's checkbox state comes
from the server-rendered default and the synchronous pre-paint script).
"""

import pytest
from django.test import override_settings
from django.urls import path
from django.views.generic import TemplateView
from playwright.sync_api import expect

from tests.conftest import requires_browser

pytestmark = [pytest.mark.e2e, requires_browser, pytest.mark.django_db]

VIEWPORT_HEIGHT = 900

#: Breakpoint name -> Tailwind min-width in px (mvp/layout.py BREAKPOINT_WIDTHS).
REAL_BREAKPOINTS = {"sm": 640, "md": 768, "lg": 1024, "xl": 1280, "2xl": 1536}

#: `never` has no width to key off; two arbitrary, far-apart widths prove the
#: regions it governs behave identically at both.
NEVER_WIDTHS = (375, 1920)


class _RegionsView(TemplateView):
    """Renders the four-region fixture with breakpoint/collapse from the
    query string — the same pattern ``demo.views.LayoutStoreDemoView`` uses,
    scoped to this test module rather than added to the demo's own routes."""

    template_name = "tests/responsive_visibility_regions.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breakpoint"] = self.request.GET.get("breakpoint")
        context["collapse"] = self.request.GET.get("collapse")
        return context


def _regions_urlconf():
    """The project's own urlconf with the fixture route prepended — mirrors
    ``tests/test_components/test_sidebar_persisted_state.py``'s
    ``sidebar_shell_urlconf``. Prepending rather than replacing keeps
    ``mvp.urls`` mounted, which the account layout's menu needs to reverse."""
    from importlib import import_module

    from django.conf import settings

    base_urlpatterns = import_module(settings.ROOT_URLCONF).urlpatterns
    route = path(
        "responsive-visibility-regions/", _RegionsView.as_view(), name="_regions"
    )
    return type("_URLConf", (), {"urlpatterns": [route, *base_urlpatterns]})


REGIONS_URLCONF = _regions_urlconf()


@pytest.fixture
def regions_server(live_server):
    """``live_server``, with the fixture route mounted for the duration of
    the test."""
    with override_settings(ROOT_URLCONF=REGIONS_URLCONF):
        yield live_server


def _goto(page, regions_server, *, bp=None, collapse=None, viewport):
    page.set_viewport_size({"width": viewport, "height": VIEWPORT_HEIGHT})
    params = []
    if bp is not None:
        params.append(f"breakpoint={bp}")
    if collapse is not None:
        params.append(f"collapse={collapse}")
    url = f"{regions_server.url}/responsive-visibility-regions/"
    if params:
        url = f"{url}?{'&'.join(params)}"
    page.goto(url)


def _resize(page, viewport):
    page.set_viewport_size({"width": viewport, "height": VIEWPORT_HEIGHT})


def _display(locator):
    return locator.evaluate("el => getComputedStyle(el).display")


def _mobile_widgets(page):
    return page.locator("#mvp-navbar-widgets-mobile")


def _desktop_widgets(page):
    return page.locator("#mvp-navbar-widgets-desktop")


def _toggle_label(page):
    return page.locator('label[aria-label="Open sidebar"]')


def _site_icon(page):
    """The navbar's copy of the brand icon — distinct from the sidebar
    header's own ``a[aria-label="Home"]``, which shares the same label."""
    return page.locator("a.mvp-navbar-brand")


def _account_nav_container(page):
    return page.locator("div.lg\\:items-start")


def _account_narrow(page):
    """The collapsed account-navigation control: the first of the
    container's three children (dropdown, page content, card)."""
    return _account_nav_container(page).locator("> div").first


def _account_wide(page):
    """The persistent account-navigation card: the last of the container's
    three children."""
    return _account_nav_container(page).locator("> div").last


def _drawer_checkbox(page):
    return page.locator("#mvp-app-toggle")


def _close_drawer(page):
    # A native click() rather than a coordinate-based one: at desktop widths
    # the overlay label sits behind other content and a coordinate click can
    # miss it (mirrors test_layout_store.py's TestAnElementBoundToTheStore...).
    page.locator('label[for="mvp-app-toggle"][aria-label="Close sidebar"]').evaluate(
        "el => el.click()"
    )


def _open_drawer(page):
    # Same reasoning as _close_drawer: drive the native control directly
    # rather than racing the drawer's transition for a clickable point.
    page.locator('label[for="mvp-app-toggle"][aria-label="Open sidebar"]').first.evaluate(
        "el => el.click()"
    )


# ---------------------------------------------------------------------------
# Region 1 + region 4 (narrow half): navbar_narrow_only_class
# ---------------------------------------------------------------------------


class TestNarrowOnlyRegions:
    """The navbar's mobile widget list and the account layout's collapsed
    navigation control: shown below the configured breakpoint, hidden at and
    above it. Under `never` — asymmetrically — hidden at every width, so the
    mobile copy never doubles up with the (unconditionally shown) wide
    region (D7)."""

    @pytest.mark.parametrize(("bp", "px"), REAL_BREAKPOINTS.items())
    def test_shown_below_hidden_at_or_above(self, page, regions_server, bp, px):
        _goto(page, regions_server, bp=bp, viewport=px - 1)
        assert _display(_mobile_widgets(page)) != "none"
        assert _display(_account_narrow(page)) != "none"

        _resize(page, px)
        assert _display(_mobile_widgets(page)) == "none"
        assert _display(_account_narrow(page)) == "none"

    def test_hidden_at_every_width_when_never(self, page, regions_server):
        for width in NEVER_WIDTHS:
            _goto(page, regions_server, bp="never", viewport=width)
            assert _display(_mobile_widgets(page)) == "none"
            assert _display(_account_narrow(page)) == "none"

    def test_unrecognised_breakpoint_falls_back_to_lg(self, page, regions_server):
        lg_px = REAL_BREAKPOINTS["lg"]
        _goto(page, regions_server, bp="bogus", viewport=lg_px - 1)
        assert _display(_mobile_widgets(page)) != "none"

        _resize(page, lg_px)
        assert _display(_mobile_widgets(page)) == "none"


# ---------------------------------------------------------------------------
# Region 2 + region 4 (wide half): navbar_wide_only_class
# ---------------------------------------------------------------------------


class TestWideOnlyRegions:
    """The navbar's desktop widget list (and ``right`` slot) and the account
    layout's persistent card: hidden below the configured breakpoint, shown
    at and above it. Under `never` there is no width to key off, so both
    stay unconditionally shown (D1)."""

    @pytest.mark.parametrize(("bp", "px"), REAL_BREAKPOINTS.items())
    def test_hidden_below_shown_at_or_above(self, page, regions_server, bp, px):
        _goto(page, regions_server, bp=bp, viewport=px - 1)
        assert _display(_desktop_widgets(page)) == "none"
        assert _display(_account_wide(page)) == "none"

        _resize(page, px)
        assert _display(_desktop_widgets(page)) != "none"
        assert _display(_account_wide(page)) != "none"

    def test_shown_at_every_width_when_never(self, page, regions_server):
        for width in NEVER_WIDTHS:
            _goto(page, regions_server, bp="never", viewport=width)
            assert _display(_desktop_widgets(page)) != "none"
            assert _display(_account_wide(page)) != "none"

    def test_unrecognised_breakpoint_falls_back_to_lg(self, page, regions_server):
        lg_px = REAL_BREAKPOINTS["lg"]
        _goto(page, regions_server, bp="bogus", viewport=lg_px - 1)
        assert _display(_desktop_widgets(page)) == "none"

        _resize(page, lg_px)
        assert _display(_desktop_widgets(page)) != "none"


# ---------------------------------------------------------------------------
# Region 3: sidebar_navbar_toggle_class
# ---------------------------------------------------------------------------


class TestSidebarEchoRegion:
    """The navbar's own copies of the sidebar-toggle button and the site
    icon: hidden wherever the sidebar header already shows its own copy of
    both. In `icons` mode that is unconditional at and above the breakpoint;
    in `offcanvas` mode only while the drawer is open there (a fully
    collapsed sidebar has neither on screen). Under `never` both stay shown
    everywhere — there is no width, and no persistent sidebar header to echo."""

    @pytest.mark.parametrize(("bp", "px"), REAL_BREAKPOINTS.items())
    def test_icons_mode_hides_at_or_above_unconditionally(
        self, page, regions_server, bp, px
    ):
        _goto(page, regions_server, bp=bp, collapse="icons", viewport=px - 1)
        assert _display(_toggle_label(page)) != "none"
        assert _display(_site_icon(page)) != "none"

        _resize(page, px)
        assert _display(_toggle_label(page)) == "none"
        assert _display(_site_icon(page)) == "none"

        # "Unconditionally" is the word this test has to earn. A persistent
        # drawer defaults open, so without closing it a rule wrongly gated on
        # the drawer being open would pass here too.
        _close_drawer(page)
        assert _display(_toggle_label(page)) == "none"
        assert _display(_site_icon(page)) == "none"

    @pytest.mark.parametrize(("bp", "px"), REAL_BREAKPOINTS.items())
    def test_offcanvas_mode_shown_below_regardless_of_drawer_state(
        self, page, regions_server, bp, px
    ):
        _goto(page, regions_server, bp=bp, collapse="offcanvas", viewport=px - 1)
        assert _display(_toggle_label(page)) != "none"
        assert _display(_site_icon(page)) != "none"

        # Below the breakpoint the drawer is an overlay, and opening it must
        # not hide either control — the rule that does the hiding is inside a
        # width query, and dropping that query would go unnoticed without this.
        _open_drawer(page)
        assert _display(_toggle_label(page)) != "none"
        assert _display(_site_icon(page)) != "none"

    def test_offcanvas_mode_hides_at_or_above_only_while_open(
        self, page, regions_server
    ):
        """One representative breakpoint (`lg`, the package default) proves
        the drawer-state dependency itself; the rule is structurally
        identical at every other breakpoint (D7)."""
        lg_px = REAL_BREAKPOINTS["lg"]
        _goto(page, regions_server, bp="lg", collapse="offcanvas", viewport=lg_px)
        # A persistent drawer defaults open on a fresh load (issue #178's
        # pre-paint script) — the precondition for the "hidden while open"
        # half of this test.
        expect(_drawer_checkbox(page)).to_be_checked()
        assert _display(_toggle_label(page)) == "none"
        assert _display(_site_icon(page)) == "none"

        _close_drawer(page)
        expect(_drawer_checkbox(page)).not_to_be_checked()
        assert _display(_toggle_label(page)) != "none"
        assert _display(_site_icon(page)) != "none"

    def test_shown_at_every_width_when_never(self, page, regions_server):
        for collapse in ("icons", "offcanvas"):
            for width in NEVER_WIDTHS:
                _goto(
                    page,
                    regions_server,
                    bp="never",
                    collapse=collapse,
                    viewport=width,
                )
                assert _display(_toggle_label(page)) != "none"
                assert _display(_site_icon(page)) != "none"

    def test_unrecognised_breakpoint_falls_back_to_lg(self, page, regions_server):
        lg_px = REAL_BREAKPOINTS["lg"]
        _goto(
            page,
            regions_server,
            bp="bogus",
            collapse="icons",
            viewport=lg_px - 1,
        )
        assert _display(_toggle_label(page)) != "none"

        _resize(page, lg_px)
        assert _display(_toggle_label(page)) == "none"


# ---------------------------------------------------------------------------
# Without JavaScript (T016)
# ---------------------------------------------------------------------------


class TestVisibilityWithoutJavaScript:
    """One representative setting, with JavaScript disabled entirely, proving
    computed visibility is identical to every other test in this module.
    `lg`/`icons` is representative because none of the four regions' rules
    depend on anything JavaScript sets up — every rule this module exercises
    is pure CSS, keyed off attributes the server already rendered."""

    def test_visibility_is_identical_with_javascript_disabled(
        self, browser, regions_server
    ):
        context = browser.new_context(java_script_enabled=False)
        try:
            page = context.new_page()
            lg_px = REAL_BREAKPOINTS["lg"]
            page.set_viewport_size({"width": lg_px - 1, "height": VIEWPORT_HEIGHT})
            page.goto(
                f"{regions_server.url}/responsive-visibility-regions/"
                "?breakpoint=lg&collapse=icons"
            )
            assert _display(_mobile_widgets(page)) != "none"
            assert _display(_desktop_widgets(page)) == "none"
            assert _display(_account_narrow(page)) != "none"
            assert _display(_account_wide(page)) == "none"
            assert _display(_toggle_label(page)) != "none"
            assert _display(_site_icon(page)) != "none"

            page.set_viewport_size({"width": lg_px, "height": VIEWPORT_HEIGHT})
            assert _display(_mobile_widgets(page)) == "none"
            assert _display(_desktop_widgets(page)) != "none"
            assert _display(_account_narrow(page)) == "none"
            assert _display(_account_wide(page)) != "none"
            assert _display(_toggle_label(page)) == "none"
            assert _display(_site_icon(page)) == "none"
        finally:
            context.close()
