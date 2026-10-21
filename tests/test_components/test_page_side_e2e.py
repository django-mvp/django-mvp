"""The side panel's column in a real browser (FS-042, FR-007, FR-011).

Whether a panel sticks under the header, moves with the page, takes focus or
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
SHORT = {"width": 1440, "height": 700}
NARROW_SCREEN = {"width": 600, "height": 700}
GAP = 16

PAGE = """
{% extends "mvp/base.html" %}
{% block content %}
<c-mvp.page :fill="fill">
  <c-mvp.page.content>
    <c-mvp.page.layout>
      <c-slot name="header"><a id="before" href="#">Before</a><h1>Title</h1></c-slot>
      <c-slot name="side">
        <c-mvp.page.side label="Contents" id="toc" :sticky="sticky" :position="position" :collapse="collapse">
          <div id="toc-body" style="height: {{ panel_height }}px; display: flex; flex-direction: column; justify-content: space-between">
            <a id="toc-first" href="#a">First</a>
            <a id="toc-last" href="#b">Last</a>
          </div>
          <a id="toc-spare" href="#c" style="position: absolute; left: 0; top: 0">Spare</a>
        </c-mvp.page.side>
      </c-slot>
      <div id="content" style="{{ content_style }}"><div style="height: 5000px">Content</div></div>
    </c-mvp.page.layout>
  </c-mvp.page.content>
</c-mvp.page>
{% endblock %}
"""


def side_test_page(request):
    """Draw the test page; ``?sticky=0``, ``?fill=1``, ``?tall=1``, ``?position=start``, ``?collapse=stack``."""
    get = request.GET
    template = engines["django"].from_string(CottonCompiler().process(PAGE))
    context = {
        "sticky": get.get("sticky", "1") == "1",
        "fill": get.get("fill") == "1",
        "position": get.get("position", "end"),
        "collapse": get.get("collapse", "drawer"),
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


def open_page(page, live_server, query="", viewport=VIEWPORT):
    page.set_default_timeout(5000)
    page.set_viewport_size(viewport)
    page.goto(f"{live_server.url}/side-test/{query}")


def top(page, selector):
    return page.evaluate(
        f"() => document.querySelector('{selector}').getBoundingClientRect().top"
    )


def header_bottom(page):
    return page.evaluate(
        "() => document.querySelector('.mvp-header').getBoundingClientRect().bottom"
    )


def frames(page, count=2):
    """Wait for ``count`` animation frames, which is when the panel catches up with a scroll."""
    page.evaluate(
        """
        count => new Promise(done => {
          const tick = left => (left ? requestAnimationFrame(() => tick(left - 1)) : done());
          tick(count);
        })
        """,
        count,
    )


def scroll_to(page, y):
    page.evaluate(f"() => window.scrollTo(0, {y})")
    frames(page)


def scroll_by(page, dy):
    page.evaluate(f"() => window.scrollBy(0, {dy})")
    frames(page)


def bottom(page, selector):
    return page.evaluate(
        f"() => document.querySelector('{selector}').getBoundingClientRect().bottom"
    )


def side_top(page):
    """The panel's published offset, or ``""`` while it holds none."""
    return page.evaluate(
        "() => document.getElementById('toc').style.getPropertyValue('--mvp-page-side-top')"
    )


def wait_for_column(page):
    """Wait until a tall panel's component has taken hold of it."""
    page.wait_for_function(
        "() => document.getElementById('toc').style.getPropertyValue('--mvp-page-side-top') !== ''"
    )


def place(page, selector, viewport_top):
    """Put an absolutely positioned control's top edge ``viewport_top`` px below the screen's top."""
    page.evaluate(
        """
        ([selector, viewportTop]) => {
          const control = document.querySelector(selector);
          const root = document.getElementById('toc');
          control.style.top = (viewportTop - root.getBoundingClientRect().top) + 'px';
        }
        """,
        [selector, viewport_top],
    )


def open_tall_page(page, live_server, query=""):
    open_page(page, live_server, f"?tall=1{query}", SHORT)
    wait_for_column(page)


def hold_at_the_foot(page):
    """Scroll a tall panel's whole range at once, so its foot is the end in view."""
    scroll_to(page, 2600)


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

    def test_on_a_filled_page_the_aside_takes_focus_by_tab_and_scrolls_by_keyboard(
        self, page, live_server
    ):
        open_page(page, live_server, "?fill=1&tall=1&position=start")

        page.focus("#before")
        page.keyboard.press("Tab")
        assert page.evaluate("() => document.activeElement.id") == "toc-panel"
        page.keyboard.press("PageDown")

        page.wait_for_function(
            "() => document.getElementById('toc-panel').scrollTop > 0"
        )

    def test_on_a_filled_page_the_panel_holds_no_offset(self, page, live_server):
        open_page(page, live_server, "?fill=1&tall=1", SHORT)
        page.wait_for_function("() => window.Alpine !== undefined")
        scroll_by(page, 300)

        assert side_top(page) == ""

    def test_a_start_panel_is_on_the_right_in_a_right_to_left_page(
        self, page, live_server
    ):
        open_page(page, live_server, "?position=start")
        page.evaluate("() => { document.documentElement.dir = 'rtl'; }")

        assert page.evaluate("""
            () => document.getElementById('toc').getBoundingClientRect().left
              > document.getElementById('content').getBoundingClientRect().left
        """)


@pytest.mark.django_db(transaction=True)
class TestTallSideColumn:
    """A sticky panel taller than the space moves with the page until an end is in view (FS-042 FR-007)."""

    def test_the_aside_has_no_scrollbar_of_its_own(self, page, live_server):
        open_tall_page(page, live_server)

        metrics = page.evaluate("""
            () => {
              const aside = document.getElementById('toc-panel');
              return {
                scrollHeight: aside.scrollHeight,
                clientHeight: aside.clientHeight,
                height: aside.getBoundingClientRect().height,
                viewport: window.innerHeight,
              };
            }
        """)
        assert metrics["height"] > metrics["viewport"]
        assert metrics["scrollHeight"] <= metrics["clientHeight"]

    def test_scrolling_down_brings_the_foot_into_view_and_holds_it_there(
        self, page, live_server
    ):
        open_tall_page(page, live_server)

        hold_at_the_foot(page)
        assert bottom(page, "#toc-panel") == pytest.approx(SHORT["height"] - GAP, abs=2)

        scroll_by(page, 400)
        assert bottom(page, "#toc-panel") == pytest.approx(SHORT["height"] - GAP, abs=2)

    def test_a_stacked_panel_moves_with_the_page_in_the_same_way(
        self, page, live_server
    ):
        open_tall_page(page, live_server, "&collapse=stack")

        hold_at_the_foot(page)

        assert bottom(page, "#toc-panel") == pytest.approx(SHORT["height"] - GAP, abs=2)

    def test_the_panel_follows_the_page_down_until_its_foot_is_in_view(
        self, page, live_server
    ):
        open_tall_page(page, live_server)
        before = top(page, "#toc")

        scroll_by(page, 300)
        scroll_by(page, 300)

        assert top(page, "#toc") == pytest.approx(before - 600, abs=2)

    def test_scrolling_up_from_the_foot_moves_the_panel_down_with_the_page(
        self, page, live_server
    ):
        open_tall_page(page, live_server)
        hold_at_the_foot(page)
        held = top(page, "#toc")

        scroll_by(page, -150)

        assert top(page, "#toc") == pytest.approx(held + 150, abs=2)

    def test_scrolling_up_further_holds_the_top_under_the_header(
        self, page, live_server
    ):
        open_tall_page(page, live_server)
        hold_at_the_foot(page)

        scroll_by(page, -2000)
        assert top(page, "#toc") == pytest.approx(header_bottom(page) + GAP, abs=2)

        scroll_by(page, -100)
        assert top(page, "#toc") == pytest.approx(header_bottom(page) + GAP, abs=2)

    def test_a_panel_that_fits_sits_under_the_header_and_holds_no_offset(
        self, page, live_server
    ):
        open_page(page, live_server, "", SHORT)
        page.wait_for_function(
            "() => document.getElementById('toc-panel')._x_dataStack"
        )

        scroll_to(page, 1200)

        assert top(page, "#toc") == pytest.approx(header_bottom(page) + GAP, abs=2)
        assert side_top(page) == ""

    def test_a_panel_that_grows_taller_than_the_space_starts_moving_with_the_page(
        self, page, live_server
    ):
        open_page(page, live_server, "", SHORT)
        page.wait_for_function(
            "() => document.getElementById('toc-panel')._x_dataStack"
        )
        assert side_top(page) == ""

        page.evaluate(
            "() => { document.getElementById('toc-body').style.height = '2400px'; }"
        )
        wait_for_column(page)
        hold_at_the_foot(page)

        assert bottom(page, "#toc-panel") == pytest.approx(SHORT["height"] - GAP, abs=2)

        page.evaluate(
            "() => { document.getElementById('toc-body').style.height = '200px'; }"
        )
        page.wait_for_function(
            "() => document.getElementById('toc').style.getPropertyValue('--mvp-page-side-top') === ''"
        )
        assert top(page, "#toc") == pytest.approx(header_bottom(page) + GAP, abs=2)

    def test_a_taller_header_moves_a_panel_held_at_the_top_down_with_it(
        self, page, live_server
    ):
        open_tall_page(page, live_server)
        hold_at_the_foot(page)
        scroll_by(page, -2000)

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
        frames(page)

        assert top(page, "#toc") == pytest.approx(header_bottom(page) + GAP, abs=2)

    def test_a_reload_part_way_down_places_the_panel_and_follows_the_next_scroll(
        self, page, live_server
    ):
        open_tall_page(page, live_server)
        scroll_to(page, 1200)

        page.reload()
        wait_for_column(page)
        placed = top(page, "#toc")
        assert header_bottom(page) <= placed <= header_bottom(page) + GAP + 2
        assert bottom(page, "#toc-panel") >= SHORT["height"] - GAP - 2

        scroll_by(page, 100)

        assert top(page, "#toc") == pytest.approx(placed - 100, abs=2)

    def test_the_offset_is_released_below_the_breakpoint_and_taken_again_above_it(
        self, page, live_server
    ):
        open_tall_page(page, live_server)

        page.set_viewport_size(NARROW_SCREEN)
        page.wait_for_function(
            "() => document.getElementById('toc').style.getPropertyValue('--mvp-page-side-top') === ''"
        )

        page.set_viewport_size(SHORT)
        wait_for_column(page)

    def test_a_replacement_of_the_panel_keeps_its_place(self, page, live_server):
        open_tall_page(page, live_server)
        hold_at_the_foot(page)
        scroll_by(page, -150)
        held = top(page, "#toc")

        page.evaluate("""
            () => {
              const panel = document.getElementById('toc');
              const copy = panel.cloneNode(true);
              copy.removeAttribute('style');
              panel.replaceWith(copy);
            }
        """)
        wait_for_column(page)
        frames(page)

        assert top(page, "#toc") == pytest.approx(held, abs=2)

    def test_a_removed_panel_gives_back_every_listener_and_observer(
        self, page, live_server
    ):
        page.add_init_script("""
            window.__live = { scroll: 0, resize: 0, observers: 0 };
            const add = window.addEventListener.bind(window);
            const remove = window.removeEventListener.bind(window);
            window.addEventListener = (type, ...rest) => {
              if (type in window.__live) window.__live[type] += 1;
              add(type, ...rest);
            };
            window.removeEventListener = (type, ...rest) => {
              if (type in window.__live) window.__live[type] -= 1;
              remove(type, ...rest);
            };
            for (const Observer of [ResizeObserver, MutationObserver]) {
              const observe = Observer.prototype.observe;
              const disconnect = Observer.prototype.disconnect;
              Observer.prototype.observe = function (...args) {
                if (!this.__watching) { this.__watching = true; window.__live.observers += 1; }
                return observe.apply(this, args);
              };
              Observer.prototype.disconnect = function () {
                if (this.__watching) { this.__watching = false; window.__live.observers -= 1; }
                return disconnect.call(this);
              };
            }
        """)
        open_tall_page(page, live_server)
        errors = []
        page.on("pageerror", lambda error: errors.append(error))
        before = page.evaluate("() => ({ ...window.__live })")

        page.evaluate("() => document.getElementById('toc').remove()")
        page.wait_for_function(
            "before => window.__live.scroll < before.scroll", arg=before
        )
        scroll_by(page, 100)

        after = page.evaluate("() => ({ ...window.__live })")
        assert after["resize"] < before["resize"]
        assert after["observers"] < before["observers"]
        assert errors == []

    def test_the_aside_is_a_tab_stop_only_where_it_scrolls(self, page, live_server):
        open_tall_page(page, live_server)

        page.focus("#before")
        page.keyboard.press("Tab")

        assert page.evaluate("() => document.activeElement.id") == "toc-first"

        page.set_viewport_size(NARROW_SCREEN)
        page.wait_for_function(
            "() => document.getElementById('toc-panel').getAttribute('tabindex') === '0'"
        )


@pytest.mark.django_db(transaction=True)
class TestTallSideColumnFocus:
    """A control reached by keyboard ends up clear of the header and of the screen's foot."""

    def test_tabbing_back_to_the_first_control_of_a_panel_held_at_its_foot_shows_it(
        self, page, live_server
    ):
        open_tall_page(page, live_server)
        hold_at_the_foot(page)
        assert top(page, "#toc-first") < 0

        page.focus("#toc-last")
        page.keyboard.press("Shift+Tab")
        frames(page)

        assert page.evaluate("() => document.activeElement.id") == "toc-first"
        assert top(page, "#toc-first") >= header_bottom(page) + GAP - 2
        assert bottom(page, "#toc-first") <= SHORT["height"]

    def test_tabbing_to_the_last_control_of_a_panel_held_at_its_top_shows_it(
        self, page, live_server
    ):
        open_tall_page(page, live_server)
        assert bottom(page, "#toc-last") > SHORT["height"]

        page.focus("#toc-first")
        page.keyboard.press("Tab")
        frames(page)

        assert page.evaluate("() => document.activeElement.id") == "toc-last"
        assert bottom(page, "#toc-last") <= SHORT["height"] - GAP + 2
        assert top(page, "#toc-last") >= header_bottom(page)

    def test_a_control_in_view_but_inside_the_gap_at_the_foot_is_moved_clear_of_it(
        self, page, live_server
    ):
        open_tall_page(page, live_server)
        place(page, "#toc-spare", SHORT["height"] - 10)

        page.focus("#toc-spare")
        frames(page)

        assert bottom(page, "#toc-spare") <= SHORT["height"] - GAP + 2

    def test_a_control_in_view_but_inside_the_gap_under_the_header_is_moved_clear_of_it(
        self, page, live_server
    ):
        open_tall_page(page, live_server)
        hold_at_the_foot(page)
        place(page, "#toc-spare", header_bottom(page) + 6)

        page.focus("#toc-spare")
        frames(page)

        assert top(page, "#toc-spare") >= header_bottom(page) + GAP - 2


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
          <a id="jump" href="#target">Jump</a>
          <a id="last" href="#b">Last</a>
          {% if untabbable_tail %}
          <input type="hidden" name="kept" value="1">
          <details><summary tabindex="-1">More</summary><a href="#c">Folded</a></details>
          {% endif %}
        </c-mvp.page.side>
      </c-slot>
      <div id="content">
        <a id="after" href="#">After</a>
        {% if long %}
        <div style="height: 2000px"></div>
        <h2 id="target">Target</h2>
        <div style="height: 2000px"></div>
        {% endif %}
      </div>
    </c-mvp.page.layout>
  </c-mvp.page.content>
</c-mvp.page>
{% endblock %}
"""


def side_drawer_page(request):
    """Draw the drawer page: ``?button=0``, ``?collapse=stack``, ``?breakpoint=lg|off``,
    ``?position=start``, ``?long=1`` for a heading far down the content."""
    get = request.GET
    template = engines["django"].from_string(CottonCompiler().process(DRAWER_PAGE))
    context = {
        "button": get.get("button", "1") == "1",
        "side_collapse": get.get("collapse", "drawer"),
        "side_breakpoint": False
        if get.get("breakpoint") == "off"
        else get.get("breakpoint", "xl"),
        "side_position": get.get("position", "end"),
        "untabbable_tail": get.get("tail") == "1",
        "long": get.get("long") == "1",
    }
    return HttpResponse(template.render(context, request))


def open_drawer_page(page, live_server, query="", viewport=NARROW):
    page.set_default_timeout(5000)
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

    def test_following_a_link_to_a_place_on_the_page_closes_the_panel(
        self, page, live_server
    ):
        open_drawer_page(page, live_server, "?long=1")
        self.open(page)

        page.click("#jump")

        page.wait_for_function(
            "() => document.querySelector('.mvp-page-side-toggle').getAttribute('aria-expanded') === 'false'"
        )
        frames(page)
        assert not page.locator("#toc .drawer-toggle").is_checked()
        assert inert_ids(page) == []
        page.locator("#toc .drawer-overlay").wait_for(state="hidden")
        assert header_bottom(page) - 1 <= top(page, "#target") < NARROW["height"]

    def test_following_a_link_to_a_place_on_the_page_moves_focus_to_that_place(
        self, page, live_server
    ):
        open_drawer_page(page, live_server, "?long=1")
        self.open(page)

        page.click("#jump")

        page.wait_for_function("() => document.activeElement.id === 'target'")

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

    def test_tab_from_the_last_control_wraps_when_the_panel_ends_in_something_untabbable(
        self, page, live_server
    ):
        open_drawer_page(page, live_server, "?tail=1")
        self.open(page)
        page.focus("#last")

        page.keyboard.press("Tab")

        assert page.evaluate("() => document.activeElement.id") == "toc-panel"

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


@pytest.mark.django_db(transaction=True)
class TestSideDrawerSlide:
    """The drawer slides in from the side it sits on, at either end (FS-042 US2)."""

    @pytest.fixture(autouse=True)
    def side_test_urls(self, settings):
        settings.ROOT_URLCONF = urlconf_of(
            path("side-drawer-test/", side_drawer_page), *demo_urls.urlpatterns
        )

    @staticmethod
    def edges(page):
        return page.evaluate(
            """() => {
                const box = document.getElementById('toc-panel').getBoundingClientRect();
                return { left: box.left, right: box.right, width: window.innerWidth };
            }"""
        )

    @pytest.mark.parametrize("direction", ["ltr", "rtl"])
    def test_an_end_panel_slides_in_from_the_end_edge(
        self, page, live_server, direction
    ):
        open_drawer_page(page, live_server, "?position=end")
        page.evaluate(f"() => {{ document.documentElement.dir = '{direction}'; }}")
        page.wait_for_timeout(500)
        closed = self.edges(page)
        # The end is the right edge of a left-to-right page and the left edge of the other.
        sign = 1 if direction == "ltr" else -1
        away = (
            (lambda e: e["left"] - e["width"]) if sign == 1 else (lambda e: -e["right"])
        )
        assert away(closed) >= -1

        page.click(BUTTON)
        page.wait_for_timeout(200)
        moving = self.edges(page)
        page.wait_for_timeout(600)
        opened = self.edges(page)

        assert away(opened) < away(moving) < away(closed)
        flush = opened["right"] if sign == 1 else opened["left"]
        assert flush == pytest.approx(opened["width"] if sign == 1 else 0, abs=1)
