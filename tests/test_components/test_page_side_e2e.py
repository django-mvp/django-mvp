"""The side panel's column in a real browser (FS-042, FR-007, FR-011).

Whether a panel sticks under the header, scrolls on its own, takes focus or
sits on the reading side is computed layout, so only a browser can settle it.
Alignment and widths are ruled by eye and not tested (testing standard §1).

Each case loads a test-only page, ``/side-test/``, that draws a title, a long
content column and a panel, with the page's options read from the query
string. It is drawn at 1440px, above the panel's default breakpoint.
"""

import pytest
from django.http import HttpResponse
from django.template import engines
from django.urls import path
from django_cotton.compiler_regex import CottonCompiler

from demo import urls as demo_urls
from tests.conftest import requires_browser, urlconf_of

pytestmark = [pytest.mark.e2e, requires_browser]

VIEWPORT = {"width": 1440, "height": 900}

PAGE = """
{% extends "mvp/base.html" %}
{% block content %}
<c-mvp.page :fill="fill">
  <c-mvp.page.content>
    <c-mvp.page.layout>
      <c-slot name="header"><a id="before" href="#">Before</a><h1>Title</h1></c-slot>
      <c-slot name="side">
        <c-mvp.page.side label="Contents" id="toc" :sticky="sticky" :position="position">
          <div id="toc-body" style="height: {{ panel_height }}px">Links</div>
        </c-mvp.page.side>
      </c-slot>
      <div id="content" style="{{ content_style }}"><div style="height: 3000px">Content</div></div>
    </c-mvp.page.layout>
  </c-mvp.page.content>
</c-mvp.page>
{% endblock %}
"""


def side_test_page(request):
    """Draw the test page; ``?sticky=0``, ``?fill=1``, ``?tall=1``, ``?position=start``."""
    get = request.GET
    template = engines["django"].from_string(CottonCompiler().process(PAGE))
    context = {
        "sticky": get.get("sticky", "1") == "1",
        "fill": get.get("fill") == "1",
        "position": get.get("position", "end"),
        "content_style": "flex: 1; min-height: 0; overflow: auto"
        if get.get("fill") == "1"
        else "",
        "panel_height": 2400 if get.get("tall") == "1" else 200,
    }
    return HttpResponse(template.render(context, request))


@pytest.fixture(autouse=True)
def side_test_urls(settings):
    settings.ROOT_URLCONF = urlconf_of(
        path("side-test/", side_test_page), *demo_urls.urlpatterns
    )


def open_page(page, live_server, query=""):
    page.set_viewport_size(VIEWPORT)
    page.goto(f"{live_server.url}/side-test/{query}")


def top(page, selector):
    return page.evaluate(
        f"() => document.querySelector('{selector}').getBoundingClientRect().top"
    )


def header_bottom(page):
    return page.evaluate(
        "() => document.querySelector('.mvp-header').getBoundingClientRect().bottom"
    )


def scroll_to(page, y):
    page.evaluate(f"() => window.scrollTo(0, {y})")


@pytest.mark.django_db(transaction=True)
class TestSideColumn:
    def test_a_sticky_panel_stays_directly_under_the_header(self, page, live_server):
        open_page(page, live_server)

        scroll_to(page, 1200)

        assert 0 <= top(page, "#toc") - header_bottom(page) <= 20

    def test_a_sticky_panel_stays_under_the_header_after_it_grows(
        self, page, live_server
    ):
        open_page(page, live_server)
        page.evaluate("""
            () => {
              const extra = document.createElement('div');
              extra.style.height = '120px';
              document.querySelector('.mvp-header').append(extra);
            }
        """)
        page.wait_for_function(
            """
            () => document.documentElement.style.getPropertyValue('--mvp-header-height')
              === document.querySelector('.mvp-header').offsetHeight + 'px'
            """
        )

        scroll_to(page, 1200)

        assert 0 <= top(page, "#toc") - header_bottom(page) <= 20

    def test_a_panel_that_does_not_stick_scrolls_away(self, page, live_server):
        open_page(page, live_server, "?sticky=0")

        scroll_to(page, 1200)

        assert top(page, "#toc") < header_bottom(page)

    def test_a_panel_taller_than_the_space_scrolls_on_its_own(self, page, live_server):
        open_page(page, live_server, "?tall=1&position=start")

        metrics = page.evaluate("""
            () => {
              const aside = document.getElementById('toc-panel');
              return {
                scrollHeight: aside.scrollHeight,
                clientHeight: aside.clientHeight,
                overflowY: getComputedStyle(aside).overflowY,
                viewport: window.innerHeight,
              };
            }
        """)
        assert metrics["overflowY"] == "auto"
        assert metrics["clientHeight"] < metrics["viewport"]
        assert metrics["scrollHeight"] > metrics["clientHeight"]

    def test_the_scrolling_aside_takes_focus_by_tab_and_scrolls_by_keyboard(
        self, page, live_server
    ):
        open_page(page, live_server, "?tall=1&position=start")

        page.focus("#before")
        page.keyboard.press("Tab")
        assert page.evaluate("() => document.activeElement.id") == "toc-panel"
        page.keyboard.press("PageDown")

        page.wait_for_function(
            "() => document.getElementById('toc-panel').scrollTop > 0"
        )

    def test_on_a_filled_page_the_panel_is_the_pages_height_and_does_not_stick(
        self, page, live_server
    ):
        open_page(page, live_server, "?fill=1&tall=1")

        sizes = page.evaluate("""
            () => {
              const box = sel => document.querySelector(sel).getBoundingClientRect();
              const aside = document.getElementById('toc-panel');
              return {
                panel: box('#toc').height,
                layout: box('.mvp-page-layout').height,
                position: getComputedStyle(document.getElementById('toc')).position,
                documentHeight: document.documentElement.scrollHeight,
                viewport: window.innerHeight,
                asideScrolls: aside.scrollHeight > aside.clientHeight,
              };
            }
        """)
        assert sizes["documentHeight"] <= sizes["viewport"] + 1
        assert sizes["position"] != "sticky"
        assert abs(sizes["panel"] - sizes["layout"]) <= 1
        assert sizes["asideScrolls"]

    def test_a_start_panel_is_on_the_right_in_a_right_to_left_page(
        self, page, live_server
    ):
        open_page(page, live_server, "?position=start")
        page.evaluate("() => { document.documentElement.dir = 'rtl'; }")

        assert page.evaluate("""
            () => document.getElementById('toc').getBoundingClientRect().left
              > document.getElementById('content').getBoundingClientRect().left
        """)


NARROW = {"width": 600, "height": 800}

DRAWER_PAGE = """
{% extends "mvp/base.html" %}
{% block content %}
<c-mvp.page>
  <c-mvp.page.content>
    <c-mvp.page.layout>
      <c-slot name="header">
        <h1>Title</h1>
        {% if button %}<c-mvp.page.side.toggle for="toc" text="Contents" />{% endif %}
      </c-slot>
      <c-slot name="side">
        <c-mvp.page.side label="Contents" id="toc" :collapse="side_collapse" :breakpoint="side_breakpoint" :position="side_position">
          <a id="first" href="#a">First</a>
          <a id="last" href="#b">Last</a>
        </c-mvp.page.side>
      </c-slot>
      <div id="content"><a id="after" href="#">After</a></div>
    </c-mvp.page.layout>
  </c-mvp.page.content>
</c-mvp.page>
{% endblock %}
"""


def side_drawer_page(request):
    """Draw the drawer page: ``?button=0``, ``?collapse=stack``, ``?breakpoint=lg|off``, ``?position=start``."""
    get = request.GET
    template = engines["django"].from_string(CottonCompiler().process(DRAWER_PAGE))
    context = {
        "button": get.get("button", "1") == "1",
        "side_collapse": get.get("collapse", "drawer"),
        "side_breakpoint": False
        if get.get("breakpoint") == "off"
        else get.get("breakpoint", "xl"),
        "side_position": get.get("position", "end"),
    }
    return HttpResponse(template.render(context, request))


def open_drawer_page(page, live_server, query="", viewport=NARROW):
    page.set_viewport_size(viewport)
    page.goto(f"{live_server.url}/side-drawer-test/{query}")
    page.wait_for_function("() => window.Alpine !== undefined")


def in_panel(page):
    """Whether focus is inside the panel."""
    return page.evaluate("() => document.activeElement.closest('#toc-panel') !== null")


def inert_ids(page):
    return page.evaluate(
        "() => [...document.querySelectorAll('[inert]')].map(e => e.id || e.tagName)"
    )


BUTTON = ".mvp-page-side-toggle"


@pytest.mark.django_db(transaction=True)
class TestSideDrawer:
    @pytest.fixture(autouse=True)
    def side_test_urls(self, settings):
        settings.ROOT_URLCONF = urlconf_of(
            path("side-drawer-test/", side_drawer_page), *demo_urls.urlpatterns
        )

    def open(self, page):
        page.click(BUTTON)
        page.wait_for_function(
            "() => document.activeElement.classList.contains('mvp-page-side-close')"
        )

    def test_below_the_breakpoint_the_panel_is_hidden_and_the_button_shown(
        self, page, live_server
    ):
        open_drawer_page(page, live_server)

        assert page.locator(BUTTON).is_visible()
        assert not page.locator("#toc-panel").is_visible()

    @pytest.mark.parametrize("position", ["end", "start"])
    def test_the_button_opens_the_panel_from_its_own_side(
        self, page, live_server, position
    ):
        open_drawer_page(page, live_server, f"?position={position}")

        self.open(page)

        box = page.locator("#toc-panel").bounding_box()
        centre = box["x"] + box["width"] / 2
        assert (centre > NARROW["width"] / 2) is (position == "end")

    def test_opening_dims_the_page_and_puts_everything_outside_the_panel_out_of_reach(
        self, page, live_server
    ):
        open_drawer_page(page, live_server)

        self.open(page)

        assert page.locator("#toc .drawer-overlay").is_visible()
        outside = page.evaluate("""
            () => ['content', 'first'].concat([...document.querySelectorAll('.mvp-page-side-toggle')].map((e, i) => (e.id = 'button' + i)))
              .map(id => document.getElementById(id).closest('[inert]') !== null)
        """)
        assert outside == [True, False, True]
        assert (
            page.evaluate(
                "() => document.querySelector('#toc .drawer-overlay').closest('[inert]')"
            )
            is None
        )

    def test_opening_moves_focus_into_the_panel_and_expands_the_button(
        self, page, live_server
    ):
        open_drawer_page(page, live_server)

        self.open(page)

        assert in_panel(page)
        assert page.get_attribute(BUTTON, "aria-expanded") == "true"

    @pytest.mark.parametrize("how", ["escape", "close button", "dimmed page"])
    def test_each_way_of_closing_returns_focus_to_the_button(
        self, page, live_server, how
    ):
        open_drawer_page(page, live_server)
        self.open(page)

        if how == "escape":
            page.keyboard.press("Escape")
        elif how == "close button":
            page.click("#toc .mvp-page-side-close")
        else:
            page.mouse.click(10, 400)

        page.wait_for_function(
            "() => document.activeElement.classList.contains('mvp-page-side-toggle')"
        )
        assert page.get_attribute(BUTTON, "aria-expanded") == "false"
        assert inert_ids(page) == []

    def test_tab_past_the_last_control_keeps_focus_inside_the_panel(
        self, page, live_server
    ):
        open_drawer_page(page, live_server)
        self.open(page)

        for _ in range(6):
            page.keyboard.press("Tab")
            assert in_panel(page)
        for _ in range(6):
            page.keyboard.press("Shift+Tab")
            assert in_panel(page)

    def test_at_the_breakpoint_the_button_is_hidden_and_the_panel_is_a_column(
        self, page, live_server
    ):
        open_drawer_page(page, live_server, viewport={"width": 1280, "height": 800})

        assert not page.locator(BUTTON).is_visible()
        assert page.locator("#toc-panel").is_visible()

    def test_a_drawer_with_no_button_is_not_shown_and_nothing_in_it_takes_focus(
        self, page, live_server
    ):
        open_drawer_page(page, live_server, "?button=0")

        assert not page.locator("#toc-panel").is_visible()
        for _ in range(8):
            page.keyboard.press("Tab")
            assert not in_panel(page)

    def test_a_stacked_panel_is_shown_with_no_button(self, page, live_server):
        open_drawer_page(page, live_server, "?collapse=stack")

        assert page.locator("#toc-panel").is_visible()
        assert not page.locator(BUTTON).is_visible()

    def test_with_no_breakpoint_a_wide_screen_still_has_a_drawer(
        self, page, live_server
    ):
        open_drawer_page(
            page,
            live_server,
            "?breakpoint=off",
            viewport={"width": 1440, "height": 900},
        )

        assert page.locator(BUTTON).is_visible()
        assert not page.locator("#toc-panel").is_visible()
        self.open(page)
        assert in_panel(page)

    def test_widening_past_the_breakpoint_closes_the_drawer_and_leaves_nothing_inert(
        self, page, live_server
    ):
        open_drawer_page(
            page, live_server, "?breakpoint=lg", viewport={"width": 900, "height": 800}
        )
        self.open(page)

        page.set_viewport_size({"width": 1100, "height": 800})

        page.wait_for_function(
            "() => document.querySelector('.mvp-page-side-toggle').getAttribute('aria-expanded') === 'false'"
        )
        assert inert_ids(page) == []
        assert not page.locator("#toc .drawer-toggle").is_checked()

    def test_removing_an_open_panel_releases_inert(self, page, live_server):
        open_drawer_page(page, live_server)
        self.open(page)
        assert inert_ids(page)

        page.evaluate("() => document.getElementById('toc').remove()")

        page.wait_for_function("() => document.querySelector('[inert]') === null")
