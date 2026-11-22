"""The sheet in a real browser (FS-047).

Placement, focus, scrolling and the keyboard offset are computed, so only a
browser settles them. Wording, widths and spacing are ruled by eye and not
tested. Each case loads a test-only page, ``/sheet-test/``, that carries no
inline script or style.

Source: assets/js/sheet.js, mvp/templates/cotton/mvp/sheet/
"""

import time

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
<c-mvp.sheet id="quoted" title="Quoted">
  <c-mvp.sheet.view name="it's"><p>Quoted</p></c-mvp.sheet.view>
</c-mvp.sheet>
<c-mvp.sheet id="tall" title="Tall">
  {% for row in rows %}<p>Row {{ row }}</p>{% endfor %}
</c-mvp.sheet>
<c-mvp.sheet id="starts-full" title="Starts full" full><p>Short</p></c-mvp.sheet>
<button type="button" id="open-starts-full" x-data
        @click="$dispatch('mvp-sheet-open', { id: 'starts-full' })">Full</button>
<c-mvp.sheet.trigger for="missing" id="orphan" href="/missing-page/" label="Gone" />
<c-mvp.sheet.trigger for="before" id="not-a-sheet" href="/not-a-sheet-page/" label="Link" />
<button type="button" id="open-orders-event" x-data
        @click="$dispatch('mvp-sheet-open', { id: 'orders', view: 'confirm' })">Orders event</button>
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

    @BOTH_WIDTHS
    def test_a_trigger_in_the_closed_sheet_sends_focus_to_the_opener_of_that_sheet(
        self, page, live_server, viewport
    ):
        open_page(page, live_server, viewport)
        page.evaluate("() => document.getElementById('open-orders').click()")
        page.get_by_role("button", name="Delete").click()
        page.click("#open-other-plain")

        page.keyboard.press("Escape")

        assert active_id(page) == "open-orders"

    @BOTH_WIDTHS
    def test_a_trigger_outside_every_sheet_gets_focus_back_itself(
        self, page, live_server, viewport
    ):
        open_page(page, live_server, viewport)
        page.evaluate("() => document.getElementById('open-orders').click()")

        page.keyboard.press("Escape")

        assert active_id(page) == "open-orders"

    @BOTH_WIDTHS
    def test_a_named_returns_wins_over_the_opener_of_the_holding_sheet(
        self, page, live_server, viewport
    ):
        open_page(page, live_server, viewport)
        page.evaluate("() => document.getElementById('open-orders').click()")
        page.get_by_role("button", name="Delete").click()
        page.click("#open-other")

        page.keyboard.press("Escape")

        assert active_id(page) == "before"


class TestFocusReturnWithoutAnOpener:
    @BOTH_WIDTHS
    def test_a_sheet_opened_by_the_event_hands_focus_on_to_the_element_that_had_it(
        self, page, live_server, viewport
    ):
        open_page(page, live_server, viewport)
        page.focus("#open-orders-event")
        page.keyboard.press("Enter")
        assert open_sheets(page) == ["orders"]
        page.click("#open-other-plain")
        assert open_sheets(page) == ["other"]

        page.keyboard.press("Escape")

        expect(page.locator("#open-orders-event")).to_be_focused()


class TestViews:
    def test_a_view_whose_name_holds_a_quote_shows(self, phone):
        dispatch(phone, id="quoted", view="it's")

        assert shown_views(phone, "quoted") == ["it's"]

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


def after_frame(page):
    """Wait for the browser to deliver the moves it holds back until the next frame."""
    page.evaluate(
        "() => new Promise(done => requestAnimationFrame("
        "() => requestAnimationFrame(() => done())))"
    )


class Finger:
    """Touch points driven through the DevTools protocol.

    Every event carries an explicit timestamp from a virtual clock, so how fast
    a drag is does not depend on how quickly the test runs.
    """

    def __init__(self, page):
        self.page = page
        self.cdp = page.context.new_cdp_session(page)
        self.clock = time.time()
        self.points = {}

    def send(self, kind, after_ms):
        self.clock += after_ms / 1000
        points = (
            []
            if kind in {"touchEnd", "touchCancel"}
            else [{"x": x, "y": y, "id": i} for i, (x, y) in self.points.items()]
        )
        self.cdp.send(
            "Input.dispatchTouchEvent",
            {"type": kind, "touchPoints": points, "timestamp": self.clock},
        )

    def down(self, x, y, finger=0, after_ms=0):
        self.points[finger] = (x, y)
        self.send("touchStart", after_ms)

    def move(self, x, y, finger=0, after_ms=16):
        self.points[finger] = (x, y)
        self.send("touchMove", after_ms)

    def up(self, after_ms=16):
        self.send("touchEnd", after_ms)
        self.points = {}

    def cancel(self, after_ms=16):
        after_frame(self.page)
        self.send("touchCancel", after_ms)
        self.points = {}

    def trace(self, x, y0, y1, steps, step_ms):
        for step in range(1, steps + 1):
            self.move(x, y0 + (y1 - y0) * step / steps, after_ms=step_ms)

    def drag(self, x, y0, y1, steps=12, step_ms=16, hold_ms=0):
        """Press at ``y0``, move to ``y1`` and lift after holding there."""
        self.down(x, y0)
        self.trace(x, y0, y1, steps, step_ms)
        self.up(after_ms=hold_ms or 16)

    def flick(self, x, y0, y1):
        """A short, fast stroke: well over the speed that counts as a flick."""
        self.drag(x, y0, y1, steps=3, step_ms=10)


@pytest.fixture
def phone(browser, live_server):
    """A phone-sized page with touch, its finger, and the script errors it raised."""
    context = browser.new_context(viewport=PHONE, has_touch=True)
    page = context.new_page()
    page.errors = []
    page.on("pageerror", lambda error: page.errors.append(str(error)))
    open_page(page, live_server, PHONE)
    page.finger = Finger(page)
    yield page
    context.close()
    assert page.errors == []


SHEET_ANIMATIONS = (
    "() => document.getAnimations()"
    ".filter(a => a.effect.target.closest('dialog')).length"
)


def rest_box(page, sheet):
    """The box once the sheet's own animations have finished.

    The page runs one of its own, a scroll-driven one on the root element, so
    waiting for every animation to end would never finish.
    """
    page.wait_for_function(f"{SHEET_ANIMATIONS} === 0")
    return box_of(page, sheet)


def top_now(page, sheet):
    """The box's top edge while a finger is still down."""
    after_frame(page)
    return box_of(page, sheet)["top"]


def open_sheet(page, sheet):
    dispatch(page, id=sheet)
    return rest_box(page, sheet)


def grab_point(page, sheet, handle="grab"):
    box = page.locator(f"#{sheet} [data-mvp-sheet-{handle}]").bounding_box()
    return box["x"] + box["width"] / 2, box["y"] + box["height"] / 2


def height_of(page, sheet):
    return page.evaluate(
        "sheet => document.getElementById(sheet).dataset.height", sheet
    )


def expanded(page, sheet):
    return page.get_attribute(f"#{sheet} [data-mvp-sheet-grab]", "aria-expanded")


def body_state(page, sheet):
    return page.evaluate(
        "sheet => { const el = document.querySelector("
        "`#${sheet} [data-mvp-sheet-body]`);"
        " return { top: el.scrollTop,"
        " overflows: el.scrollHeight > el.clientHeight }; }",
        sheet,
    )


def closed(page, sheet):
    page.wait_for_function("sheet => !document.getElementById(sheet).open", arg=sheet)


class TestHeights:
    def test_a_short_sheet_rests_no_taller_than_its_content(self, phone):
        box = open_sheet(phone, "orders")

        assert box["height"] < box["viewport"] / 2
        assert not body_state(phone, "orders")["overflows"]
        assert box["bottom"] == pytest.approx(box["viewport"], abs=2)

    def test_a_long_sheet_rests_below_the_top_of_the_screen(self, phone):
        box = open_sheet(phone, "tall")

        assert box["top"] > box["viewport"] * 0.25
        assert box["height"] <= box["viewport"] / 2 + 1
        assert body_state(phone, "tall")["overflows"]
        assert height_of(phone, "tall") == "rest"

    def test_a_sheet_asked_to_open_full_opens_above_where_rest_would_be(self, phone):
        rest = open_sheet(phone, "tall")
        phone.keyboard.press("Escape")

        full = open_sheet(phone, "starts-full")

        assert height_of(phone, "starts-full") == "full"
        assert full["top"] < rest["top"]
        assert full["bottom"] == pytest.approx(full["viewport"], abs=2)
        assert full["top"] > 0

    def test_a_sheet_asked_to_open_full_is_a_centred_dialog_on_a_wide_screen(
        self, browser, live_server
    ):
        context = browser.new_context(viewport=DESKTOP)
        page = context.new_page()
        open_page(page, live_server, DESKTOP)

        box = open_sheet(page, "starts-full")

        assert box["top"] > 0
        assert box["bottom"] < box["viewport"]
        context.close()


class TestDraggingBetweenHeights:
    def test_dragging_up_from_rest_and_letting_go_near_the_top_makes_it_full(
        self, phone
    ):
        rest = open_sheet(phone, "tall")
        x, y = grab_point(phone, "tall")

        phone.finger.drag(x, y, 60)

        full = rest_box(phone, "tall")
        assert height_of(phone, "tall") == "full"
        assert full["top"] < rest["top"]
        assert full["bottom"] == pytest.approx(full["viewport"], abs=2)
        assert open_sheets(phone) == ["tall"]

    def test_a_short_sheet_can_be_dragged_up_to_full_too(self, phone):
        rest = open_sheet(phone, "orders")
        x, y = grab_point(phone, "orders")

        phone.finger.drag(x, y, 60)

        full = rest_box(phone, "orders")
        assert height_of(phone, "orders") == "full"
        assert full["height"] > rest["height"]
        assert full["bottom"] == pytest.approx(full["viewport"], abs=2)

    def test_the_sheet_follows_the_finger_while_it_is_down(self, phone):
        rest = open_sheet(phone, "tall")
        x, y = grab_point(phone, "tall")

        phone.finger.down(x, y)
        phone.finger.trace(x, y, y - 120, steps=6, step_ms=40)

        assert top_now(phone, "tall") == pytest.approx(rest["top"] - 120, abs=3)
        phone.finger.up(after_ms=300)

    def test_dragging_down_from_full_to_nearer_rest_leaves_it_at_rest_and_open(
        self, phone
    ):
        rest = open_sheet(phone, "tall")
        x, y = grab_point(phone, "tall")
        phone.finger.drag(x, y, 60)
        full = rest_box(phone, "tall")
        x, y = grab_point(phone, "tall")

        phone.finger.drag(x, y, y + (rest["top"] - full["top"]), hold_ms=200)

        settled = rest_box(phone, "tall")
        assert height_of(phone, "tall") == "rest"
        assert settled["top"] == pytest.approx(rest["top"], abs=2)
        assert open_sheets(phone) == ["tall"]

    def test_dragging_a_rested_sheet_well_below_closes_it_and_returns_focus(
        self, phone
    ):
        phone.tap("#open-orders")
        rest_box(phone, "orders")
        x, y = grab_point(phone, "orders")
        posts = []
        phone.on(
            "request",
            lambda request: (
                posts.append(request.url) if request.method == "POST" else None
            ),
        )

        phone.finger.drag(x, y, y + 300, hold_ms=200)

        closed(phone, "orders")
        assert open_sheets(phone) == []
        assert active_id(phone) == "open-orders"
        assert posts == []

    def test_a_small_slow_drag_down_settles_back_at_rest(self, phone):
        rest = open_sheet(phone, "tall")
        x, y = grab_point(phone, "tall")

        phone.finger.drag(x, y, y + 30, hold_ms=250)

        settled = rest_box(phone, "tall")
        assert open_sheets(phone) == ["tall"]
        assert height_of(phone, "tall") == "rest"
        assert settled["top"] == pytest.approx(rest["top"], abs=2)

    def test_a_short_flick_up_from_rest_makes_it_full(self, phone):
        rest = open_sheet(phone, "tall")
        x, y = grab_point(phone, "tall")

        phone.finger.flick(x, y, y - 60)

        full = rest_box(phone, "tall")
        assert height_of(phone, "tall") == "full"
        assert full["top"] < rest["top"]

    def test_a_short_flick_down_from_rest_closes_it(self, phone):
        open_sheet(phone, "tall")
        x, y = grab_point(phone, "tall")

        phone.finger.flick(x, y, y + 40)

        closed(phone, "tall")

    def test_a_short_flick_down_from_full_leaves_it_at_rest_and_open(self, phone):
        rest = open_sheet(phone, "tall")
        x, y = grab_point(phone, "tall")
        phone.finger.drag(x, y, 60)
        rest_box(phone, "tall")
        x, y = grab_point(phone, "tall")

        phone.finger.flick(x, y, y + 40)

        settled = rest_box(phone, "tall")
        assert open_sheets(phone) == ["tall"]
        assert height_of(phone, "tall") == "rest"
        assert settled["top"] == pytest.approx(rest["top"], abs=2)

    def test_a_flick_down_after_dragging_up_toward_full_ends_at_rest_and_open(
        self, phone
    ):
        open_sheet(phone, "tall")
        x, y = grab_point(phone, "tall")

        phone.finger.down(x, y)
        phone.finger.trace(x, y, 80, steps=12, step_ms=40)
        phone.finger.trace(x, 80, 80, steps=5, step_ms=20)
        phone.finger.trace(x, 80, 160, steps=2, step_ms=10)
        phone.finger.up(after_ms=10)

        rest_box(phone, "tall")
        assert open_sheets(phone) == ["tall"]
        assert height_of(phone, "tall") == "rest"

    def test_a_drag_down_from_full_past_rest_closes_it(self, phone):
        open_sheet(phone, "tall")
        x, y = grab_point(phone, "tall")
        phone.finger.drag(x, y, 60)
        rest_box(phone, "tall")
        x, y = grab_point(phone, "tall")

        phone.finger.drag(x, y, PHONE["height"] - 20, hold_ms=200)

        closed(phone, "tall")

    def test_a_drag_that_starts_on_the_head_moves_the_sheet_too(self, phone):
        rest = open_sheet(phone, "tall")
        x, y = grab_point(phone, "tall", "head")

        phone.finger.drag(x, y, 60)

        assert rest_box(phone, "tall")["top"] < rest["top"]
        assert height_of(phone, "tall") == "full"

    def test_a_cancelled_drag_settles_where_the_finger_last_was(self, phone):
        rest = open_sheet(phone, "tall")
        x, y = grab_point(phone, "tall")

        phone.finger.down(x, y)
        phone.finger.trace(x, y, y - (rest["top"] - 80), steps=8, step_ms=40)
        phone.finger.cancel(after_ms=300)

        settled = rest_box(phone, "tall")
        assert height_of(phone, "tall") == "full"
        assert settled["top"] < rest["top"]

    def test_closing_and_opening_again_opens_at_rest(self, phone):
        rest = open_sheet(phone, "tall")
        x, y = grab_point(phone, "tall")
        phone.finger.drag(x, y, 60)
        rest_box(phone, "tall")
        phone.keyboard.press("Escape")

        again = open_sheet(phone, "tall")

        assert height_of(phone, "tall") == "rest"
        assert again["top"] == pytest.approx(rest["top"], abs=2)

    def test_a_sheet_asked_to_open_full_opens_full_again_after_being_shrunk(
        self, phone
    ):
        full = open_sheet(phone, "starts-full")
        x, y = grab_point(phone, "starts-full")
        phone.finger.drag(x, y, y + (full["height"] / 2), hold_ms=200)
        rest_box(phone, "starts-full")
        assert height_of(phone, "starts-full") == "rest"
        phone.keyboard.press("Escape")

        again = open_sheet(phone, "starts-full")

        assert height_of(phone, "starts-full") == "full"
        assert again["top"] == pytest.approx(full["top"], abs=2)


class TestFixedSheet:
    def test_it_follows_a_drag_up_a_little_and_settles_back(self, phone):
        phone.tap("#open-typing")
        rest = rest_box(phone, "typing")
        x, y = grab_point(phone, "typing")

        phone.finger.down(x, y)
        phone.finger.trace(x, y, y - 300, steps=8, step_ms=40)
        moved = rest["top"] - top_now(phone, "typing")
        phone.finger.up(after_ms=300)

        assert 0 < moved <= 25
        settled = rest_box(phone, "typing")
        assert settled["top"] == pytest.approx(rest["top"], abs=2)
        assert height_of(phone, "typing") == "rest"
        assert open_sheets(phone) == ["typing"]

    def test_it_still_closes_when_dragged_down(self, phone):
        phone.tap("#open-typing")
        rest_box(phone, "typing")
        x, y = grab_point(phone, "typing")

        phone.finger.drag(x, y, PHONE["height"] - 20, hold_ms=200)

        closed(phone, "typing")

    def test_it_still_closes_when_flicked_down(self, phone):
        phone.tap("#open-typing")
        rest_box(phone, "typing")
        x, y = grab_point(phone, "typing")

        phone.finger.flick(x, y, y + 40)

        closed(phone, "typing")

    def test_its_grab_bar_offers_no_change_of_height(self, phone):
        phone.tap("#open-typing")
        rest = rest_box(phone, "typing")

        phone.tap("#typing [data-mvp-sheet-grab]")

        assert expanded(phone, "typing") is None
        assert height_of(phone, "typing") == "rest"
        assert rest_box(phone, "typing")["top"] == pytest.approx(rest["top"], abs=2)


class TestBodyAndPageBehind:
    def test_a_drag_inside_the_body_scrolls_the_body_and_not_the_sheet(self, phone):
        open_sheet(phone, "tall")
        x, y = grab_point(phone, "tall")
        phone.finger.drag(x, y, 60)
        full = rest_box(phone, "tall")
        body = phone.locator("#tall [data-mvp-sheet-body]").bounding_box()
        middle = body["y"] + body["height"] / 2

        phone.finger.drag(x, middle, middle - 150)

        phone.wait_for_function(
            "() => document.querySelector('#tall [data-mvp-sheet-body]').scrollTop > 0"
        )
        assert rest_box(phone, "tall")["top"] == pytest.approx(full["top"], abs=1)
        assert height_of(phone, "tall") == "full"

    def test_the_page_behind_does_not_scroll_during_a_drag(self, phone):
        phone.tap("#open-orders")
        rest_box(phone, "orders")
        x, y = grab_point(phone, "orders", "head")

        phone.finger.down(x, y)
        phone.finger.trace(x, y, y - 200, steps=8, step_ms=40)
        during = phone.evaluate("() => window.scrollY")
        phone.finger.trace(x, y - 200, y + 20, steps=8, step_ms=40)
        phone.finger.up(after_ms=300)

        assert during == 0
        assert phone.evaluate("() => window.scrollY") == 0


class TestGrabBar:
    def test_a_tap_switches_between_the_heights_and_says_which(self, phone):
        rest = open_sheet(phone, "tall")
        assert expanded(phone, "tall") == "false"

        phone.tap("#tall [data-mvp-sheet-grab]")
        full = rest_box(phone, "tall")
        assert expanded(phone, "tall") == "true"
        assert full["top"] < rest["top"]

        phone.tap("#tall [data-mvp-sheet-grab]")
        back = rest_box(phone, "tall")
        assert expanded(phone, "tall") == "false"
        assert back["top"] == pytest.approx(rest["top"], abs=2)

    def test_the_keyboard_switches_between_the_heights_and_says_which(self, phone):
        rest = open_sheet(phone, "tall")
        phone.focus("#tall [data-mvp-sheet-grab]")

        phone.keyboard.press("Enter")
        full = rest_box(phone, "tall")
        assert expanded(phone, "tall") == "true"
        assert full["top"] < rest["top"]

        phone.keyboard.press("Space")
        back = rest_box(phone, "tall")
        assert expanded(phone, "tall") == "false"
        assert back["top"] == pytest.approx(rest["top"], abs=2)

    def test_a_sheet_opened_full_says_so(self, phone):
        open_sheet(phone, "starts-full")

        assert expanded(phone, "starts-full") == "true"

    def test_a_mouse_drag_ending_on_the_grab_bar_is_a_drag_and_not_a_tap(self, phone):
        rest = open_sheet(phone, "tall")
        x, y = grab_point(phone, "tall")

        phone.mouse.move(x, y)
        phone.mouse.down()
        for step in range(1, 7):
            phone.mouse.move(x, y - (y - 60) * step / 6)
            phone.wait_for_timeout(60)
        phone.wait_for_timeout(200)
        phone.mouse.up()

        full = rest_box(phone, "tall")
        phone.wait_for_timeout(100)
        assert height_of(phone, "tall") == "full"
        assert full["top"] < rest["top"]


class TestGestureEdgeCases:
    def test_a_sheet_opened_mid_drag_closes_the_dragged_one_and_stays_clean(
        self, phone
    ):
        open_sheet(phone, "tall")
        x, y = grab_point(phone, "tall")

        phone.finger.down(x, y)
        phone.finger.trace(x, y, y - 100, steps=4, step_ms=40)
        dispatch(phone, id="other")
        phone.finger.trace(x, y - 100, y - 150, steps=2, step_ms=40)
        phone.finger.up(after_ms=300)

        other = rest_box(phone, "other")
        assert open_sheets(phone) == ["other"]
        assert height_of(phone, "other") == "rest"
        assert other["bottom"] == pytest.approx(other["viewport"], abs=2)
        styles = "() => document.querySelector('#tall .mvp-sheet-box').style.cssText"
        assert phone.evaluate(styles) == ""

    def test_a_second_finger_does_not_move_the_sheet_twice_as_far(self, phone):
        rest = open_sheet(phone, "tall")
        x, y = grab_point(phone, "tall")

        phone.finger.down(x, y)
        phone.finger.down(x + 40, y + 200, finger=1)
        for step in range(1, 5):
            phone.finger.points[0] = (x, y - 25 * step)
            phone.finger.points[1] = (x + 40, y + 200 - 25 * step)
            phone.finger.send("touchMove", 40)

        assert top_now(phone, "tall") == pytest.approx(rest["top"] - 100, abs=3)
        phone.finger.up(after_ms=300)

    def test_a_finger_that_lands_second_on_the_grab_bar_does_not_drag(self, phone):
        rest = open_sheet(phone, "tall")
        x, y = grab_point(phone, "tall")
        body = phone.locator("#tall [data-mvp-sheet-body]").bounding_box()

        phone.finger.down(x, body["y"] + 40)
        phone.finger.down(x + 20, y, finger=1)
        for step in range(1, 5):
            phone.finger.points[1] = (x + 20, y - 25 * step)
            phone.finger.send("touchMove", 40)

        assert top_now(phone, "tall") == pytest.approx(rest["top"], abs=1)
        phone.finger.up(after_ms=300)
        assert height_of(phone, "tall") == "rest"


class TestReducedMotionDrag:
    def test_the_sheet_follows_the_finger_and_settles_without_animating(self, phone):
        phone.emulate_media(reduced_motion="reduce")
        rest = open_sheet(phone, "tall")
        x, y = grab_point(phone, "tall")

        phone.finger.down(x, y)
        phone.finger.trace(x, y, y - 150, steps=6, step_ms=40)
        assert top_now(phone, "tall") == pytest.approx(rest["top"] - 150, abs=3)
        phone.finger.trace(x, y - 150, 60, steps=6, step_ms=40)
        phone.finger.up(after_ms=300)

        assert height_of(phone, "tall") == "full"
        assert phone.evaluate(SHEET_ANIMATIONS) == 0
        assert rest_box(phone, "tall")["top"] < rest["top"]

    def test_a_closing_drag_closes_straight_away(self, phone):
        phone.emulate_media(reduced_motion="reduce")
        open_sheet(phone, "tall")
        x, y = grab_point(phone, "tall")

        phone.finger.drag(x, y, PHONE["height"] - 20, hold_ms=200)

        assert open_sheets(phone) == []


class TestWideScreenIgnoresDrags:
    @pytest.mark.parametrize("viewport", [DESKTOP, JUST_WIDE], ids=["1280", "640"])
    def test_the_pointer_moves_nothing(self, browser, live_server, viewport):
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        open_page(page, live_server, viewport)
        before = open_sheet(page, "orders")
        head = page.locator("#orders [data-mvp-sheet-head]").bounding_box()
        x, y = head["x"] + 20, head["y"] + head["height"] / 2

        page.mouse.move(x, y)
        page.mouse.down()
        for step in range(1, 6):
            page.mouse.move(x, y + 80 * step)
            page.wait_for_timeout(30)
        during = box_of(page, "orders")
        page.mouse.up()

        after = rest_box(page, "orders")
        assert open_sheets(page) == ["orders"]
        assert height_of(page, "orders") == "rest"
        assert during["top"] == pytest.approx(before["top"], abs=1)
        assert after["top"] == pytest.approx(before["top"], abs=1)
        context.close()


class TestTriggerModifierClicks:
    @pytest.mark.parametrize("key", ["Control", "Meta", "Shift"])
    def test_a_link_trigger_is_left_to_the_browser_with_a_modifier_held(
        self, page, live_server, key
    ):
        open_page(page, live_server)
        page.evaluate(
            """
            () => document.addEventListener("click", event => {
              window.leftAlone = !event.defaultPrevented;
              event.preventDefault();
            })
            """
        )

        page.click("#open-orders", modifiers=[key])

        assert page.evaluate("() => window.leftAlone") is True
        assert open_sheets(page) == []

    def test_a_plain_click_still_opens_the_sheet(self, page, live_server):
        open_page(page, live_server)

        page.click("#open-orders")

        assert open_sheets(page) == ["orders"]
