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

from demo import urls as demo_urls
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


def form_page(request):
    """Draw the page whose list hands its order to a form."""
    return render_page(FORM_PAGE, request)


def echo(request):
    """Answer with the identifiers the form delivered, in order."""
    return JsonResponse({"order": request.POST.getlist("order")})


def post_page(request, project_id):
    """Draw the page whose list posts its order."""
    project = ProjectFactory._meta.model.objects.get(pk=project_id)
    return render_page(
        POST_PAGE, request, project=project, tasks=project.tasks.all(), answered=""
    )


def save(request, project_id):
    """Store a posted order and answer with the list drawn again."""
    project = ProjectFactory._meta.model.objects.get(pk=project_id)
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
        path("reorder-test/form/", form_page),
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
