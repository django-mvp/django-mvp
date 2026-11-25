"""Tests for the list row: ``<c-mvp.list.row>`` and ``<c-mvp.list.row.action>``.

Rendered-markup tests: what is drawn once, what carries the marks the row's script
reads, and what a developer's own attributes do. Gestures are proved in a browser.

Source: mvp/templates/cotton/mvp/list/row/action.html
"""

import re
from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured

ACTION = '<c-mvp.list.row.action text="Rename" icon="edit" {attrs} />'


@pytest.fixture
def render_action(cotton_render_string_soup):
    def render(attrs=""):
        return cotton_render_string_soup(ACTION.format(attrs=attrs))

    return render


class TestRowAction:
    def test_it_is_a_button_marked_as_a_row_action(self, render_action):
        button = render_action().select_one("button")

        assert button is not None
        assert button.has_attr("data-mvp-row-action")
        assert button["type"] == "button"
        assert not button.has_attr("data-mvp-row-main")
        assert not button.has_attr("data-mvp-row-leaves")

    def test_the_type_prop_sets_the_buttons_type(self, render_action):
        button = render_action('type="submit"').select_one("button")

        assert button["type"] == "submit"

    def test_an_address_makes_it_a_link(self, render_action):
        link = render_action('href="/rename/"').select_one("a")

        assert link["href"] == "/rename/"
        assert link.has_attr("data-mvp-row-action")

    def test_main_and_leaves_are_marked(self, render_action):
        button = render_action("main leaves").select_one("button")

        assert button.has_attr("data-mvp-row-main")
        assert button.has_attr("data-mvp-row-leaves")

    def test_a_label_becomes_the_accessible_name(self, render_action):
        button = render_action('label="Rename Quarterly report"').select_one("button")

        assert button["aria-label"] == "Rename Quarterly report"

    def test_no_label_leaves_the_words_as_the_name(self, render_action):
        assert not render_action().select_one("button").has_attr("aria-label")

    def test_danger_is_passed_to_the_item(self, render_action):
        button = render_action("danger").select_one("button")

        assert button.has_attr("data-mvp-row-danger")
        assert "text-error" in button["class"]

    def test_an_id_and_other_attributes_land_once_on_the_element(self, render_action):
        soup = render_action('id="rename-4" form="f" hx-post="/x/" class="extra"')

        assert len(soup.select("#rename-4")) == 1
        button = soup.select_one("#rename-4")
        assert button["form"] == "f"
        assert button["hx-post"] == "/x/"
        assert "extra" in button["class"]

    def test_the_attrs_prop_reaches_the_element(self, cotton_render_string_soup):
        soup = cotton_render_string_soup(
            '<c-mvp.list.row.action text="Go" :attrs="extra" />',
            {"extra": {"data-probe": "1"}},
        )

        assert soup.select_one("button")["data-probe"] == "1"


ROW = """
<c-mvp.list.row id="{id}" label="Quarterly report" lead="Due Friday" face_class="gap-2"
                class="{cls}">
  <span id="content">Quarterly report</span>
  <c-slot name="actions">{actions}</c-slot>
</c-mvp.list.row>
"""

ACTIONS = """
<c-mvp.list.row.action text="Open" icon="edit" href="/open/" main />
<c-mvp.list.row.action text="Rename" icon="edit" id="rename-4" form="rename-form" />
<c-mvp.list.row.action text="Remove" icon="delete" danger leaves />
"""


@pytest.fixture
def render_row(cotton_render_string_soup):
    def render(actions=ACTIONS, row_id="row-4", cls=""):
        return cotton_render_string_soup(
            ROW.format(id=row_id, actions=actions, cls=cls)
        )

    return render


class TestListRowWithActions:
    def test_every_action_is_in_the_row_once(self, render_row):
        soup = render_row()

        assert len(soup.select("[data-mvp-row-action]")) == 3
        assert len(soup.select("[data-mvp-row-menu]")) == 1
        for text in ("Open", "Rename", "Remove"):
            matches = [
                el
                for el in soup.select("[data-mvp-row-action]")
                if el.get_text(strip=True) == text
            ]
            assert len(matches) == 1

    def test_the_menu_is_a_large_full_width_daisy_menu(self, render_row):
        menu = render_row().select_one("[data-mvp-row-menu]")

        assert menu.name == "ul"
        assert {"menu", "menu-lg", "w-full", "p-0"} <= set(menu["class"])

    def test_the_row_is_a_list_item_that_starts_the_script(self, render_row):
        item = render_row().select_one("li")

        assert item.has_attr("data-mvp-row")
        assert item["x-data"] == "mvpRowActions"
        assert "mvp-row" in item["class"]

    def test_the_item_carries_the_rows_id_once(self, render_row):
        soup = render_row()

        assert soup.select_one("li")["id"] == "row-4"
        assert len(soup.select("#row-4")) == 1

    def test_the_face_holds_the_content_and_the_control(self, render_row):
        face = render_row().select_one(".mvp-row-face")

        assert "list-row" in face["class"]
        assert "gap-2" in face["class"]
        assert face.select_one("#content") is not None
        assert face.select_one(".mvp-row-more") is not None

    def test_the_menu_sits_in_the_dropdown_panel(self, render_row):
        panel = render_row().select_one(".mvp-row-dropdown .dropdown-content")

        assert panel.select_one("[data-mvp-row-menu]") is not None

    def test_the_dropdown_trigger_is_named_for_the_row(self, render_row):
        trigger = render_row().select_one(".mvp-row-dropdown [aria-label]")

        assert trigger["aria-label"] == "More for Quarterly report"

    def test_the_sheet_trigger_opens_the_rows_sheet(self, render_row):
        soup = render_row()

        trigger = soup.select_one(".mvp-row-sheet-trigger")
        assert trigger["data-for"] == "row-4-sheet"
        assert trigger["aria-label"] == "More for Quarterly report"
        assert soup.select_one("dialog#row-4-sheet") is not None

    def test_the_sheet_has_an_empty_body_for_the_menu_to_move_into(self, render_row):
        body = render_row().select_one("dialog [data-mvp-row-sheet-body]")

        assert body is not None
        assert body.get_text(strip=True) == ""
        assert body.select_one("[data-mvp-row-action]") is None

    def test_the_sheet_is_named_by_the_label_with_the_lead(self, render_row):
        soup = render_row()

        assert (
            soup.select_one("#row-4-sheet-title").get_text(strip=True)
            == "Quarterly report"
        )
        assert (
            soup.select_one("[data-mvp-sheet-lead]").get_text(strip=True)
            == "Due Friday"
        )

    def test_an_id_and_a_form_on_an_action_appear_once_in_the_row(self, render_row):
        soup = render_row()

        assert len(soup.select("#rename-4")) == 1
        assert len(soup.select("[form=rename-form]")) == 1

    def test_the_main_action_carries_the_mark(self, render_row):
        marked = render_row().select("[data-mvp-row-main]")

        assert [m.get_text(strip=True) for m in marked] == ["Open"]

    def test_the_leaving_action_carries_the_mark(self, render_row):
        marked = render_row().select("[data-mvp-row-leaves]")

        assert [m.get_text(strip=True) for m in marked] == ["Remove"]

    def test_two_main_actions_raise(self, render_row):
        actions = (
            '<c-mvp.list.row.action text="A" main />'
            '<c-mvp.list.row.action text="B" main />'
        )

        with pytest.raises(ImproperlyConfigured, match="row-4"):
            render_row(actions)

    def test_an_empty_id_raises(self, render_row):
        with pytest.raises(ImproperlyConfigured):
            render_row(row_id="")


class TestListRowWithoutActions:
    def test_it_is_a_plain_row(self, render_row):
        soup = render_row(actions="", cls="extra")

        item = soup.select_one("li")
        assert "list-row" in item["class"]
        assert "extra" in item["class"]
        assert "mvp-row" not in item["class"]
        assert item.select_one("#content") is not None

    def test_it_has_no_menu_control_sheet_or_script(self, render_row):
        soup = render_row(actions="")

        assert soup.select_one("li").has_attr("x-data") is False
        assert soup.select_one("[data-mvp-row]") is None
        assert soup.select_one(".mvp-row-more") is None
        assert soup.select_one("[data-mvp-row-menu]") is None
        assert soup.select_one("dialog") is None

    def test_it_needs_no_id(self, render_row):
        item = render_row(actions="", row_id="").select_one("li")

        assert item is not None
        assert not item.has_attr("id")

    def test_the_item_carries_the_rows_id_once(self, render_row):
        soup = render_row(actions="")

        assert soup.select_one("li")["id"] == "row-4"
        assert len(soup.select("#row-4")) == 1


class TestRowStylesheet:
    """The shipped stylesheet carries the rules the row's script and markup name."""

    STYLESHEET = Path(__file__).parents[2] / "mvp" / "static" / "css" / "django-mvp.css"

    @pytest.fixture
    def css(self):
        return self.STYLESHEET.read_text()

    @pytest.mark.parametrize(
        "selector",
        [
            ".mvp-row-face",
            ".mvp-row-under",
            ".mvp-row-button",
            ".mvp-row-button-neutral",
            ".mvp-row-button-primary",
            ".mvp-row-button-danger",
            ".is-open",
            ".is-dragging",
            ".is-hinting",
            ".is-committing",
            ".is-folded",
            ".is-full",
            "[data-mvp-row-full]",
            ".mvp-row-dropdown",
            ".mvp-row-sheet-trigger",
        ],
    )
    def test_it_styles_what_the_row_draws(self, css, selector):
        assert re.search(re.escape(selector) + r"(?![\w-])", css)

    def test_the_sheet_trigger_replaces_the_dropdown_only_once_the_row_is_set_up(
        self, css
    ):
        coarse = re.findall(r"@media \(pointer: ?coarse\)\{(.*?\})\}", css)
        selectors = [
            selector
            for rules in coarse
            for selector in re.findall(r"([^{}]+)\{[^{}]*\}", rules)
            if "mvp-row-" in selector
        ]

        assert selectors
        assert all("[data-mvp-row-ready]" in selector for selector in selectors)
