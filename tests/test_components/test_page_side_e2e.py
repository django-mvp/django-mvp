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
