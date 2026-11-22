"""The sheet in a real browser (FS-047).

Placement, focus, scrolling and the keyboard offset are computed, so only a
browser settles them. Wording, widths and spacing are ruled by eye and not
tested. Each case loads a test-only page, ``/sheet-test/``, that carries no
inline script or style.

Source: assets/js/sheet.js, mvp/templates/cotton/mvp/sheet/
"""

import pytest
from django.http import HttpResponse
from django.template import engines
from django.urls import path
from django_cotton.compiler_regex import CottonCompiler
from playwright.sync_api import expect

from demo import urls as demo_urls
from mvp.config import MVP_CONFIG
from tests.conftest import requires_browser, urlconf_of

pytestmark = [pytest.mark.e2e, requires_browser]

PHONE = {"width": 390, "height": 844}
DESKTOP = {"width": 1280, "height": 800}
SHORT = {"width": 1280, "height": 420}
JUST_NARROW = {"width": 639, "height": 800}
JUST_WIDE = {"width": 640, "height": 800}
BOTH_WIDTHS = pytest.mark.parametrize(
    "viewport", [PHONE, DESKTOP], ids=["phone", "desktop"]
)

PAGE = """
{% extends "mvp/base.html" %}
{% block content %}
<a id="before" href="/before-page/">Before</a>
<form id="form" method="post" action="/posted/">
  <button type="submit" id="submit">Send</button>
  <c-mvp.sheet.trigger for="orders" id="open-orders" href="/orders-page/" label="Orders" />
  <c-mvp.sheet id="orders" title="Orders" lead="Three open">
    <c-mvp.sheet.view name="menu">
      <c-mvp.sheet.menu>
        <c-mvp.sheet.menu.item text="Rename" icon="edit" @click="show('rename')" />
        <c-mvp.sheet.menu.item text="Delete" icon="trash" danger @click="show('confirm')" />
      </c-mvp.sheet.menu>
    </c-mvp.sheet.view>
    <c-mvp.sheet.view name="rename">
      <input id="rename-field" type="text" name="name" aria-label="Name">
      <button type="button" id="rename-back" @click="show('menu')">Back</button>
    </c-mvp.sheet.view>
    <c-mvp.sheet.view name="confirm">
      <button type="button" id="confirm-back" @click="show('menu')">Back</button>
      <c-mvp.sheet.trigger for="other" id="open-other" returns="before">Other</c-mvp.sheet.trigger>
      <c-mvp.sheet.trigger for="other" id="open-other-plain">Plain</c-mvp.sheet.trigger>
    </c-mvp.sheet.view>
  </c-mvp.sheet>
</form>
<c-mvp.sheet id="other" title="Other"><p>Elsewhere</p></c-mvp.sheet>
<c-mvp.sheet id="typing" title="Typing" fixed>
  <c-mvp.sheet.view name="fill">
    {% for row in rows %}<p>Line {{ row }}</p>{% endfor %}
    <input id="typing-field" type="text" aria-label="Note">
  </c-mvp.sheet.view>
</c-mvp.sheet>
<c-mvp.sheet id="tall" title="Tall">
  {% for row in rows %}<p>Row {{ row }}</p>{% endfor %}
</c-mvp.sheet>
<c-mvp.sheet.trigger for="missing" id="orphan" href="/missing-page/" label="Gone" />
<c-mvp.sheet.trigger for="before" id="not-a-sheet" href="/not-a-sheet-page/" label="Link" />
<button type="button" id="open-tall" x-data @click="$dispatch('mvp-sheet-open', { id: 'tall' })">Tall</button>
<button type="button" id="open-typing" x-data @click="$dispatch('mvp-sheet-open', { id: 'typing' })">Typing</button>
{% for row in filler %}<p>Page {{ row }}</p>{% endfor %}
{% endblock %}
"""


def sheet_test_page(request):
    """Draw the test page."""
    template = engines["django"].from_string(CottonCompiler().process(PAGE))
    context = {"rows": range(60), "filler": range(120)}
    return HttpResponse(template.render(context, request))


def landing_page(request):
    """Stand in for every address the page links or posts to."""
    return HttpResponse(f"<p id='landed'>{request.method} {request.path}</p>")


@pytest.fixture(autouse=True)
def sheet_test_urls(settings):
    settings.ROOT_URLCONF = urlconf_of(
        path("sheet-test/", sheet_test_page),
        path("orders-page/", landing_page),
        path("posted/", landing_page),
        path("missing-page/", landing_page),
        path("not-a-sheet-page/", landing_page),
        *demo_urls.urlpatterns,
    )


def open_page(page, live_server, viewport=PHONE):
    page.set_default_timeout(5000)
    page.set_viewport_size(viewport)
    page.goto(f"{live_server.url}/sheet-test/")
    page.wait_for_function("() => window.Alpine && Alpine.version")


def settle(page):
    """Wait for the open or close slide, a CSS transition, to finish."""
    page.evaluate(
        "() => Promise.all(document.getAnimations()"
        ".filter(a => a instanceof CSSTransition).map(a => a.finished))"
    )


def dispatch(page, **detail):
    page.evaluate(
        "detail => window.dispatchEvent(new CustomEvent('mvp-sheet-open', { detail }))",
        detail,
    )


def open_sheets(page):
    return page.evaluate(
        "() => [...document.querySelectorAll('dialog[data-mvp-sheet][open]')]"
        ".map(el => el.id)"
    )


def focus_is_inside(page, selector):
    return page.evaluate(
        "selector => document.querySelector(selector).contains(document.activeElement)",
        selector,
    )


def focus_is_behind(page, selector):
    """Whether focus is on the page behind the dialog, not in it or on the browser."""
    return page.evaluate(
        "selector => document.activeElement !== document.body"
        " && !document.querySelector(selector).contains(document.activeElement)",
        selector,
    )


def active_id(page):
    return page.evaluate("() => document.activeElement.id")


def shown_views(page, sheet="orders"):
    """The views showing, once Alpine has caught up with the last click."""
    page.evaluate("() => new Promise(done => requestAnimationFrame(() => done()))")
    return page.evaluate(
        "sheet => [...document.querySelectorAll("
        "`#${sheet} [data-mvp-sheet-view]`)]"
        ".filter(el => el.checkVisibility()).map(el => el.dataset.mvpSheetView)",
        sheet,
    )


def box_of(page, sheet):
    settle(page)
    return page.evaluate(
        "sheet => { const r = document.querySelector(`#${sheet} .mvp-sheet-box`)"
        ".getBoundingClientRect();"
        " return { top: r.top, bottom: r.bottom, height: r.height,"
        " viewport: window.innerHeight }; }",
        sheet,
    )


class TestOpening:
    @BOTH_WIDTHS
    def test_the_trigger_opens_the_sheet_and_focus_moves_into_it(
        self, page, live_server, viewport
    ):
        open_page(page, live_server, viewport)

        page.click("#open-orders")

        assert open_sheets(page) == ["orders"]
        assert focus_is_inside(page, "#orders")
        assert shown_views(page) == ["menu"]

    def test_a_narrow_screen_anchors_the_sheet_to_the_bottom_with_its_grab_bar(
        self, page, live_server
    ):
        open_page(page, live_server, PHONE)

        page.click("#open-orders")

        box = box_of(page, "orders")
        assert box["bottom"] == pytest.approx(box["viewport"], abs=2)
        expect(page.locator("#orders [data-mvp-sheet-grab]")).to_be_visible()

    def test_a_wide_screen_centres_the_sheet_without_a_grab_bar(
        self, page, live_server
    ):
        open_page(page, live_server, DESKTOP)

        page.click("#open-orders")

        box = box_of(page, "orders")
        centre = (box["top"] + box["bottom"]) / 2
        assert centre == pytest.approx(box["viewport"] / 2, abs=2)
        expect(page.locator("#orders [data-mvp-sheet-grab]")).to_be_hidden()

    @pytest.mark.parametrize(
        ("viewport", "centred"), [(JUST_NARROW, False), (JUST_WIDE, True)]
    )
    def test_the_switch_between_narrow_and_wide_is_at_640_pixels(
        self, page, live_server, viewport, centred
    ):
        open_page(page, live_server, viewport)

        page.click("#open-orders")

        box = box_of(page, "orders")
        assert (box["bottom"] < box["viewport"] - 2) is centred
        grab = page.locator("#orders [data-mvp-sheet-grab]")
        expect(grab).to_be_hidden() if centred else expect(grab).to_be_visible()

    def test_a_view_that_does_not_exist_opens_the_first_view(self, page, live_server):
        open_page(page, live_server)

        dispatch(page, id="orders", view="nowhere")

        assert open_sheets(page) == ["orders"]
        assert shown_views(page) == ["menu"]

    def test_a_named_view_opens_at_that_view(self, page, live_server):
        open_page(page, live_server)

        dispatch(page, id="orders", view="confirm")

        assert shown_views(page) == ["confirm"]

    def test_a_trigger_whose_sheet_is_absent_follows_its_link(self, page, live_server):
        open_page(page, live_server)

        page.click("#orphan")

        page.wait_for_url("**/missing-page/")
        assert open_sheets(page) == []

    def test_a_trigger_naming_an_element_that_is_not_a_sheet_follows_its_link(
        self, page, live_server
    ):
        open_page(page, live_server)

        page.click("#not-a-sheet")

        page.wait_for_url("**/not-a-sheet-page/")

    def test_two_sheets_open_and_close_each_on_its_own(self, page, live_server):
        open_page(page, live_server)

        dispatch(page, id="tall")
        assert open_sheets(page) == ["tall"]
        page.keyboard.press("Escape")
        assert open_sheets(page) == []
        dispatch(page, id="other")
        assert open_sheets(page) == ["other"]
        page.keyboard.press("Escape")
        assert open_sheets(page) == []

    def test_opening_a_different_sheet_closes_the_open_one(self, page, live_server):
        open_page(page, live_server)
        page.click("#open-orders")

        dispatch(page, id="other")

        assert open_sheets(page) == ["other"]

    def test_a_trigger_inside_a_sheet_opens_a_second_and_closes_the_first(
        self, page, live_server
    ):
        open_page(page, live_server)
        page.click("#open-orders")
        dispatch(page, id="orders", view="confirm")

        page.click("#open-other-plain")

        assert open_sheets(page) == ["other"]


class TestFocusReturn:
    def test_focus_goes_to_the_element_the_second_sheet_names(self, page, live_server):
        open_page(page, live_server)
        page.click("#open-orders")
        dispatch(page, id="orders", view="confirm")
        page.click("#open-other")

        page.keyboard.press("Escape")

        assert active_id(page) == "before"

    def test_a_trigger_in_the_closed_sheet_sends_focus_to_the_first_trigger(
        self, page, live_server
    ):
        open_page(page, live_server)
        page.click("#open-orders")
        dispatch(page, id="orders", view="confirm")
        page.click("#open-other-plain")

        page.keyboard.press("Escape")

        assert active_id(page) == "open-orders"


class TestViews:
    def test_a_view_switches_to_another_and_back_while_the_sheet_stays_open(
        self, page, live_server
    ):
        open_page(page, live_server)
        page.click("#open-orders")

        page.get_by_role("button", name="Delete").click()
        assert shown_views(page) == ["confirm"]
        page.click("#confirm-back")

        assert shown_views(page) == ["menu"]
        assert open_sheets(page) == ["orders"]

    def test_reopening_a_closed_sheet_shows_its_first_view(self, page, live_server):
        open_page(page, live_server)
        page.click("#open-orders")
        page.get_by_role("button", name="Rename").click()
        assert shown_views(page) == ["rename"]
        page.keyboard.press("Escape")

        page.click("#open-orders")

        assert shown_views(page) == ["menu"]


class TestClosing:
    @BOTH_WIDTHS
    @pytest.mark.parametrize("way", ["escape", "outside", "button"])
    def test_every_way_of_closing_returns_focus_and_submits_nothing(
        self, page, live_server, viewport, way
    ):
        open_page(page, live_server, viewport)
        posts = []
        page.on(
            "request",
            lambda request: (
                posts.append(request.url) if request.method == "POST" else None
            ),
        )
        page.click("#open-orders")

        if way == "escape":
            page.keyboard.press("Escape")
        elif way == "outside":
            page.mouse.click(5, 5)
        else:
            page.locator("#orders .mvp-sheet-foot button").click()

        assert open_sheets(page) == []
        assert active_id(page) == "open-orders"
        page.wait_for_timeout(200)
        assert posts == []
        assert "/sheet-test/" in page.url

    def test_a_keyboard_alone_opens_switches_views_closes_and_reopens(
        self, page, live_server
    ):
        open_page(page, live_server)
        page.focus("#before")
        page.keyboard.press("Tab")
        page.keyboard.press("Tab")
        assert active_id(page) == "open-orders"
        page.keyboard.press("Enter")
        assert open_sheets(page) == ["orders"]
        settle(page)

        page.get_by_role("button", name="Delete").focus()
        page.keyboard.press("Enter")
        assert shown_views(page) == ["confirm"]
        page.focus("#confirm-back")
        page.keyboard.press("Enter")
        assert shown_views(page) == ["menu"]
        assert open_sheets(page) == ["orders"]

        page.keyboard.press("Escape")
        assert open_sheets(page) == []
        assert active_id(page) == "open-orders"
        page.keyboard.press("Enter")
        assert open_sheets(page) == ["orders"]
        assert shown_views(page) == ["menu"]


class TestFocusStaysInside:
    @BOTH_WIDTHS
    def test_tab_never_reaches_the_page_behind(self, page, live_server, viewport):
        open_page(page, live_server, viewport)
        page.click("#open-orders")

        for _ in range(12):
            page.keyboard.press("Tab")
            assert not focus_is_behind(page, "#orders")
        for _ in range(12):
            page.keyboard.press("Shift+Tab")
            assert not focus_is_behind(page, "#orders")


class TestScrolling:
    @BOTH_WIDTHS
    def test_a_tall_body_scrolls_with_the_head_kept_and_the_page_still(
        self, page, live_server, viewport
    ):
        open_page(page, live_server, {**viewport, "height": 420})
        page.click("#open-tall")
        settle(page)
        head = page.locator("#tall [data-mvp-sheet-head]")
        body = page.locator("#tall [data-mvp-sheet-body]")
        head_top = head.evaluate("el => el.getBoundingClientRect().top")
        assert body.evaluate("el => el.scrollHeight > el.clientHeight")

        body.hover()
        page.mouse.wheel(0, 600)
        page.wait_for_function(
            "() => document.querySelector('#tall [data-mvp-sheet-body]').scrollTop > 0"
        )
        page.mouse.wheel(0, 100000)
        page.wait_for_timeout(200)

        assert head.evaluate("el => el.getBoundingClientRect().top") == head_top
        expect(head).to_be_in_viewport()
        assert page.evaluate("() => window.scrollY") == 0


class TestNothingFromElsewhere:
    def test_a_page_with_a_sheet_requests_nothing_from_another_origin(
        self, page, live_server, monkeypatch
    ):
        # The icon font is the project's own choice and the demo's is a CDN's;
        # the sheet draws icons by name and adds no request of its own.
        monkeypatch.setitem(MVP_CONFIG, "icon_stylesheet", "")
        foreign = []
        page.on(
            "request",
            lambda request: (
                foreign.append(request.url)
                if not request.url.startswith((live_server.url, "data:", "blob:"))
                else None
            ),
        )

        open_page(page, live_server)
        page.click("#open-orders")
        page.wait_for_load_state("networkidle")

        assert foreign == []


class TestWithScriptsOff:
    def test_a_trigger_with_an_address_follows_its_link(self, browser, live_server):
        context = browser.new_context(java_script_enabled=False)
        page = context.new_page()
        page.set_default_timeout(5000)

        page.goto(f"{live_server.url}/sheet-test/")
        page.click("#open-orders")

        page.wait_for_url("**/orders-page/")
        context.close()


class TestKeyboardOffset:
    """No automated browser draws an on-screen keyboard, so these cases fake one.

    They redefine ``window.visualViewport``'s height and offset to what a
    keyboard leaves and fire ``resize`` on it, which is what a phone does.
    """

    KEYBOARD = 300

    def fake_keyboard(self, page, height):
        page.evaluate(
            """
            height => {
              const viewport = window.visualViewport;
              Object.defineProperty(viewport, "height", {
                configurable: true, get: () => height });
              Object.defineProperty(viewport, "offsetTop", {
                configurable: true, get: () => 0 });
              viewport.dispatchEvent(new Event("resize"));
            }
            """,
            height,
        )

    def field_bottom(self, page):
        return page.evaluate(
            "() => document.getElementById('typing-field')"
            ".getBoundingClientRect().bottom"
        )

    def test_a_field_below_the_faked_keyboard_line_is_lifted_above_it(
        self, page, live_server
    ):
        open_page(page, live_server, PHONE)
        page.click("#open-typing")
        field = page.locator("#typing-field")
        field.scroll_into_view_if_needed()
        line = PHONE["height"] - self.KEYBOARD
        assert self.field_bottom(page) > line

        field.focus()
        self.fake_keyboard(page, line)

        page.wait_for_function(
            "line => document.getElementById('typing-field')"
            ".getBoundingClientRect().bottom <= line",
            arg=line,
        )
        box = box_of(page, "typing")
        assert box["bottom"] <= line + 1

    def test_closing_the_sheet_takes_the_offset_away(self, page, live_server):
        open_page(page, live_server, PHONE)
        page.click("#open-typing")
        self.fake_keyboard(page, PHONE["height"] - self.KEYBOARD)
        offset = "() => document.getElementById('typing').style.getPropertyValue"
        assert page.evaluate(offset + "('--mvp-sheet-keyboard')") != ""

        page.keyboard.press("Escape")

        assert page.evaluate(offset + "('--mvp-sheet-keyboard')") == ""

    def test_a_sheet_that_is_not_open_does_not_listen(self, page, live_server):
        open_page(page, live_server, PHONE)
        page.click("#open-typing")

        self.fake_keyboard(page, PHONE["height"] - self.KEYBOARD)

        untouched = page.evaluate(
            "() => document.getElementById('tall').style"
            ".getPropertyValue('--mvp-sheet-keyboard')"
        )
        assert untouched == ""


class TestReducedMotion:
    def durations(self, page):
        return page.evaluate(
            """
            () => ["#orders", "#orders .mvp-sheet-box"].flatMap(selector => {
              const style = getComputedStyle(document.querySelector(selector));
              return [style.transitionDuration, style.animationDuration]
                .flatMap(value => value.split(", "));
            })
            """
        )

    def test_the_sheet_slides_by_default(self, page, live_server):
        open_page(page, live_server)
        page.click("#open-orders")

        assert set(self.durations(page)) != {"0s"}

    def test_reduced_motion_removes_the_slide(self, page, live_server):
        page.emulate_media(reduced_motion="reduce")
        open_page(page, live_server)
        page.click("#open-orders")

        assert set(self.durations(page)) == {"0s"}


class TestAcrossTheWidthSwitch:
    def test_an_open_sheet_stays_open_on_its_view_and_returns_to_rest(
        self, page, live_server
    ):
        open_page(page, live_server, JUST_NARROW)
        dispatch(page, id="orders", view="rename")
        page.evaluate("() => document.getElementById('orders').dataset.height = 'full'")

        page.set_viewport_size(JUST_WIDE)
        page.wait_for_function(
            "() => !document.querySelector('#orders [data-mvp-sheet-grab]')"
            ".checkVisibility()"
        )
        assert open_sheets(page) == ["orders"]
        assert shown_views(page) == ["rename"]

        page.evaluate("() => document.getElementById('orders').dataset.height = 'full'")
        page.set_viewport_size(JUST_NARROW)
        page.wait_for_function(
            "() => document.querySelector('#orders [data-mvp-sheet-grab]')"
            ".checkVisibility()"
        )

        assert open_sheets(page) == ["orders"]
        assert shown_views(page) == ["rename"]
        assert page.evaluate(
            "() => document.getElementById('orders').dataset.height"
        ) in {None, "rest"}
