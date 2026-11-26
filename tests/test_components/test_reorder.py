"""Tests for <c-mvp.reorder> and <c-mvp.reorder.row>.

Renders each component through the Cotton compiler, the way a template that
invokes it would, and asserts the hooks the script and a consumer's CSS depend
on. Source: mvp/templates/cotton/mvp/reorder/
"""

import pytest
from bs4 import BeautifulSoup
from django.template import engines
from django.test import RequestFactory
from django_cotton.compiler_regex import CottonCompiler

compiler = CottonCompiler()

LIST = """
<c-mvp.reorder {attrs}>
  <c-mvp.reorder.row value="11" label="Alpha">Alpha</c-mvp.reorder.row>
  <c-mvp.reorder.row value="12" label="Beta">Beta</c-mvp.reorder.row>
</c-mvp.reorder>
"""


def render(attrs="", request=None):
    """Render a two-row list with the given attributes on the list."""
    source = compiler.process(LIST.format(attrs=attrs))
    html = engines["django"].from_string(source).render({}, request)
    return BeautifulSoup(html, "html.parser")


@pytest.mark.django_db
class TestReorderList:
    """The list's root and the hooks its script reads."""

    def test_the_root_carries_the_component_and_the_list_its_rows(self):
        soup = render('id="steps" label="Steps"')

        root = soup.select_one("[data-mvp-reorder]")
        assert root["x-data"] == "mvpReorder"
        assert root["id"] == "steps"
        assert (
            len(root.select("ol[data-mvp-reorder-list] > [data-mvp-reorder-row]")) == 2
        )

    def test_the_list_is_named_by_its_label(self):
        soup = render('id="steps" label="Steps"')

        assert soup.select_one("ol")["aria-label"] == "Steps"

    def test_always_mode_needs_no_id(self):
        soup = render("")

        root = soup.select_one("[data-mvp-reorder]")
        assert root.get("id") is None
        assert root["data-mvp-reorder-mode"] == "always"

    def test_the_mode_and_the_field_name_reach_the_script(self):
        soup = render('id="steps" mode="on-demand" name="steps"')

        root = soup.select_one("[data-mvp-reorder]")
        assert root["data-mvp-reorder-mode"] == "on-demand"
        assert root["data-mvp-reorder-name"] == "steps"

    def test_the_field_name_defaults_to_order(self):
        soup = render("")

        assert soup.select_one("[data-mvp-reorder]")["data-mvp-reorder-name"] == "order"

    def test_a_list_with_no_destination_marks_none(self):
        root = render("").select_one("[data-mvp-reorder]")

        assert root.get("data-mvp-reorder-form") is None
        assert root.get("data-mvp-reorder-url") is None
        assert root.select("input[name=csrfmiddlewaretoken]") == []

    def test_the_form_destination_is_marked(self):
        root = render("form").select_one("[data-mvp-reorder]")

        assert root.has_attr("data-mvp-reorder-form")

    def test_the_url_destination_carries_the_address_and_a_csrf_token(self):
        request = RequestFactory().get("/")

        root = render('id="steps" url="/steps/order/"', request).select_one(
            "[data-mvp-reorder]"
        )

        token = root.select_one("input[name=csrfmiddlewaretoken]")
        assert root["data-mvp-reorder-url"] == "/steps/order/"
        assert token["value"]
        assert token["value"] != "NOTPROVIDED"

    def test_the_list_carries_a_hidden_alert_the_script_shows_on_a_failed_post(self):
        root = render('id="steps" url="/steps/order/"').select_one("[data-mvp-reorder]")

        alert = root.select_one("[data-mvp-reorder-alert]")
        assert alert["role"] == "alert"
        assert alert.has_attr("hidden")

    def test_the_buttons_are_on_unless_hidden(self):
        shown = render("").select_one("[data-mvp-reorder]")
        hidden = render("hide_buttons").select_one("[data-mvp-reorder]")

        assert not shown.has_attr("data-mvp-reorder-hide-buttons")
        assert hidden.has_attr("data-mvp-reorder-hide-buttons")

    def test_extra_attributes_reach_the_root(self):
        root = render('data-probe="x"').select_one("[data-mvp-reorder]")

        assert root["data-probe"] == "x"


@pytest.mark.django_db
class TestReorderRow:
    """One row: its hooks, its controls and their accessible names."""

    def test_a_row_carries_its_value_and_a_hidden_input_holding_it(self):
        rows = render("").select("[data-mvp-reorder-row]")

        assert [row["data-mvp-reorder-value"] for row in rows] == ["11", "12"]
        assert [row.select_one("input[type=hidden]")["value"] for row in rows] == [
            "11",
            "12",
        ]

    def test_the_move_buttons_and_the_handle_are_named_from_the_label(self):
        row = render("").select_one("[data-mvp-reorder-row]")

        up = row.select_one("[data-mvp-reorder-up]")
        down = row.select_one("[data-mvp-reorder-down]")
        handle = row.select_one("[data-mvp-reorder-handle]")
        assert up.name == "button" and "Alpha" in up["aria-label"]
        assert down.name == "button" and "Alpha" in down["aria-label"]
        assert "Alpha" in handle["aria-label"]
        assert up["aria-label"] != down["aria-label"]

    def test_the_controls_are_hidden_until_the_list_is_active(self):
        row = render("").select_one("[data-mvp-reorder-row]")

        for hook in ("up", "down", "handle"):
            assert row.select_one(f"[data-mvp-reorder-{hook}]").has_attr("hidden")

    def test_the_row_carries_the_announcement_the_script_speaks(self):
        row = render("").select_one("[data-mvp-reorder-row]")

        moves = row.select_one("[data-mvp-reorder-moves]")
        assert "{position}" in moves["data-mvp-reorder-moved"]
        assert "{total}" in moves["data-mvp-reorder-moved"]

    def test_the_title_is_the_slot(self):
        row = render("").select_one("[data-mvp-reorder-row]")

        assert "Alpha" in row.get_text()

    def test_a_label_is_escaped(self):
        source = compiler.process(
            '<c-mvp.reorder><c-mvp.reorder.row value="1" label=\'"><b>x</b>\'>t'
            "</c-mvp.reorder.row></c-mvp.reorder>"
        )
        html = engines["django"].from_string(source).render({})

        assert "<b>x</b>" not in html
