"""A formset built with ``can_order``, reordered in a real browser.

Moving a row, adding one, removing one and submitting are all browser
behaviour, so each case loads a test-only page, ``/formset-order-test/``, that
draws a plain three-row formset and answers a valid post with the names in
``ordered_forms`` order.
"""

import pytest
from django import forms
from django.http import HttpResponse, JsonResponse
from django.template import engines
from django.urls import path
from django_cotton.compiler_regex import CottonCompiler
from playwright.sync_api import expect

from demo import urls as demo_urls
from tests.conftest import requires_browser, urlconf_of

pytestmark = [pytest.mark.e2e, requires_browser]

PAGE = """
{% extends "mvp/base.html" %}
{% block content %}
<form id="save" method="post">
  {% csrf_token %}
  <c-mvp.form.formset :formset="formset" layout="{{ layout }}" />
  <button type="submit" id="submit">Save</button>
</form>
{% endblock %}
"""

ROWS = "[data-mvp-reorder-list] > [data-mvp-reorder-row]"


class NameForm(forms.Form):
    """A row with one required field."""

    name = forms.CharField()


OrderedFormSet = forms.formset_factory(NameForm, can_order=True, can_delete=True)


def formset_page(request):
    """Draw the set, or answer a valid post with the names in submitted order."""
    if request.method == "POST":
        formset = OrderedFormSet(request.POST)
        if formset.is_valid():
            return JsonResponse(
                {
                    "names": [
                        form.cleaned_data["name"] for form in formset.ordered_forms
                    ],
                    "total": formset.total_form_count(),
                }
            )
    else:
        formset = OrderedFormSet(initial=[{"name": name} for name in "abc"])
    template = engines["django"].from_string(CottonCompiler().process(PAGE))
    layout = request.GET.get("layout", "stacked")
    return HttpResponse(
        template.render({"formset": formset, "layout": layout}, request)
    )


@pytest.fixture(autouse=True)
def formset_order_urls(settings):
    settings.ROOT_URLCONF = urlconf_of(
        path("formset-order-test/", formset_page),
        *demo_urls.urlpatterns,
    )


def open_page(page, live_server, layout="stacked", width=1280):
    page.set_viewport_size({"width": width, "height": 900})
    page.goto(f"{live_server.url}/formset-order-test/?layout={layout}")
    page.wait_for_function("window.Alpine !== undefined")
    tag_rows(page)


def tag_rows(page):
    """Name each row by its field's value, so a row is found after it has moved."""
    page.eval_on_selector_all(
        ROWS,
        """rows => rows.forEach(row => {
            row.dataset.testName = row.querySelector('input[name$="-name"]').value;
        })""",
    )


def add_row(page, name):
    """Add a row with the add control and fill it in."""
    page.locator('[x-on\\:click="addRow()"]').click()
    row = page.locator(ROWS).last
    row.locator('input[name$="-name"]').fill(name)
    row.evaluate("(row, name) => { row.dataset.testName = name; }", name)


def names(page):
    """The rows' names in document order, removed and blank rows included."""
    return page.eval_on_selector_all(
        ROWS,
        "rows => rows.map(row => row.querySelector('input[name$=\"-name\"]').value)",
    )


def indexes(page):
    """Each row's field name by its value, to show no row was renumbered."""
    return page.eval_on_selector_all(
        ROWS,
        """rows => Object.fromEntries(rows.map(row => {
            const input = row.querySelector('input[name$="-name"]');
            return [input.value, input.name];
        }))""",
    )


def row_of(page, name):
    return page.locator(f'{ROWS}[data-test-name="{name}"]')


def move(page, name, direction):
    row_of(page, name).locator(f"[data-mvp-reorder-{direction}]:visible").click()


def submit(page):
    """Post the form and return the JSON answer of a valid one."""
    with page.expect_navigation():
        page.evaluate("document.getElementById('save').requestSubmit()")
    return page.evaluate("JSON.parse(document.body.innerText)")


def submit_invalid(page):
    """Post the form and wait for the page to come back drawn again."""
    with page.expect_navigation():
        page.evaluate("document.getElementById('save').requestSubmit()")
    page.wait_for_function("window.Alpine !== undefined")


class TestReorderingARowSet:
    def test_rows_moved_with_the_buttons_arrive_in_the_new_order(
        self, page, live_server
    ):
        open_page(page, live_server)

        move(page, "a", "down")
        move(page, "a", "down")

        assert submit(page)["names"] == ["b", "c", "a"]

    def test_an_untouched_blank_row_leaves_the_moved_set_valid(self, page, live_server):
        open_page(page, live_server)

        move(page, "c", "up")

        answer = submit(page)
        assert answer["names"] == ["a", "c", "b"]
        assert answer["total"] == 4

    def test_moving_rows_renumbers_no_row(self, page, live_server):
        open_page(page, live_server)
        before = indexes(page)

        move(page, "a", "down")
        move(page, "c", "up")

        assert indexes(page) == before
        expect(page.locator('input[name="form-TOTAL_FORMS"]')).to_have_value("4")

    def test_a_row_dragged_by_its_handle_moves(self, page, live_server):
        open_page(page, live_server)
        handle = row_of(page, "a").locator("[data-mvp-reorder-handle]")
        box = handle.bounding_box()
        end = row_of(page, "c").bounding_box()
        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        page.mouse.down()
        page.mouse.move(
            box["x"] + box["width"] / 2, end["y"] + end["height"] * 0.75, steps=12
        )
        page.mouse.up()

        assert submit(page)["names"] == ["b", "c", "a"]


class TestAddingAndRemovingRows:
    def test_an_added_row_lands_last_and_moves_like_the_others(self, page, live_server):
        open_page(page, live_server)

        add_row(page, "d")
        assert names(page)[-1] == "d"
        move(page, "d", "up")
        move(page, "d", "up")

        assert submit(page)["names"] == ["a", "b", "d", "c"]

    def test_a_removed_row_is_skipped_by_the_buttons(self, page, live_server):
        open_page(page, live_server)

        row_of(page, "b").locator('[x-on\\:click="remove()"]').first.click()
        move(page, "a", "down")

        expect(row_of(page, "c").locator("[data-mvp-reorder-up]")).to_have_attribute(
            "aria-disabled", "true"
        )
        assert submit(page)["names"] == ["c", "a"]

    def test_a_row_removed_after_a_move_is_left_out(self, page, live_server):
        open_page(page, live_server)

        move(page, "a", "down")
        row_of(page, "c").locator('[x-on\\:click="remove()"]').first.click()

        assert submit(page)["names"] == ["b", "a"]


class TestAnInvalidSubmission:
    def test_rows_come_back_in_the_persons_order_with_every_value(
        self, page, live_server
    ):
        open_page(page, live_server)
        move(page, "a", "down")
        move(page, "a", "down")
        row_of(page, "a").locator('input[name$="-name"]').fill("")

        submit_invalid(page)

        assert names(page)[:3] == ["b", "c", ""]
        page.locator(ROWS).nth(2).locator('input[name$="-name"]').fill("a")
        assert submit(page)["names"] == ["b", "c", "a"]

    def test_a_new_row_the_person_filled_in_keeps_its_place(self, page, live_server):
        open_page(page, live_server)
        add_row(page, "d")
        for _ in range(4):
            move(page, "d", "up")
        row_of(page, "a").locator('input[name$="-name"]').fill("")

        submit_invalid(page)

        assert names(page)[:4] == ["d", "", "b", "c"]
        page.locator(ROWS).nth(1).locator('input[name$="-name"]').fill("a")
        assert submit(page)["names"] == ["d", "a", "b", "c"]


class TestTheTabularLayout:
    def test_the_move_buttons_work_on_a_phone(self, page, live_server):
        open_page(page, live_server, layout="tabular", width=390)

        move(page, "a", "down")

        assert submit(page)["names"] == ["b", "a", "c"]
