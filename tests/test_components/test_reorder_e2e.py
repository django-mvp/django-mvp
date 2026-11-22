"""The reorderable list in a real browser: dragging, the buttons, the destinations.

Whether a row follows the pointer and which rows make room is computed layout
and event behaviour, so only a browser can settle it. Each case loads a
test-only page, ``/reorder-test/``, drawn at desktop width.
"""

import json

import pytest
from django.http import HttpResponse, JsonResponse
from django.template import engines
from django.urls import path
from django_cotton.compiler_regex import CottonCompiler
from playwright.sync_api import expect

from demo import urls as demo_urls
from demo.models import Project
from mvp.ordering import save_order
from tests.conftest import requires_browser, urlconf_of
from tests.factories import ProjectFactory, ProjectTaskFactory

pytestmark = [pytest.mark.e2e, requires_browser]

VIEWPORT = {"width": 1280, "height": 900}

PAGE = """
{% extends "mvp/base.html" %}
{% block content %}
<c-mvp.reorder id="steps" label="Steps">
  <c-mvp.reorder.row value="a" label="Alpha">Alpha</c-mvp.reorder.row>
  <c-mvp.reorder.row value="b" label="Beta">Beta</c-mvp.reorder.row>
  <c-mvp.reorder.row value="c" label="Gamma">Gamma</c-mvp.reorder.row>
</c-mvp.reorder>
{% endblock %}
"""


FORM_PAGE = """
{% extends "mvp/base.html" %}
{% block content %}
<form id="save" method="post" action="/reorder-test/echo/">
  {% csrf_token %}
  <c-mvp.reorder id="steps" label="Steps" form name="order">
    <c-mvp.reorder.row value="a" label="Alpha">Alpha</c-mvp.reorder.row>
    <c-mvp.reorder.row value="b" label="Beta">Beta</c-mvp.reorder.row>
    <c-mvp.reorder.row value="c" label="Gamma">Gamma</c-mvp.reorder.row>
  </c-mvp.reorder>
  <button type="submit" id="submit">Save</button>
</form>
{% endblock %}
"""

TWO_PAGE = """
{% extends "mvp/base.html" %}
{% block content %}
<form id="save" method="post" action="/reorder-test/echo/">
  {% csrf_token %}
  <c-mvp.reorder id="steps" label="Steps" form>
    <c-mvp.reorder.row value="a" label="Alpha">Alpha</c-mvp.reorder.row>
    <c-mvp.reorder.row value="b" label="Beta">Beta</c-mvp.reorder.row>
    <c-mvp.reorder.row value="c" label="Gamma">Gamma</c-mvp.reorder.row>
  </c-mvp.reorder>
  <c-mvp.reorder id="others" label="Others" form>
    <c-mvp.reorder.row value="x" label="Ex">Ex</c-mvp.reorder.row>
    <c-mvp.reorder.row value="y" label="Why">Why</c-mvp.reorder.row>
  </c-mvp.reorder>
</form>
{% endblock %}
"""

SINGLE_PAGE = """
{% extends "mvp/base.html" %}
{% block content %}
<c-mvp.reorder id="steps" label="Steps">
  <c-mvp.reorder.row value="a" label="Alpha">Alpha</c-mvp.reorder.row>
</c-mvp.reorder>
<c-mvp.reorder id="empty" label="Nothing"></c-mvp.reorder>
{% endblock %}
"""

TALL_PAGE = """
{% extends "mvp/base.html" %}
{% block content %}
<c-mvp.reorder id="steps" label="Steps">
  <c-mvp.reorder.row value="a" label="Alpha">Alpha</c-mvp.reorder.row>
  <c-mvp.reorder.row value="b" label="Beta">Beta</c-mvp.reorder.row>
  <c-mvp.reorder.row value="c" label="Gamma">Gamma</c-mvp.reorder.row>
</c-mvp.reorder>
<div style="height: 3000px"></div>
{% endblock %}
"""

ROWS = """
<c-mvp.reorder.row value="p" label="Pee">Pee</c-mvp.reorder.row>
<c-mvp.reorder.row value="q" label="Queue">Queue</c-mvp.reorder.row>
<c-mvp.reorder.row value="r" label="Are">Are</c-mvp.reorder.row>
"""

POST_LIST = """
<c-mvp.reorder id="steps" label="Steps" url="/reorder-test/save/{{ project.pk }}/" data-answer="{{ answered }}">
  {% for task in tasks %}
    <c-mvp.reorder.row value="{{ task.pk }}" label="{{ task.title }}">{{ task.title }}</c-mvp.reorder.row>
  {% endfor %}
</c-mvp.reorder>
"""

POST_PAGE = (
    '{% extends "mvp/base.html" %}{% block content %}' + POST_LIST + "{% endblock %}"
)


def render_page(source, request, **context):
    """Render a Cotton page source with the request."""
    template = engines["django"].from_string(CottonCompiler().process(source))
    return HttpResponse(template.render(context, request))


def reorder_test_page(request):
    """Draw the plain test page."""
    return render_page(PAGE, request)


def single_page(request):
    """Draw a list with one row and a list with none."""
    return render_page(SINGLE_PAGE, request)


def tall_page(request):
    """Draw the plain list above a stretch of page that scrolls."""
    return render_page(TALL_PAGE, request)


def form_page(request):
    """Draw the page whose list hands its order to a form."""
    return render_page(FORM_PAGE, request)


def two_page(request):
    """Draw the page with two lists."""
    return render_page(TWO_PAGE, request)


def rows(request):
    """Answer with three rows, as a swap of a list's contents would."""
    return render_page(ROWS, request)


def echo(request):
    """Answer with the identifiers the form delivered, in order."""
    return JsonResponse({"order": request.POST.getlist("order")})


def post_page(request, project_id):
    """Draw the page whose list posts its order."""
    project = Project.objects.get(pk=project_id)
    return render_page(
        POST_PAGE, request, project=project, tasks=project.tasks.all(), answered=""
    )


def save(request, project_id):
    """Store a posted order and answer with the list drawn again."""
    project = Project.objects.get(pk=project_id)
    posts = request.session.setdefault("posts", [])
    posts.append(request.POST.getlist("order"))
    save_order(project.tasks.all(), request.POST.getlist("order"))
    html = (
        engines["django"]
        .from_string(CottonCompiler().process(POST_LIST))
        .render(
            {"project": project, "tasks": project.tasks.all(), "answered": "yes"},
            request,
        )
    )
    return HttpResponse(html)


@pytest.fixture(autouse=True)
def reorder_test_urls(settings):
    settings.ROOT_URLCONF = urlconf_of(
        path("reorder-test/", reorder_test_page),
        path("reorder-test/single/", single_page),
        path("reorder-test/tall/", tall_page),
        path("reorder-test/form/", form_page),
        path("reorder-test/two/", two_page),
        path("reorder-test/rows/", rows),
        path("reorder-test/echo/", echo),
        path("reorder-test/post/<int:project_id>/", post_page),
        path("reorder-test/save/<int:project_id>/", save),
        *demo_urls.urlpatterns,
    )


def open_page(page, live_server):
    page.set_default_timeout(5000)
    page.set_viewport_size(VIEWPORT)
    page.goto(f"{live_server.url}/reorder-test/")
    page.wait_for_function("window.Alpine !== undefined")


def values(page, root="#steps"):
    """The rows' identifiers in document order."""
    return page.eval_on_selector_all(
        f"{root} [data-mvp-reorder-row]",
        "rows => rows.map(row => row.dataset.mvpReorderValue)",
    )


def drag(page, source, target, below=True, grab="[data-mvp-reorder-handle]"):
    """Drag the row ``source`` by ``grab`` until it is over the row ``target``."""
    start = page.locator(f'#steps [data-mvp-reorder-value="{source}"] {grab}')
    end = page.locator(f'#steps [data-mvp-reorder-value="{target}"]').bounding_box()
    box = start.bounding_box()
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.down()
    y = end["y"] + end["height"] * (0.75 if below else 0.25)
    page.mouse.move(box["x"] + box["width"] / 2, y, steps=12)
    page.mouse.up()


class TestDraggingARow:
    def test_dragging_a_row_by_its_handle_moves_it_and_the_rows_it_passed(
        self, page, live_server
    ):
        open_page(page, live_server)

        drag(page, "a", "c")

        assert values(page) == ["b", "c", "a"]

    def test_dragging_from_outside_the_handle_starts_nothing(self, page, live_server):
        open_page(page, live_server)

        drag(page, "a", "c", grab="div")

        assert values(page) == ["a", "b", "c"]


class TestMoveButtons:
    def test_the_down_button_swaps_a_row_with_the_next_one(self, page, live_server):
        open_page(page, live_server)

        page.locator(
            '#steps [data-mvp-reorder-value="a"] [data-mvp-reorder-down]'
        ).click()

        assert values(page) == ["b", "a", "c"]

    def test_the_up_button_swaps_a_row_with_the_previous_one(self, page, live_server):
        open_page(page, live_server)

        page.locator(
            '#steps [data-mvp-reorder-value="c"] [data-mvp-reorder-up]'
        ).click()

        assert values(page) == ["a", "c", "b"]

    def test_the_first_rows_up_button_does_nothing(self, page, live_server):
        open_page(page, live_server)

        page.locator(
            '#steps [data-mvp-reorder-value="a"] [data-mvp-reorder-up]'
        ).dispatch_event("click")

        assert values(page) == ["a", "b", "c"]

    def test_the_controls_show_once_the_list_is_active(self, page, live_server):
        open_page(page, live_server)

        hidden = page.eval_on_selector_all(
            "#steps [data-mvp-reorder-up], #steps [data-mvp-reorder-handle]",
            "els => els.map(el => el.hidden)",
        )

        assert hidden == [False] * 6


class TestFormDestination:
    def test_a_form_submitted_after_moves_delivers_the_order_under_the_name(
        self, page, live_server
    ):
        page.set_default_timeout(5000)
        page.set_viewport_size(VIEWPORT)
        page.goto(f"{live_server.url}/reorder-test/form/")
        page.wait_for_function("window.Alpine !== undefined")

        drag(page, "a", "c")
        page.locator(
            '#steps [data-mvp-reorder-value="c"] [data-mvp-reorder-up]'
        ).click()
        with page.expect_navigation():
            page.click("#submit")

        assert json.loads(page.inner_text("body"))["order"] == ["c", "b", "a"]


@pytest.mark.django_db(transaction=True)
class TestUrlDestination:
    @pytest.fixture
    def project(self):
        project = ProjectFactory()
        for title in ("one", "two", "three"):
            ProjectTaskFactory(project=project, title=title)
        project.tasks.update(position=0)
        for index, task in enumerate(project.tasks.order_by("pk")):
            task.position = index
            task.save()
        return project

    def open_posting_page(self, page, live_server, project):
        page.set_default_timeout(5000)
        page.set_viewport_size(VIEWPORT)
        page.goto(f"{live_server.url}/reorder-test/post/{project.pk}/")
        page.wait_for_function("window.Alpine !== undefined")

    def test_a_move_posts_the_order_and_the_answer_replaces_the_list(
        self, page, live_server, project
    ):
        self.open_posting_page(page, live_server, project)
        first = project.tasks.order_by("position").first()

        page.locator(
            f'#steps [data-mvp-reorder-value="{first.pk}"] [data-mvp-reorder-down]'
        ).click()

        page.wait_for_selector("#steps[data-answer=yes]")
        assert [t.title for t in project.tasks.order_by("position")] == [
            "two",
            "one",
            "three",
        ]

    def test_the_posted_order_is_in_the_rows_order(self, page, live_server, project):
        self.open_posting_page(page, live_server, project)
        last = project.tasks.order_by("position").last()

        page.locator(
            f'#steps [data-mvp-reorder-value="{last.pk}"] [data-mvp-reorder-up]'
        ).click()
        page.wait_for_selector("#steps[data-answer=yes]")

        ids = [t.pk for t in project.tasks.order_by("position")]
        assert ids[1] == last.pk

    def test_the_buttons_carry_ids_built_from_the_list_and_the_row(
        self, page, live_server, project
    ):
        self.open_posting_page(page, live_server, project)
        first = project.tasks.order_by("position").first()

        ids = page.eval_on_selector_all(
            f'#steps [data-mvp-reorder-value="{first.pk}"] button',
            "b => b.map(x => x.id)",
        )

        assert ids == [f"steps-{first.pk}-up", f"steps-{first.pk}-down"]


class TestNoDestination:
    def test_a_list_with_neither_destination_sends_nothing(self, page, live_server):
        open_page(page, live_server)
        posts = []
        page.on("request", lambda r: posts.append(r) if r.method == "POST" else None)

        drag(page, "a", "c")
        page.locator(
            '#steps [data-mvp-reorder-value="b"] [data-mvp-reorder-down]'
        ).click()
        page.wait_for_timeout(300)

        assert posts == []


class TestSeveralLists:
    def test_reordering_one_list_leaves_the_other_alone(self, page, live_server):
        page.set_default_timeout(5000)
        page.set_viewport_size(VIEWPORT)
        page.goto(f"{live_server.url}/reorder-test/two/")
        page.wait_for_function("window.Alpine !== undefined")
        before = page.eval_on_selector_all(
            "#others input[type=hidden]", "i => i.map(x => x.name + '=' + x.value)"
        )

        drag(page, "a", "c")
        page.locator(
            '#steps [data-mvp-reorder-value="b"] [data-mvp-reorder-down]'
        ).click()

        assert values(page) != ["a", "b", "c"]
        assert values(page, "#others") == ["x", "y"]
        assert (
            page.eval_on_selector_all(
                "#others input[type=hidden]", "i => i.map(x => x.name + '=' + x.value)"
            )
            == before
        )


class TestRowsAddedAfterLoad:
    APPEND = """
        () => {
          const list = document.querySelector("#steps [data-mvp-reorder-list]");
          const row = list.firstElementChild.cloneNode(true);
          row.dataset.mvpReorderValue = "z";
          row.querySelector("input").value = "z";
          list.append(row);
        }
    """

    def test_an_appended_row_can_be_dragged_and_moved_with_its_buttons(
        self, page, live_server
    ):
        open_page(page, live_server)

        page.evaluate(self.APPEND)
        drag(page, "z", "a", below=False)
        assert values(page) == ["z", "a", "b", "c"]
        page.locator(
            '#steps [data-mvp-reorder-value="z"] [data-mvp-reorder-down]'
        ).click()

        assert values(page) == ["a", "z", "b", "c"]

    def test_the_edge_buttons_follow_an_appended_row(self, page, live_server):
        open_page(page, live_server)

        page.evaluate(self.APPEND)

        last = page.locator(
            '#steps [data-mvp-reorder-value="z"] [data-mvp-reorder-down]'
        )
        previous_last = page.locator(
            '#steps [data-mvp-reorder-value="c"] [data-mvp-reorder-down]'
        )
        expect(last).to_have_attribute("aria-disabled", "true")
        expect(previous_last).not_to_have_attribute("aria-disabled", "true")

    def test_rows_arriving_in_a_swap_of_the_lists_contents_work(
        self, page, live_server
    ):
        open_page(page, live_server)

        page.evaluate(
            """() => htmx.ajax("GET", "/reorder-test/rows/",
                 {target: "#steps [data-mvp-reorder-list]", swap: "innerHTML"})"""
        )
        page.wait_for_selector('#steps [data-mvp-reorder-value="p"]')
        page.locator(
            '#steps [data-mvp-reorder-value="r"] [data-mvp-reorder-up]'
        ).click()
        drag(page, "p", "r")

        assert values(page) == ["r", "p", "q"]
        first = page.locator(
            "#steps [data-mvp-reorder-row] [data-mvp-reorder-up]"
        ).first
        expect(first).to_have_attribute("aria-disabled", "true")


PHONE = {"width": 390, "height": 700}

VIBRATE_STUB = """
window.vibrations = [];
navigator.vibrate = (pattern) => { window.vibrations.push(pattern); return true; };
"""


def scroll_y(page):
    return page.evaluate("window.scrollY")


def centre(page, selector):
    box = page.locator(selector).bounding_box()
    return box["x"] + box["width"] / 2, box["y"] + box["height"] / 2


class Finger:
    """Trusted touches sent through the browser's DevTools protocol."""

    def __init__(self, page):
        self.session = page.context.new_cdp_session(page)

    def send(self, kind, *points):
        self.session.send(
            "Input.dispatchTouchEvent",
            {
                "type": kind,
                "touchPoints": [
                    {"x": x, "y": y, "id": index} for index, (x, y) in enumerate(points)
                ],
            },
        )

    def drag(self, start, end, steps=12):
        """Press at ``start`` and move to ``end`` in even steps, then lift."""
        self.send("touchStart", start)
        for step in range(1, steps + 1):
            x = start[0] + (end[0] - start[0]) * step / steps
            y = start[1] + (end[1] - start[1]) * step / steps
            self.send("touchMove", (x, y))
        self.send("touchEnd")


@pytest.fixture
def touch_page(browser, live_server):
    context = browser.new_context(has_touch=True, viewport=PHONE)
    page = context.new_page()
    page.set_default_timeout(5000)
    page.add_init_script(VIBRATE_STUB)
    page.goto(f"{live_server.url}/reorder-test/tall/")
    page.wait_for_function("window.Alpine !== undefined")
    yield page
    context.close()


def handle(value):
    return f'#steps [data-mvp-reorder-value="{value}"] [data-mvp-reorder-handle]'


class TestTouchDragging:
    def test_a_touch_drag_from_the_handle_moves_the_row_and_the_page_stays(
        self, touch_page
    ):
        end = centre(touch_page, '#steps [data-mvp-reorder-value="c"]')

        Finger(touch_page).drag(centre(touch_page, handle("a")), (end[0], end[1] + 20))

        assert values(touch_page) == ["b", "c", "a"]
        assert scroll_y(touch_page) == 0

    def test_a_touch_drag_from_anywhere_else_scrolls_the_page(self, touch_page):
        title = centre(touch_page, '#steps [data-mvp-reorder-value="b"] div')

        Finger(touch_page).drag(title, (title[0], title[1] - 300))

        assert values(touch_page) == ["a", "b", "c"]
        assert scroll_y(touch_page) > 0

    def test_a_drag_from_a_handle_calls_vibrate(self, touch_page):
        end = centre(touch_page, '#steps [data-mvp-reorder-value="c"]')

        Finger(touch_page).drag(centre(touch_page, handle("a")), end)

        assert touch_page.evaluate("window.vibrations.length") == 1


class TestStartingADrag:
    def test_a_right_click_on_a_handle_starts_no_drag(self, page, live_server):
        open_page(page, live_server)
        x, y = centre(page, handle("a"))
        end = page.locator('#steps [data-mvp-reorder-value="c"]').bounding_box()

        page.mouse.move(x, y)
        page.mouse.down(button="right")
        page.mouse.move(x, end["y"] + end["height"] * 0.75, steps=12)
        page.mouse.up(button="right")

        assert values(page) == ["a", "b", "c"]

    def test_a_second_finger_on_a_handle_starts_no_drag(self, touch_page):
        resting = centre(touch_page, '#steps [data-mvp-reorder-value="c"] div')
        start = centre(touch_page, handle("a"))
        end = centre(touch_page, '#steps [data-mvp-reorder-value="c"]')
        finger = Finger(touch_page)

        finger.send("touchStart", resting)
        finger.send("touchStart", resting, start)
        for step in range(1, 9):
            lower = (start[0], start[1] + (end[1] - start[1]) * step / 8)
            finger.send("touchMove", resting, lower)
        finger.send("touchEnd")

        assert values(touch_page) == ["a", "b", "c"]
        assert touch_page.evaluate("window.vibrations.length") == 0


class TestEdgeScrolling:
    def test_the_page_scrolls_while_the_pointer_rests_near_the_bottom(
        self, touch_page, live_server
    ):
        touch_page.set_viewport_size({"width": 1280, "height": 400})
        x, y = centre(touch_page, handle("a"))

        touch_page.mouse.move(x, y)
        touch_page.mouse.down()
        touch_page.mouse.move(x, 395, steps=10)
        touch_page.wait_for_timeout(600)
        scrolled = scroll_y(touch_page)
        touch_page.mouse.up()

        assert scrolled > 0


class TestCancellingADrag:
    @pytest.fixture
    def project(self):
        project = ProjectFactory()
        for title in ("one", "two", "three"):
            ProjectTaskFactory(project=project, title=title)
        for index, task in enumerate(project.tasks.order_by("pk")):
            task.position = index
            task.save()
        return project

    def hold_over_last(self, page):
        x, y = centre(page, handle("a"))
        end = page.locator('#steps [data-mvp-reorder-value="c"]').bounding_box()
        page.mouse.move(x, y)
        page.mouse.down()
        page.mouse.move(x, end["y"] + end["height"] * 0.75, steps=12)
        assert page.eval_on_selector_all(
            "#steps [data-mvp-reorder-row]:not(.mvp-reorder-held)",
            "rows => rows.map(row => row.dataset.mvpReorderValue)",
        ) == ["b", "c", "a"]

    def test_escape_returns_the_row_to_where_it_started(self, page, live_server):
        open_page(page, live_server)

        self.hold_over_last(page)
        page.keyboard.press("Escape")
        page.mouse.up()

        assert values(page) == ["a", "b", "c"]

    def test_a_cancelled_drag_can_be_followed_by_another(self, page, live_server):
        open_page(page, live_server)

        self.hold_over_last(page)
        page.keyboard.press("Escape")
        page.mouse.up()
        drag(page, "b", "c")

        assert values(page) == ["a", "c", "b"]

    @pytest.mark.django_db(transaction=True)
    def test_a_cancelled_drag_posts_nothing(self, page, live_server, project):
        page.set_default_timeout(5000)
        page.set_viewport_size(VIEWPORT)
        page.goto(f"{live_server.url}/reorder-test/post/{project.pk}/")
        page.wait_for_function("window.Alpine !== undefined")
        posts = []
        page.on("request", lambda r: posts.append(r) if r.method == "POST" else None)
        first = project.tasks.order_by("position").first()
        x, y = centre(
            page,
            f'#steps [data-mvp-reorder-value="{first.pk}"] [data-mvp-reorder-handle]',
        )

        page.mouse.move(x, y)
        page.mouse.down()
        page.mouse.move(x, y + 140, steps=12)
        page.keyboard.press("Escape")
        page.mouse.up()
        page.wait_for_timeout(300)

        assert posts == []


class TestDroppingOutsideTheList:
    def test_a_row_let_go_outside_the_list_stays_where_the_gap_was(
        self, page, live_server
    ):
        open_page(page, live_server)
        x, y = centre(page, handle("a"))
        end = page.locator('#steps [data-mvp-reorder-value="c"]').bounding_box()

        page.mouse.move(x, y)
        page.mouse.down()
        page.mouse.move(x, end["y"] + end["height"] * 0.75, steps=12)
        page.mouse.move(1270, 880, steps=6)
        page.mouse.up()

        assert values(page) == ["b", "c", "a"]


def button(value, which):
    return f'#steps [data-mvp-reorder-value="{value}"] [data-mvp-reorder-{which}]'


class TestButtonEdges:
    def test_the_first_rows_up_and_the_last_rows_down_are_disabled(
        self, page, live_server
    ):
        open_page(page, live_server)

        expect(page.locator(button("a", "up"))).to_have_attribute(
            "aria-disabled", "true"
        )
        expect(page.locator(button("c", "down"))).to_have_attribute(
            "aria-disabled", "true"
        )
        expect(page.locator(button("a", "down"))).not_to_have_attribute(
            "aria-disabled", "true"
        )
        expect(page.locator(button("c", "up"))).not_to_have_attribute(
            "aria-disabled", "true"
        )

    def test_the_last_rows_down_button_does_nothing(self, page, live_server):
        open_page(page, live_server)

        page.locator(button("c", "down")).dispatch_event("click")

        assert values(page) == ["a", "b", "c"]

    def test_a_moved_row_takes_the_edge_state_of_its_new_place(self, page, live_server):
        open_page(page, live_server)

        page.locator(button("a", "down")).click()

        expect(page.locator(button("b", "up"))).to_have_attribute(
            "aria-disabled", "true"
        )
        expect(page.locator(button("a", "up"))).not_to_have_attribute(
            "aria-disabled", "true"
        )


class TestFocusAndAnnouncement:
    def test_focus_stays_on_the_button_that_was_used(self, page, live_server):
        open_page(page, live_server)

        page.locator(button("a", "down")).click()

        expect(page.locator(button("a", "down"))).to_be_focused()

    def test_a_move_is_announced_in_a_live_region_with_its_new_position(
        self, page, live_server
    ):
        open_page(page, live_server)
        region = page.locator("#steps [role=status]")
        expect(region).to_have_text("")

        page.locator(button("a", "down")).click()

        text = region.text_content()
        assert "2" in text and "3" in text

    def test_the_live_region_is_hidden_from_sight(self, page, live_server):
        open_page(page, live_server)

        box = page.locator("#steps [role=status]").bounding_box()

        assert box["width"] <= 1 and box["height"] <= 1

    def test_a_move_the_buttons_refuse_announces_nothing(self, page, live_server):
        open_page(page, live_server)

        page.locator(button("a", "up")).dispatch_event("click")

        expect(page.locator("#steps [role=status]")).to_have_text("")

    def test_a_cancelled_drag_announces_nothing(self, page, live_server):
        open_page(page, live_server)
        x, y = centre(page, handle("a"))

        page.mouse.move(x, y)
        page.mouse.down()
        page.mouse.move(x, y + 120, steps=12)
        page.keyboard.press("Escape")
        page.mouse.up()

        expect(page.locator("#steps [role=status]")).to_have_text("")


class TestKeyboard:
    def test_tab_reaches_both_buttons_of_every_row(self, page, live_server):
        open_page(page, live_server)
        page.locator(button("a", "up")).focus()

        reached = []
        for _ in range(6):
            reached.append(
                page.evaluate(
                    """() => {
                      const el = document.activeElement;
                      const row = el.closest("[data-mvp-reorder-row]");
                      const kind = el.hasAttribute("data-mvp-reorder-up") ? "up" : "down";
                      return row.dataset.mvpReorderValue + kind;
                    }"""
                )
            )
            page.keyboard.press("Tab")

        assert reached == ["aup", "adown", "bup", "bdown", "cup", "cdown"]

    @pytest.mark.parametrize("key", ["Enter", "Space"])
    def test_enter_and_space_use_a_button(self, page, live_server, key):
        open_page(page, live_server)
        page.locator(button("b", "down")).focus()

        page.keyboard.press(key)

        assert values(page) == ["a", "c", "b"]
        expect(page.locator(button("b", "down"))).to_be_focused()


class TestReducedMotion:
    def transitions_during_a_drag(self, page, live_server):
        page.set_default_timeout(5000)
        page.set_viewport_size(VIEWPORT)
        page.goto(f"{live_server.url}/reorder-test/")
        page.wait_for_function("window.Alpine !== undefined")
        x, y = centre(page, handle("a"))
        end = page.locator('#steps [data-mvp-reorder-value="c"]').bounding_box()
        page.mouse.move(x, y)
        page.mouse.down()
        page.mouse.move(x, end["y"] + end["height"] * 0.75, steps=6)
        found = page.eval_on_selector_all(
            "#steps [data-mvp-reorder-row]:not(.mvp-reorder-held)",
            """rows => rows.map(row => [
                getComputedStyle(row).transitionDuration,
                row.style.transition,
            ])""",
        )
        page.mouse.up()
        return found

    def test_reduced_motion_applies_no_transition_to_the_rows(self, page, live_server):
        page.emulate_media(reduced_motion="reduce")

        found = self.transitions_during_a_drag(page, live_server)

        assert {computed for computed, _ in found} == {"0s"}
        assert {inline for _, inline in found} == {""}

    def test_the_rows_slide_when_motion_is_allowed(self, page, live_server):
        page.emulate_media(reduced_motion="no-preference")

        found = self.transitions_during_a_drag(page, live_server)

        assert {inline for _, inline in found} != {""}


class TestFewRows:
    def open_single(self, page, live_server):
        page.set_default_timeout(5000)
        page.set_viewport_size(VIEWPORT)
        page.goto(f"{live_server.url}/reorder-test/single/")
        page.wait_for_function("window.Alpine !== undefined")

    def test_a_list_with_one_row_shows_no_handle_and_no_buttons(
        self, page, live_server
    ):
        self.open_single(page, live_server)

        for hook in ("up", "down", "handle"):
            expect(page.locator(f"#steps [data-mvp-reorder-{hook}]")).to_be_hidden()

    def test_a_list_with_no_rows_has_no_controls(self, page, live_server):
        self.open_single(page, live_server)

        assert page.locator("#empty [data-mvp-reorder-moves]").count() == 0

    def test_the_controls_return_when_a_row_is_added(self, page, live_server):
        self.open_single(page, live_server)

        page.evaluate(TestRowsAddedAfterLoad.APPEND)

        for hook in ("up", "down", "handle"):
            expect(
                page.locator(f"#steps [data-mvp-reorder-{hook}]").first
            ).to_be_visible()

    def test_the_controls_go_when_the_list_is_down_to_one_row(self, page, live_server):
        open_page(page, live_server)

        page.evaluate(
            """() => document.querySelectorAll('#steps [data-mvp-reorder-row]')
                 .forEach((row, index) => { if (index) row.remove(); })"""
        )

        expect(page.locator("#steps [data-mvp-reorder-handle]")).to_be_hidden()
