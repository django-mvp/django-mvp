"""The list row's menu and the buttons built under it, in a real browser (FS-048).

What is placed, focusable, open or moved is computed, so only a browser settles it.
Wording and spacing are ruled by eye and not tested. Each case loads a test-only
page, ``/row-test/``, that carries no inline script or style.

Source: assets/js/row_actions.js, mvp/templates/cotton/mvp/list/row/
"""

import time

import pytest
from django.http import HttpResponse
from django.template import engines
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django_cotton.compiler_regex import CottonCompiler

from demo import urls as demo_urls
from mvp.config import MVP_CONFIG
from tests.conftest import requires_browser, urlconf_of

pytestmark = [pytest.mark.e2e, requires_browser]

PHONE = {"width": 390, "height": 844}
DESKTOP = {"width": 1280, "height": 800}
NAMES = ["Open", "Rename", "Remove"]

PAGE = """
{% extends "mvp/base.html" %}
{% block content %}
<a id="before" href="#before">Before</a>
<form id="rename-form" method="post" action="/row-test/posted/"></form>
<ul class="list">
  <c-mvp.list.row id="report" label="Quarterly report" lead="Due Friday">
    <span>Quarterly report</span>
    <c-slot name="actions">
      <c-mvp.list.row.action text="Open" icon="edit" href="#ran-open" main />
      <c-mvp.list.row.action text="Rename" icon="edit" id="rename-action"
                             form="rename-form" type="submit"
                             label="Rename Quarterly report" />
      <c-mvp.list.row.action text="Remove" icon="delete" href="#ran-remove" danger />
    </c-slot>
  </c-mvp.list.row>
</ul>
<button type="button" id="after">After</button>
{% endblock %}
"""


def link_markup(index):
    """The link a row holds, for a swipe to end over."""
    return f'<a id="link{index}" href="#followed">Row {index}</a>'


def swipe_rows(count, *, main=True, link=True):
    """Markup for ``count`` rows, each with three actions."""
    return "".join(
        f"""
  <c-mvp.list.row id="row{index}" label="Row {index}" lead="Due Friday">
    {link_markup(index) if link else "<span>Row</span>"}
    <c-slot name="actions">
      <c-mvp.list.row.action text="Open" icon="edit" href="#ran-open"
                             {"main" if main else ""} />
      <c-mvp.list.row.action text="Rename" icon="edit" href="#ran-rename" />
      <c-mvp.list.row.action text="Remove" icon="delete" href="#ran-remove" danger />
    </c-slot>
  </c-mvp.list.row>"""
        for index in range(count)
    )


LEAVING_ROWS = """
  <c-mvp.list.row id="gone" label="Gone" lead="Due Friday">
    <a id="link-gone" href="#followed">Gone</a>
    <c-slot name="actions">
      <c-mvp.list.row.action text="Archive" icon="edit" href="#ran-archive"
                             main leaves />
      <c-mvp.list.row.action text="Rename" icon="edit" href="#ran-rename" />
      <c-mvp.list.row.action text="Remove" icon="delete" danger leaves
                             hx-post="/row-swipe/error/" hx-swap="none" />
    </c-slot>
  </c-mvp.list.row>
  <c-mvp.list.row id="kept" label="Kept" lead="Due Friday">
    <a id="link-kept" href="#followed">Kept</a>
    <c-slot name="actions">
      <c-mvp.list.row.action text="Keep" icon="edit" leaves hx-post="/row-swipe/error/"
                             hx-swap="none" hx-confirm="Sure?" />
      <c-mvp.list.row.action text="Rename" icon="edit" href="#ran-rename" />
      <c-mvp.list.row.action text="Refresh" icon="edit" hx-post="/row-swipe/error/"
                             hx-swap="none" />
    </c-slot>
  </c-mvp.list.row>
"""

CONFIRMING_ROW = """
  <c-mvp.list.row id="asking" label="Asking" lead="Due Friday">
    <a id="link-asking" href="#followed">Asking</a>
    <c-slot name="actions">
      <c-mvp.list.row.action text="Keep" icon="edit" main leaves
                             hx-post="/row-swipe/error/"
                             hx-swap="none" hx-confirm="Sure?" />
      <c-mvp.list.row.action text="Rename" icon="edit" href="#ran-rename" />
    </c-slot>
  </c-mvp.list.row>
"""

DATA_PREFIXED_ROW = """
  <c-mvp.list.row id="prefixed" label="Prefixed" lead="Due Friday">
    <a id="link-prefixed" href="#followed">Prefixed</a>
    <c-slot name="actions">
      <c-mvp.list.row.action text="Keep" icon="edit" leaves
                             data-hx-post="/row-swipe/error/"
                             data-hx-swap="none" data-hx-confirm="Sure?" />
      <c-mvp.list.row.action text="Rename" icon="edit" href="#ran-rename" />
    </c-slot>
  </c-mvp.list.row>
"""

REMOVING_ROWS = """
  <c-mvp.list.row id="removing" label="Removing" lead="Due Friday">
    <a id="link-removing" href="#followed">Removing</a>
    <c-slot name="actions">
      <c-mvp.list.row.action text="Remove" icon="delete" danger leaves
                             hx-post="/row-swipe/emptied/"
                             hx-target="closest [data-mvp-row]" hx-swap="outerHTML" />
      <c-mvp.list.row.action text="Rename" icon="edit" href="#ran-rename" />
    </c-slot>
  </c-mvp.list.row>
  <c-mvp.list.row id="staying" label="Staying" lead="Due Friday">
    <a id="link-staying" href="#followed">Staying</a>
    <c-slot name="actions">
      <c-mvp.list.row.action text="Rename" icon="edit" href="#ran-rename" />
    </c-slot>
  </c-mvp.list.row>
"""

REORDER_LIST = (
    """<button type="button" id="start" data-mvp-reorder-start="steps">Start</button>
<button type="button" id="end" data-mvp-reorder-end="steps">End</button>
<c-mvp.reorder id="steps" label="Steps" mode="on-demand">
  <c-mvp.reorder.row value="a" label="Alpha">Alpha</c-mvp.reorder.row>
  <c-mvp.reorder.row value="b" label="Beta">Beta</c-mvp.reorder.row>"""
    + swipe_rows(1)
    + "</c-mvp.reorder>"
)

NESTED_LISTS = (
    '<div id="outer"><div id="inner"><ul class="list">'
    + swipe_rows(1)
    + "</ul></div></div>"
)

SWAP_REGION = (
    '<button type="button" id="reload" hx-get="/row-swipe-rows/" hx-target="#region"'
    ' hx-swap="innerHTML">Reload</button><div id="region"><ul class="list">'
    + swipe_rows(1)
    + "</ul></div>"
)

# Pages that draw their own list around the rows.
OWN_LIST = {"reorder", "nested", "swap", "below", "hidden"}

SWIPE_PAGES = {
    "below": (
        '<div style="height: 3000px"></div><ul class="list">' + swipe_rows(1) + "</ul>"
    ),
    "reorder": REORDER_LIST,
    "nested": NESTED_LISTS,
    "swap": SWAP_REGION,
    "leaves": LEAVING_ROWS,
    "confirming": CONFIRMING_ROW,
    "prefixed": DATA_PREFIXED_ROW,
    "removing": REMOVING_ROWS,
    "main": swipe_rows(1),
    "plain": swipe_rows(1, main=False),
    "many": swipe_rows(30),
    "scroller": '<div id="scroller">' + swipe_rows(20) + "</div>",
    "hidden": '<div hidden><ul class="list">' + swipe_rows(1) + "</ul></div>",
    "sheet": (
        '<c-mvp.sheet.trigger for="holder" id="holder-open" label="Holder" />'
        '<c-mvp.sheet id="holder" title="Holder">' + swipe_rows(1) + "</c-mvp.sheet>"
    ),
}


def swipe_page(request, name):
    """Draw a test page with the rows a swipe needs."""
    rows = SWIPE_PAGES[name]
    if name not in OWN_LIST:
        rows = f'<ul class="list">{rows}</ul>'
    source = (
        '{% extends "mvp/base.html" %}{% block content %}'
        '<button type="button" id="after">After</button>' + rows + "{% endblock %}"
    )
    template = engines["django"].from_string(CottonCompiler().process(source))
    return HttpResponse(template.render({}, request))


def swapped_rows(request):
    """Stand in for the server's answer that replaces a list with new rows."""
    source = '<ul class="list">' + swipe_rows(2) + "</ul>"
    template = engines["django"].from_string(CottonCompiler().process(source))
    return HttpResponse(template.render({}, request))


@csrf_exempt
def failing_request(request):
    """Stand in for a server that cannot do what an action asks."""
    return HttpResponse("no", status=500)


@csrf_exempt
def emptied_request(request):
    """Stand in for a server that did what an action asked and has nothing to show."""
    return HttpResponse("")


def row_test_page(request):
    """Draw the test page."""
    template = engines["django"].from_string(CottonCompiler().process(PAGE))
    return HttpResponse(template.render({}, request))


@csrf_exempt
def landing_page(request):
    """Stand in for the address the form posts to."""
    return HttpResponse("<p id='landed'>posted</p>")


@pytest.fixture(autouse=True)
def row_test_urls(settings, monkeypatch):
    # The icon font is the project's own choice and the demo's is a CDN's.
    monkeypatch.setitem(MVP_CONFIG, "icon_stylesheet", "")
    settings.ROOT_URLCONF = urlconf_of(
        path("row-test/", row_test_page),
        path("row-test/posted/", landing_page),
        path("row-swipe/error/", failing_request),
        path("row-swipe/emptied/", emptied_request),
        path("row-swipe-rows/", swapped_rows),
        path("row-swipe/<str:name>/", swipe_page),
        *demo_urls.urlpatterns,
    )


@pytest.fixture
def touch_page(browser, live_server):
    """A phone: a coarse pointer, touch and a narrow screen."""
    context = browser.new_context(viewport=PHONE, has_touch=True, is_mobile=True)
    context.add_init_script(REMEMBER_HINT)
    page = context.new_page()
    open_page(page, live_server)
    yield page
    context.close()


@pytest.fixture
def mouse_page(page, live_server):
    page.set_viewport_size(DESKTOP)
    open_page(page, live_server)
    return page


def open_page(page, live_server):
    page.set_default_timeout(5000)
    page.goto(f"{live_server.url}/row-test/")
    page.wait_for_function("() => window.Alpine && Alpine.version")
    page.wait_for_selector("[data-mvp-row-ready]", state="attached")


def words_of(locator):
    return [text.strip() for text in locator.all_inner_texts()]


class TestButtonsUnderTheRow:
    def test_there_is_one_button_for_each_action(self, mouse_page):
        buttons = mouse_page.locator(".mvp-row-under [data-mvp-row-button]")

        assert words_of(buttons) == NAMES

    def test_the_buttons_leave_ids_and_form_hooks_once_on_the_page(self, mouse_page):
        assert mouse_page.locator("#rename-action").count() == 1
        assert mouse_page.locator("[form='rename-form']").count() == 1
        assert mouse_page.locator(".mvp-row-under [id]").count() == 0
        assert mouse_page.locator(".mvp-row-under [form]").count() == 0

    def test_a_button_carries_the_actions_name_only_when_it_has_one(self, mouse_page):
        labels = mouse_page.locator(
            ".mvp-row-under [data-mvp-row-button]"
        ).evaluate_all("buttons => buttons.map(b => b.getAttribute('aria-label'))")

        assert labels == [None, "Rename Quarterly report", None]

    def test_the_main_action_is_marked_and_the_dangerous_one_is_a_tone(
        self, mouse_page
    ):
        buttons = mouse_page.locator(".mvp-row-under [data-mvp-row-button]")

        assert buttons.nth(0).get_attribute("data-mvp-row-main") is not None
        assert "mvp-row-button-primary" in buttons.nth(0).get_attribute("class")
        assert "mvp-row-button-neutral" in buttons.nth(1).get_attribute("class")
        assert "mvp-row-button-danger" in buttons.nth(2).get_attribute("class")

    def test_pressing_a_button_presses_the_action(self, mouse_page):
        mouse_page.locator(".mvp-row-under [data-mvp-row-button]").nth(
            2
        ).dispatch_event("click")

        assert mouse_page.evaluate("() => location.hash") == "#ran-remove"

    def test_the_layer_is_inert(self, mouse_page):
        assert mouse_page.locator(".mvp-row-under").evaluate("el => el.inert")


class TestMenuWithAMouse:
    def test_the_dropdown_opens_and_offers_every_action(self, mouse_page):
        mouse_page.click(".mvp-row-dropdown button")

        panel = mouse_page.locator(".mvp-row-dropdown .dropdown-content")
        assert panel.evaluate("el => el.matches(':popover-open')")
        assert words_of(panel.locator("[data-mvp-row-action]")) == NAMES

    def test_the_sheet_trigger_is_not_shown(self, mouse_page):
        assert not mouse_page.locator(".mvp-row-sheet-trigger").is_visible()


class TestMenuWithATouch:
    def test_the_sheet_opens_with_every_action_and_closes_once_one_is_chosen(
        self, touch_page
    ):
        assert not touch_page.locator(".mvp-row-dropdown").is_visible()

        touch_page.tap(".mvp-row-sheet-trigger")

        sheet = touch_page.locator("#report-sheet")
        assert sheet.evaluate("el => el.open")
        actions = sheet.locator("[data-mvp-row-sheet-body] [data-mvp-row-action]")
        assert words_of(actions) == NAMES

        actions.nth(0).tap()

        touch_page.wait_for_function(
            "() => !document.getElementById('report-sheet').open"
        )
        assert touch_page.evaluate("() => location.hash") == "#ran-open"

    def test_the_menu_is_back_in_the_dropdown_after_the_sheet_closes(self, touch_page):
        touch_page.tap(".mvp-row-sheet-trigger")
        touch_page.wait_for_function(
            "() => document.getElementById('report-sheet').open"
        )
        touch_page.keyboard.press("Escape")
        touch_page.wait_for_function(
            "() => !document.getElementById('report-sheet').open"
        )

        assert (
            touch_page.locator("[data-mvp-row-sheet-body] [data-mvp-row-menu]").count()
            == 0
        )
        assert (
            touch_page.locator(
                ".mvp-row-dropdown .dropdown-content [data-mvp-row-menu]"
            ).count()
            == 1
        )


class TestMenuWithAKeyboard:
    def test_tab_reaches_the_control_and_never_the_buttons_under_the_row(
        self, mouse_page
    ):
        mouse_page.focus("#before")
        reached = []
        for _ in range(4):
            mouse_page.keyboard.press("Tab")
            reached.append(
                mouse_page.evaluate(
                    "() => document.activeElement.closest('.mvp-row-under') !== null"
                    " ? 'under' : document.activeElement.closest('.mvp-row-more')"
                    " ? 'more' : document.activeElement.id"
                )
            )

        assert "more" in reached
        assert "under" not in reached

    def test_the_menu_opens_from_the_control_and_runs_every_action(self, mouse_page):
        items = mouse_page.locator(
            ".mvp-row-dropdown .dropdown-content [data-mvp-row-action]"
        )

        def choose(index):
            mouse_page.focus(".mvp-row-dropdown button")
            mouse_page.keyboard.press("Enter")
            items.nth(index).wait_for(state="visible")
            items.nth(index).focus()
            mouse_page.keyboard.press("Enter")

        # The Rename action submits a form and leaves the page, so it goes last.
        for index, expected in ((0, "#ran-open"), (2, "#ran-remove")):
            choose(index)

            mouse_page.wait_for_function(f"() => location.hash === '{expected}'")
            items.nth(index).wait_for(state="hidden")

        choose(1)

        mouse_page.wait_for_selector("#landed")

    def test_the_form_hooked_action_submits_its_form(self, mouse_page):
        mouse_page.click(".mvp-row-dropdown button")
        mouse_page.locator(".mvp-row-dropdown .dropdown-content #rename-action").click()

        mouse_page.wait_for_selector("#landed")


class TestWithoutTheScript:
    @pytest.fixture
    def bare_page(self, page, live_server):
        page.set_default_timeout(5000)
        page.route(
            "**/django-mvp.js",
            lambda route: route.fulfill(body="", content_type="text/javascript"),
        )
        page.set_viewport_size(DESKTOP)
        page.goto(f"{live_server.url}/row-test/")
        return page

    def test_the_dropdown_still_opens(self, bare_page):
        assert bare_page.locator("[data-mvp-row-ready]").count() == 0

        bare_page.click(".mvp-row-dropdown button")

        for name in NAMES:
            assert bare_page.get_by_text(name, exact=True).first.is_visible()


class TestNothingFromElsewhere:
    def test_a_page_with_a_row_requests_nothing_from_another_origin(
        self, page, live_server
    ):
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
        page.click(".mvp-row-dropdown button")
        page.wait_for_load_state("networkidle")

        assert foreign == []


REST = 3 * 4.75 * 16
OFFSET = "el => parseFloat(el.style.getPropertyValue('--mvp-row-x') || '0')"
REMEMBER_HINT = "localStorage.setItem('mvp-row-hinted', '1')"

# Records, for the page that is loading, whether any row was ever nudged.
WATCH_HINT = """
window.wasHinting = false;
new MutationObserver(() => {
  if (document.querySelector('.mvp-row.is-hinting')) window.wasHinting = true;
}).observe(document, {subtree: true, attributes: true, attributeFilter: ['class']});
"""

VIBRATE = (
    "window.vibrations = [];"
    "navigator.vibrate = (ms) => { window.vibrations.push(ms); return true; };"
)


class Finger:
    """One touch moving sideways, through the DevTools protocol.

    Every event carries a timestamp from a virtual clock, so how fast a drag is
    does not depend on how quickly the test runs.
    """

    def __init__(self, page):
        self.cdp = page.context.new_cdp_session(page)
        self.clock = time.time()
        self.at = None

    def send(self, kind, after_ms):
        self.clock += after_ms / 1000
        points = [] if kind == "touchEnd" else [{"x": self.at[0], "y": self.at[1]}]
        self.cdp.send(
            "Input.dispatchTouchEvent",
            {"type": kind, "touchPoints": points, "timestamp": self.clock},
        )

    def down(self, x, y):
        self.at = (x, y)
        self.send("touchStart", 0)

    def move(self, x, y, after_ms=16):
        self.at = (x, y)
        self.send("touchMove", after_ms)

    def up(self):
        self.send("touchEnd", 16)

    def tap(self, locator):
        """Touch the middle of an element and lift."""
        # A touch within the double-tap window of the last one gives no click.
        time.sleep(max(0, self.clock - time.time()) + 0.4)
        self.clock = time.time()
        box = locator.bounding_box()
        self.down(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        self.send("touchEnd", 40)

    def drag(self, x0, x1, y, steps=12, step_ms=16):
        """Press at ``x0``, move to ``x1`` in even steps and lift."""
        self.down(x0, y)
        self.pull(x0, x1, y, steps, step_ms)
        self.up()

    def pull(self, x0, x1, y, steps=12, step_ms=16):
        for step in range(1, steps + 1):
            self.move(x0 + (x1 - x0) * step / steps, y, step_ms)

    def flick(self, x0, x1, y):
        """A short, fast stroke: well over the speed that counts as a flick."""
        self.drag(x0, x1, y, steps=3, step_ms=10)


@pytest.fixture
def finger_page(browser, live_server, request):
    """A phone open on the swipe page the test names, with a finger."""
    context = browser.new_context(viewport=PHONE, has_touch=True, is_mobile=True)
    context.add_init_script(VIBRATE)
    context.add_init_script(REMEMBER_HINT)
    page = context.new_page()
    page.set_default_timeout(5000)
    page.errors = []
    page.on("pageerror", lambda error: page.errors.append(str(error)))
    name = getattr(request, "param", "main")
    page.goto(f"{live_server.url}/row-swipe/{name}/")
    page.wait_for_function("() => window.Alpine && Alpine.version")
    page.wait_for_selector("[data-mvp-row-ready]", state="attached")
    page.finger = Finger(page)
    yield page
    context.close()


def on_page(name):
    return pytest.mark.parametrize("finger_page", [name], indirect=True)


def row_state(page, index=0):
    """The row's open flag and offset, once its transitions have been given a frame."""
    row = page.locator(".mvp-row").nth(index)
    return row.evaluate(
        "el => ({open: el.classList.contains('is-open'),"
        " full: el.classList.contains('is-full'),"
        " dragging: el.classList.contains('is-dragging'),"
        " x: parseFloat(el.style.getPropertyValue('--mvp-row-x') || '0')})"
    )


def middle_of(page, index=0):
    box = page.locator(".mvp-row").nth(index).bounding_box()
    return box["y"] + box["height"] / 2


class TestSwipeOpensARow:
    def test_a_short_swipe_leaves_the_row_open_on_its_actions(self, finger_page):
        y = middle_of(finger_page)

        finger_page.finger.drag(300, 140, y)

        state = row_state(finger_page)
        assert state["open"]
        assert state["x"] == pytest.approx(-REST, abs=2)
        assert not finger_page.locator(".mvp-row-under").evaluate("el => el.inert")

    def test_a_swipe_short_of_half_the_actions_closes_again(self, finger_page):
        y = middle_of(finger_page)

        finger_page.finger.drag(300, 250, y)

        state = row_state(finger_page)
        assert not state["open"]
        assert state["x"] == 0
        assert finger_page.locator(".mvp-row-under").evaluate("el => el.inert")

    def test_a_flick_opens_however_short_and_a_flick_back_closes(self, finger_page):
        y = middle_of(finger_page)

        finger_page.finger.flick(300, 270, y)
        assert row_state(finger_page)["open"]

        finger_page.finger.flick(100, 160, y)
        assert not row_state(finger_page)["open"]

    def test_a_swipe_the_wrong_way_gives_a_little_and_settles(self, finger_page):
        y = middle_of(finger_page)
        finger_page.finger.down(100, y)
        finger_page.finger.pull(100, 300, y)

        assert 0 < row_state(finger_page)["x"] <= 16

        finger_page.finger.up()
        assert row_state(finger_page)["x"] == 0

    @on_page("plain")
    def test_a_row_without_a_main_action_resists_and_settles_on_its_actions(
        self, finger_page
    ):
        y = middle_of(finger_page)
        finger_page.finger.down(360, y)
        finger_page.finger.pull(360, 40, y)

        held = row_state(finger_page)
        assert not held["full"]
        assert REST < -held["x"] < REST + (320 - REST) * 0.25 + 2

        finger_page.finger.up()
        assert row_state(finger_page)["x"] == pytest.approx(-REST, abs=2)
        assert finger_page.evaluate("() => location.hash") == ""

    def test_a_mouse_drag_does_not_move_the_row(self, browser, live_server):
        page = browser.new_page(viewport=DESKTOP)
        page.goto(f"{live_server.url}/row-swipe/main/")
        page.wait_for_selector("[data-mvp-row-ready]", state="attached")
        box = page.locator(".mvp-row").bounding_box()
        y = box["y"] + box["height"] / 2

        page.mouse.move(600, y)
        page.mouse.down()
        page.mouse.move(300, y, steps=10)
        page.mouse.up()

        assert row_state(page) == {
            "open": False,
            "full": False,
            "dragging": False,
            "x": 0,
        }
        page.close()


class TestSwipeRunsTheMainAction:
    def test_a_swipe_past_sixty_percent_presses_the_main_action(self, finger_page):
        y = middle_of(finger_page)

        finger_page.finger.drag(370, 60, y)

        finger_page.wait_for_function("() => location.hash === '#ran-open'")
        finger_page.wait_for_function(
            "() => !document.querySelector('.mvp-row').classList.contains('is-open')"
        )

    def test_the_cue_is_given_once_as_the_point_is_passed(self, finger_page):
        y = middle_of(finger_page)
        finger_page.finger.down(370, y)
        finger_page.finger.pull(370, 300, y)
        assert finger_page.evaluate("() => vibrations.length") == 0

        finger_page.finger.pull(300, 40, y, steps=20)
        finger_page.finger.pull(40, 30, y, steps=4)

        assert finger_page.evaluate("() => vibrations.length") == 1
        finger_page.finger.up()

    @on_page("plain")
    def test_a_row_with_no_main_action_gives_no_cue(self, finger_page):
        y = middle_of(finger_page)

        finger_page.finger.drag(370, 40, y)

        assert finger_page.evaluate("() => vibrations.length") == 0


class TestRowsCloseEachOther:
    @on_page("many")
    def test_swiping_another_row_closes_the_open_one(self, finger_page):
        finger_page.finger.drag(300, 140, middle_of(finger_page, 0))
        assert row_state(finger_page, 0)["open"]

        finger_page.finger.drag(300, 140, middle_of(finger_page, 1))

        assert not row_state(finger_page, 0)["open"]
        assert row_state(finger_page, 1)["open"]

    def test_tapping_elsewhere_closes_the_open_row(self, finger_page):
        finger_page.finger.drag(300, 140, middle_of(finger_page))

        finger_page.finger.tap(finger_page.locator("#after"))

        assert not row_state(finger_page)["open"]

    @on_page("many")
    def test_scrolling_the_page_closes_the_open_row(self, finger_page):
        finger_page.finger.drag(300, 140, middle_of(finger_page))

        finger_page.mouse.wheel(0, 200)

        finger_page.wait_for_function(
            "() => !document.querySelector('.mvp-row').classList.contains('is-open')"
        )

    @on_page("scroller")
    def test_scrolling_a_container_around_the_list_closes_the_open_row(
        self, finger_page
    ):
        finger_page.evaluate(
            "() => { const box = document.getElementById('scroller');"
            " box.style.height = '160px'; box.style.overflow = 'auto'; }"
        )
        finger_page.finger.drag(300, 140, middle_of(finger_page))
        assert row_state(finger_page)["open"]

        finger_page.evaluate(
            "() => document.getElementById('scroller').scrollBy(0, 80)"
        )

        finger_page.wait_for_function(
            "() => !document.querySelector('.mvp-row').classList.contains('is-open')"
        )

    def test_escape_closes_the_open_row(self, finger_page):
        finger_page.finger.drag(300, 140, middle_of(finger_page))

        finger_page.keyboard.press("Escape")

        assert not row_state(finger_page)["open"]

    def test_escape_with_focus_inside_returns_focus_to_the_rows_content(
        self, finger_page
    ):
        finger_page.finger.drag(300, 140, middle_of(finger_page))
        finger_page.locator(".mvp-row-under [data-mvp-row-button]").first.focus()

        finger_page.keyboard.press("Escape")

        assert not row_state(finger_page)["open"]
        assert finger_page.evaluate("() => document.activeElement.id") == "link0"

    @on_page("sheet")
    def test_escape_in_a_row_in_an_open_sheet_keeps_the_sheet_open(self, finger_page):
        finger_page.locator("#holder-open").tap()
        finger_page.wait_for_function("() => document.getElementById('holder').open")
        finger_page.wait_for_timeout(600)
        finger_page.finger.drag(300, 140, middle_of(finger_page))
        assert row_state(finger_page)["open"]

        finger_page.keyboard.press("Escape")

        assert not row_state(finger_page)["open"]
        assert finger_page.evaluate("() => document.getElementById('holder').open")

    @on_page("sheet")
    def test_escape_with_no_row_open_is_left_to_the_sheet_around_the_list(
        self, finger_page
    ):
        finger_page.locator("#holder-open").tap()
        finger_page.wait_for_function("() => document.getElementById('holder').open")
        finger_page.wait_for_timeout(600)
        finger_page.finger.drag(300, 140, middle_of(finger_page))
        finger_page.keyboard.press("Escape")
        assert not row_state(finger_page)["open"]

        finger_page.keyboard.press("Escape")

        finger_page.wait_for_function("() => !document.getElementById('holder').open")


class TestSwipeLeavesTheContentAlone:
    def test_tapping_the_open_row_closes_it_and_follows_nothing(self, finger_page):
        finger_page.finger.drag(300, 140, middle_of(finger_page))

        finger_page.finger.tap(finger_page.locator("#link0"))

        assert not row_state(finger_page)["open"]
        assert finger_page.evaluate("() => location.hash") == ""

    def test_a_press_on_a_button_just_after_a_swipe_still_runs_it(self, finger_page):
        finger_page.finger.drag(300, 140, middle_of(finger_page))
        finger_page.evaluate(
            "() => document.querySelectorAll('.mvp-row, .mvp-row-under')"
            ".forEach(el => { el.style.transition = 'none'; })"
        )
        button = finger_page.locator(".mvp-row-under [data-mvp-row-button]").nth(2)
        box = button.bounding_box()

        finger_page.mouse.click(box["x"] + box["width"] / 2, box["y"] + 10)

        finger_page.wait_for_function("() => location.hash === '#ran-remove'")

    def test_a_swipe_that_ends_over_a_link_does_not_follow_it(self, finger_page):
        link = finger_page.locator("#link0").bounding_box()
        y = link["y"] + link["height"] / 2

        finger_page.finger.drag(link["x"] + 20, link["x"] - 60, y)
        # The click that ends a swipe is a real one, which a script cannot send.
        finger_page.mouse.click(link["x"] + 5, y)

        assert finger_page.evaluate("() => location.hash") == ""

    @pytest.mark.parametrize(
        ("start", "direction"),
        [(10, "rtl"), (380, "ltr")],
        ids=["left edge", "right edge"],
    )
    def test_a_touch_in_the_back_gesture_area_does_not_move_the_row(
        self, finger_page, start, direction
    ):
        # Each edge is tried with the direction that would open the row from it.
        finger_page.evaluate(
            f"() => {{ document.documentElement.dir = '{direction}'; }}"
        )
        y = middle_of(finger_page)

        finger_page.finger.drag(start, 180, y)

        assert row_state(finger_page) == {
            "open": False,
            "full": False,
            "dragging": False,
            "x": 0,
        }

    def test_a_mostly_vertical_movement_is_left_to_the_page(self, finger_page):
        y = middle_of(finger_page)
        finger_page.finger.down(200, y)
        finger_page.finger.move(190, y + 40)
        finger_page.finger.move(170, y + 90)

        assert row_state(finger_page)["dragging"] is False
        assert row_state(finger_page)["x"] == 0
        finger_page.finger.up()

    @on_page("sheet")
    def test_a_sideways_touch_on_a_sheet_item_leaves_the_row(self, finger_page):
        finger_page.locator("#holder-open").tap()
        finger_page.wait_for_function("() => document.getElementById('holder').open")
        finger_page.locator("#row0-sheet-trigger, .mvp-row-sheet-trigger").tap()
        finger_page.wait_for_function(
            "() => document.getElementById('row0-sheet').open"
        )
        item = finger_page.locator("#row0-sheet [data-mvp-row-action]").first
        box = item.bounding_box()

        finger_page.finger.drag(box["x"] + 200, box["x"] + 60, box["y"] + 10)

        assert row_state(finger_page) == {
            "open": False,
            "full": False,
            "dragging": False,
            "x": 0,
        }


class TestSwipeOnARightToLeftPage:
    def test_the_row_opens_the_mirror_way(self, finger_page):
        finger_page.evaluate("() => { document.documentElement.dir = 'rtl'; }")
        y = middle_of(finger_page)

        finger_page.finger.drag(100, 260, y)

        state = row_state(finger_page)
        assert state["open"]
        assert state["x"] == pytest.approx(-REST, abs=2)


def folded(page, index=0):
    return (
        page.locator(".mvp-row")
        .nth(index)
        .evaluate("el => el.classList.contains('is-folded')")
    )


def remember_folding(page):
    """Record whether any row was ever folded, since an undo is quick."""
    page.evaluate(
        """() => {
            window.wasFolded = false;
            new MutationObserver(() => {
              if (document.querySelector('.mvp-row.is-folded')) window.wasFolded = true;
            }).observe(document.body, {subtree: true, attributes: true,
                                       attributeFilter: ['class']});
        }"""
    )


@pytest.fixture
def desk_page(browser, live_server, request):
    """A desktop browser with a trackpad open on the swipe page the test names."""
    page = browser.new_page(viewport=DESKTOP)
    page.set_default_timeout(5000)
    page.goto(f"{live_server.url}/row-swipe/{getattr(request, 'param', 'main')}/")
    page.wait_for_selector("[data-mvp-row-ready]", state="attached")
    yield page
    page.close()


def swipe_with_trackpad(page, towards, index=0, steps=6):
    """Two fingers sideways over a row: a run of wheel events with no vertical part."""
    box = page.locator(".mvp-row").nth(index).bounding_box()
    page.mouse.move(box["x"] + 300, box["y"] + box["height"] / 2)
    for _ in range(steps):
        page.mouse.wheel(towards / steps, 0)
        page.wait_for_timeout(16)


class TestActionClosesTheRow:
    def test_tapping_an_action_runs_it_and_closes_the_row(self, finger_page):
        finger_page.finger.drag(300, 140, middle_of(finger_page))

        finger_page.finger.tap(
            finger_page.locator(".mvp-row-under [data-mvp-row-button]").nth(2)
        )

        finger_page.wait_for_function("() => location.hash === '#ran-remove'")
        finger_page.wait_for_function(
            "() => !document.querySelector('.mvp-row').classList.contains('is-open')"
        )

    def test_a_main_action_that_does_not_leave_closes_the_row_and_keeps_it(
        self, finger_page
    ):
        finger_page.finger.drag(370, 60, middle_of(finger_page))

        finger_page.wait_for_function("() => location.hash === '#ran-open'")
        finger_page.wait_for_function(
            "() => !document.querySelector('.mvp-row')"
            ".classList.contains('is-committing')"
        )
        assert row_state(finger_page)["x"] == 0
        assert not folded(finger_page)


class TestTrackpad:
    def test_a_sideways_wheel_opens_the_row_once_it_stops(self, desk_page):
        swipe_with_trackpad(desk_page, 300)

        assert row_state(desk_page)["dragging"]
        desk_page.wait_for_function(
            "() => document.querySelector('.mvp-row').classList.contains('is-open')"
        )
        assert row_state(desk_page)["x"] == pytest.approx(-REST, abs=2)

    def test_a_short_wheel_swipe_closes_again(self, desk_page):
        swipe_with_trackpad(desk_page, 60)

        desk_page.wait_for_function(
            "() => !document.querySelector('.mvp-row')"
            ".classList.contains('is-dragging')"
        )
        assert row_state(desk_page) == {
            "open": False,
            "full": False,
            "dragging": False,
            "x": 0,
        }

    def test_a_wheel_swipe_back_closes_an_open_row(self, desk_page):
        swipe_with_trackpad(desk_page, 300)
        desk_page.wait_for_function(
            "() => document.querySelector('.mvp-row').classList.contains('is-open')"
        )

        swipe_with_trackpad(desk_page, -300)

        desk_page.wait_for_function(
            "() => !document.querySelector('.mvp-row').classList.contains('is-open')"
        )

    def test_a_long_wheel_swipe_runs_the_main_action(self, desk_page):
        swipe_with_trackpad(desk_page, 1100, steps=11)

        desk_page.wait_for_function("() => location.hash === '#ran-open'")

    @pytest.mark.parametrize("desk_page", ["many"], indirect=True)
    def test_a_mostly_vertical_wheel_is_left_to_the_page(self, desk_page):
        box = desk_page.locator(".mvp-row").first.bounding_box()
        desk_page.mouse.move(box["x"] + 300, box["y"] + 20)

        desk_page.mouse.wheel(10, 120)
        desk_page.wait_for_timeout(250)

        assert row_state(desk_page)["x"] == 0
        assert desk_page.evaluate("() => scrollY") > 0


class TestRowsThatLeave:
    @on_page("leaves")
    def test_a_main_action_that_leaves_folds_the_row(self, finger_page):
        finger_page.finger.drag(370, 60, middle_of(finger_page))

        finger_page.wait_for_function("() => location.hash === '#ran-archive'")
        assert folded(finger_page)
        assert (
            finger_page.locator(".mvp-row").first.evaluate("el => el.style.height")
            == "0px"
        )

    @pytest.mark.parametrize("desk_page", ["leaves"], indirect=True)
    def test_a_leaving_action_chosen_from_the_menu_folds_the_row_too(self, desk_page):
        desk_page.locator(".mvp-row-dropdown button").first.click()

        desk_page.locator(".dropdown-content [data-mvp-row-action]").first.click()

        desk_page.wait_for_function("() => location.hash === '#ran-archive'")
        assert folded(desk_page)

    @pytest.mark.parametrize("desk_page", ["leaves"], indirect=True)
    def test_an_action_that_does_not_leave_does_not_fold_the_row(self, desk_page):
        desk_page.locator(".mvp-row-dropdown button").first.click()

        desk_page.locator(".dropdown-content [data-mvp-row-action]").nth(1).click()

        desk_page.wait_for_function("() => location.hash === '#ran-rename'")
        assert not folded(desk_page)

    @pytest.mark.parametrize("desk_page", ["leaves"], indirect=True)
    def test_a_request_that_does_not_leave_does_not_fold_the_row(self, desk_page):
        remember_folding(desk_page)
        second = desk_page.locator(".mvp-row").nth(1)
        second.locator(".mvp-row-dropdown button[aria-label^='More for']").click()

        second.locator(".dropdown-content [data-mvp-row-action]").last.click()

        desk_page.wait_for_timeout(400)
        assert not desk_page.evaluate("() => window.wasFolded")

    @on_page("leaves")
    def test_a_failing_request_puts_the_row_back(self, finger_page):
        remember_folding(finger_page)
        finger_page.finger.drag(300, 140, middle_of(finger_page))

        finger_page.finger.tap(
            finger_page.locator(".mvp-row-under [data-mvp-row-button]").nth(2)
        )

        finger_page.wait_for_function("() => window.wasFolded")
        finger_page.wait_for_function(
            "() => !document.querySelector('.mvp-row').classList.contains('is-folded')"
        )
        assert (
            finger_page.locator(".mvp-row").first.evaluate("el => el.style.height")
            == ""
        )
        assert row_state(finger_page)["x"] == 0
        assert finger_page.locator("#link-gone").is_visible()

    @on_page("leaves")
    def test_a_declined_confirmation_leaves_the_row_shown(self, finger_page):
        asked = []
        finger_page.on("dialog", lambda dialog: (asked.append(1), dialog.dismiss()))
        remember_folding(finger_page)
        finger_page.finger.drag(300, 140, middle_of(finger_page, 1))

        finger_page.finger.tap(
            finger_page.locator(".mvp-row")
            .nth(1)
            .locator("[data-mvp-row-button]")
            .first
        )

        finger_page.wait_for_timeout(400)
        assert asked
        assert not finger_page.evaluate("() => window.wasFolded")

    @on_page("confirming")
    def test_a_declined_confirmation_after_a_long_swipe_leaves_the_row_shown(
        self, finger_page
    ):
        finger_page.on("dialog", lambda dialog: dialog.dismiss())

        finger_page.finger.drag(370, 60, middle_of(finger_page))

        finger_page.wait_for_function(
            "() => !document.querySelector('.mvp-row')"
            ".classList.contains('is-committing')"
        )
        assert row_state(finger_page)["x"] == 0
        assert not folded(finger_page)
        assert finger_page.locator(".mvp-row-under").evaluate("el => el.inert")

    @on_page("leaves")
    def test_the_layer_under_a_folded_row_is_inert(self, finger_page):
        finger_page.finger.drag(370, 60, middle_of(finger_page))

        finger_page.wait_for_function("() => location.hash === '#ran-archive'")
        assert folded(finger_page)
        assert finger_page.locator(".mvp-row-under").first.evaluate("el => el.inert")

    @pytest.mark.parametrize("desk_page", ["prefixed"], indirect=True)
    def test_a_request_written_with_data_attributes_is_waited_for_too(self, desk_page):
        desk_page.on("dialog", lambda dialog: dialog.dismiss())
        remember_folding(desk_page)
        desk_page.locator(".mvp-row-dropdown button").first.click()

        desk_page.locator(".dropdown-content [data-mvp-row-action]").first.click()

        desk_page.wait_for_timeout(400)
        assert not desk_page.evaluate("() => window.wasFolded")

    @pytest.mark.parametrize("desk_page", ["removing"], indirect=True)
    def test_a_leaving_request_answered_with_nothing_removes_the_row(self, desk_page):
        desk_page.locator(".mvp-row-dropdown button").first.click()

        desk_page.locator(".dropdown-content [data-mvp-row-action]").first.click()

        desk_page.wait_for_function("() => !document.querySelector('#removing')")
        assert desk_page.locator(".mvp-row").count() == 1


def announce(page, selector, kind):
    """Raise the window event a list raises as reordering starts or ends."""
    page.evaluate(
        "([selector, kind]) => document.querySelector(selector).dispatchEvent("
        "new CustomEvent(`mvp:reorder-${kind}`, {bubbles: true}))",
        [selector, kind],
    )


class TestSwitchingSwipingOff:
    def test_a_list_switched_off_stays_shut_and_keeps_its_menu(self, finger_page):
        finger_page.evaluate("() => mvpRows.off(document.querySelector('ul.list'))")

        finger_page.finger.drag(300, 140, middle_of(finger_page))

        state = row_state(finger_page)
        assert not state["open"]
        assert state["x"] == 0
        finger_page.wait_for_timeout(450)
        finger_page.tap(".mvp-row-sheet-trigger")
        finger_page.wait_for_function(
            "() => document.getElementById('row0-sheet').open"
        )
        sheet = finger_page.locator("#row0-sheet")
        assert sheet.locator("[data-mvp-row-action]").count() == 3

    def test_a_list_switched_back_on_swipes_again(self, finger_page):
        finger_page.evaluate("() => mvpRows.off(document.querySelector('ul.list'))")
        finger_page.evaluate("() => mvpRows.on(document.querySelector('ul.list'))")

        finger_page.finger.drag(300, 140, middle_of(finger_page))

        assert row_state(finger_page)["open"]

    def test_switching_a_list_off_shuts_the_row_open_in_it(self, finger_page):
        finger_page.finger.drag(300, 140, middle_of(finger_page))
        assert row_state(finger_page)["open"]

        finger_page.evaluate("() => mvpRows.off(document.querySelector('ul.list'))")

        state = row_state(finger_page)
        assert not state["open"]
        assert state["x"] == 0

    def test_the_interface_shuts_the_open_row(self, finger_page):
        finger_page.finger.drag(300, 140, middle_of(finger_page))
        assert row_state(finger_page)["open"]

        finger_page.evaluate("() => mvpRows.shut()")

        assert not row_state(finger_page)["open"]

    def test_it_is_the_one_global(self, finger_page):
        assert finger_page.evaluate("() => Object.keys(window.mvpRows).sort()") == [
            "off",
            "on",
            "shut",
        ]


class TestReorderAnnouncements:
    @on_page("reorder")
    def test_a_real_lists_mode_shuts_the_open_row_and_stops_swiping_until_it_ends(
        self, finger_page
    ):
        finger_page.finger.drag(300, 140, middle_of(finger_page))
        assert row_state(finger_page)["open"]

        finger_page.wait_for_timeout(450)  # the click that ends a swipe is held back
        finger_page.click("#start")

        assert not row_state(finger_page)["open"]
        finger_page.finger.drag(300, 140, middle_of(finger_page))
        assert row_state(finger_page)["x"] == 0

        finger_page.click("#end")

        finger_page.finger.drag(300, 140, middle_of(finger_page))
        assert row_state(finger_page)["open"]

    @on_page("reorder")
    def test_the_menu_still_offers_every_action_during_the_mode(self, finger_page):
        finger_page.click("#start")

        finger_page.tap(".mvp-row-sheet-trigger")

        finger_page.wait_for_function(
            "() => document.getElementById('row0-sheet').open"
        )
        sheet = finger_page.locator("#row0-sheet")
        assert sheet.locator("[data-mvp-row-action]").count() == 3

    @on_page("reorder")
    def test_a_list_already_in_its_mode_does_not_swipe(self, finger_page):
        finger_page.evaluate(
            "() => document.getElementById('steps').setAttribute('data-reordering', '')"
        )

        finger_page.finger.drag(300, 140, middle_of(finger_page))

        assert row_state(finger_page)["x"] == 0

    @on_page("nested")
    def test_a_start_shuts_the_row_open_in_that_list(self, finger_page):
        finger_page.finger.drag(300, 140, middle_of(finger_page))
        assert row_state(finger_page)["open"]

        announce(finger_page, "#inner", "start")

        assert not row_state(finger_page)["open"]

    @on_page("nested")
    def test_a_nested_pair_leaves_swiping_off_until_the_outer_pair_ends(
        self, finger_page
    ):
        announce(finger_page, "#outer", "start")
        announce(finger_page, "#inner", "start")
        announce(finger_page, "#inner", "end")

        finger_page.finger.drag(300, 140, middle_of(finger_page))
        assert row_state(finger_page)["x"] == 0

        announce(finger_page, "#outer", "end")

        finger_page.finger.drag(300, 140, middle_of(finger_page))
        assert row_state(finger_page)["open"]

    @on_page("nested")
    def test_a_stop_without_a_start_does_not_switch_off_the_developers_flag(
        self, finger_page
    ):
        finger_page.evaluate("() => mvpRows.off(document.getElementById('outer'))")

        announce(finger_page, "#inner", "end")
        finger_page.finger.drag(300, 140, middle_of(finger_page))

        assert row_state(finger_page)["x"] == 0

    @on_page("nested")
    def test_a_start_abandons_a_swipe_in_progress_in_that_list(self, finger_page):
        y = middle_of(finger_page)
        finger_page.finger.down(300, y)
        finger_page.finger.pull(300, 200, y)

        announce(finger_page, "#inner", "start")
        finger_page.finger.pull(200, 140, y)
        finger_page.finger.up()

        state = row_state(finger_page)
        assert not state["open"]
        assert state["x"] == 0


class TestRowsThatArriveByHtmx:
    @on_page("swap")
    def test_new_rows_swipe_and_open_their_menus_unaided(self, finger_page):
        finger_page.click("#reload")
        finger_page.wait_for_function(
            "() => document.querySelectorAll('.mvp-row[data-mvp-row-ready]').length"
            " === 2"
        )

        finger_page.finger.drag(300, 140, middle_of(finger_page, 1))
        assert row_state(finger_page, 1)["open"]

        finger_page.mouse.click(5, 5)
        finger_page.locator(".mvp-row-dropdown button").nth(1).dispatch_event("click")
        panel = finger_page.locator(".mvp-row-dropdown .dropdown-content").nth(1)
        finger_page.wait_for_function(
            "() => document.querySelectorAll('.dropdown-content:popover-open')"
            ".length === 1"
        )
        assert panel.evaluate("el => el.matches(':popover-open')")


def hint_context(browser, **options):
    """A browser that has never shown this site's rows: nothing is remembered."""
    context = browser.new_context(**options)
    context.add_init_script(WATCH_HINT)
    return context


def open_swipe_page(context, live_server, name="main"):
    page = context.new_page()
    page.set_default_timeout(5000)
    page.goto(f"{live_server.url}/row-swipe/{name}/")
    page.wait_for_function("() => window.Alpine && Alpine.version")
    page.wait_for_selector("[data-mvp-row-ready]", state="attached")
    return page


def remembered(page):
    return page.evaluate("() => localStorage.getItem('mvp-row-hinted')")


class TestFirstTimeNudge:
    def test_the_first_row_is_nudged_open_and_back_once_and_never_again(
        self, browser, live_server
    ):
        context = hint_context(browser, viewport=PHONE, has_touch=True, is_mobile=True)
        page = open_swipe_page(context, live_server)
        page.wait_for_function(
            "() => document.querySelector('.mvp-row').classList.contains('is-hinting')"
            " && parseFloat(document.querySelector('.mvp-row').style"
            ".getPropertyValue('--mvp-row-x') || '0') < 0"
        )

        shown = row_state(page)
        assert -4.5 * 16 <= shown["x"] < 0
        assert not shown["open"]
        page.wait_for_function(
            "() => !document.querySelector('.mvp-row').classList.contains('is-hinting')"
        )
        assert row_state(page)["x"] == 0
        assert page.locator(".mvp-row-under").evaluate("el => el.inert")
        assert remembered(page) is not None

        page.reload()
        page.wait_for_selector("[data-mvp-row-ready]", state="attached")
        page.wait_for_timeout(2500)

        assert not page.evaluate("() => window.wasHinting")
        context.close()

    def test_only_the_first_row_is_nudged(self, browser, live_server):
        context = hint_context(browser, viewport=PHONE, has_touch=True, is_mobile=True)
        page = open_swipe_page(context, live_server, "many")
        page.wait_for_function(
            "() => document.querySelector('.mvp-row').classList.contains('is-hinting')"
        )

        assert (
            not page.locator(".mvp-row")
            .nth(1)
            .evaluate("el => el.classList.contains('is-hinting')")
        )
        context.close()

    def test_a_mouse_is_not_nudged(self, browser, live_server):
        context = hint_context(browser, viewport=DESKTOP)
        page = open_swipe_page(context, live_server)

        page.wait_for_timeout(2500)

        assert not page.evaluate("() => window.wasHinting")
        assert remembered(page) is None
        context.close()

    def test_a_row_nobody_can_see_gives_no_nudge_and_remembers_nothing(
        self, browser, live_server
    ):
        context = hint_context(browser, viewport=PHONE, has_touch=True, is_mobile=True)
        page = open_swipe_page(context, live_server, "hidden")

        page.wait_for_timeout(2500)

        assert not page.evaluate("() => window.wasHinting")
        assert remembered(page) is None
        context.close()

    def test_no_row_in_view_gives_no_nudge_and_remembers_nothing(
        self, browser, live_server
    ):
        context = hint_context(browser, viewport=PHONE, has_touch=True, is_mobile=True)
        page = open_swipe_page(context, live_server, "below")

        page.wait_for_timeout(2500)

        assert not page.evaluate("() => window.wasHinting")
        assert remembered(page) is None
        context.close()

    def test_a_row_that_arrives_by_htmx_is_nudged_when_none_was(
        self, browser, live_server
    ):
        context = hint_context(browser, viewport=PHONE, has_touch=True, is_mobile=True)
        page = open_swipe_page(context, live_server, "swap")
        page.wait_for_function("() => window.wasHinting")
        page.evaluate("() => localStorage.removeItem('mvp-row-hinted')")
        page.evaluate("() => { window.wasHinting = false; }")
        page.wait_for_function(
            "() => !document.querySelector('.mvp-row').classList.contains('is-hinting')"
        )

        page.click("#reload")

        page.wait_for_function("() => window.wasHinting")
        context.close()

    def test_a_blocked_store_does_not_stop_the_page(self, browser, live_server):
        context = hint_context(browser, viewport=PHONE, has_touch=True, is_mobile=True)
        context.add_init_script(
            "Object.defineProperty(window, 'localStorage',"
            " {get() { throw new Error('blocked'); }});"
        )
        page = open_swipe_page(context, live_server)
        page.errors = []
        page.on("pageerror", lambda error: page.errors.append(str(error)))

        page.wait_for_timeout(2500)

        assert page.errors == []
        assert not page.evaluate("() => window.wasHinting")
        context.close()


class TestReducedMotion:
    def test_the_rows_transitions_are_effectively_instant(self, browser, live_server):
        context = hint_context(
            browser,
            viewport=PHONE,
            has_touch=True,
            is_mobile=True,
            reduced_motion="reduce",
        )
        context.add_init_script(REMEMBER_HINT)
        page = open_swipe_page(context, live_server, "leaves")

        durations = page.evaluate(
            """() => [
              '.mvp-row', '.mvp-row > .mvp-row-face', '.mvp-row > .mvp-row-under',
              '.mvp-row-button',
            ].map(selector => {
              const style = getComputedStyle(document.querySelector(selector));
              return style.transitionDuration.split(',')
                .map(value => parseFloat(value));
            }).flat()"""
        )

        assert max(durations) <= 0.02
        context.close()

    def test_a_row_ends_in_the_right_state_when_it_opens_and_folds(
        self, browser, live_server
    ):
        context = hint_context(
            browser,
            viewport=PHONE,
            has_touch=True,
            is_mobile=True,
            reduced_motion="reduce",
        )
        context.add_init_script(REMEMBER_HINT)
        page = open_swipe_page(context, live_server, "leaves")
        page.finger = Finger(page)

        page.finger.drag(300, 140, middle_of(page))
        assert row_state(page)["open"]
        page.evaluate("() => mvpRows.shut()")
        assert row_state(page)["x"] == 0
        page.finger.drag(370, 60, middle_of(page))

        page.wait_for_function("() => location.hash === '#ran-archive'")
        assert folded(page)
        page.wait_for_function(
            "() => getComputedStyle(document.querySelector('.mvp-row')).opacity === '0'"
        )
        context.close()

    def test_the_nudge_jumps_and_ends_closed(self, browser, live_server):
        context = hint_context(
            browser,
            viewport=PHONE,
            has_touch=True,
            is_mobile=True,
            reduced_motion="reduce",
        )
        page = open_swipe_page(context, live_server)
        page.wait_for_function("() => window.wasHinting")

        page.wait_for_function(
            "() => !document.querySelector('.mvp-row').classList.contains('is-hinting')"
        )

        state = row_state(page)
        assert state["x"] == 0
        assert not state["open"]
        context.close()
