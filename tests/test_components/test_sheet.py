"""Tests for the sheet components: ``<c-mvp.sheet>``, its view, trigger and menu.

Rendered-markup tests: roles, names, relationships and the hooks the sheet's
script reads. Placement, height and focus are proved in a real browser.

Source: mvp/templates/cotton/mvp/sheet/index.html
"""

import pytest

SHEET = """
<c-mvp.sheet id="more" title="Orders" {attrs}>
  <p id="body">The body</p>
  {slots}
</c-mvp.sheet>
"""


@pytest.fixture
def render_sheet(cotton_render_string_soup):
    """Render a sheet with extra attributes and slots."""

    def render(attrs="", slots=""):
        return cotton_render_string_soup(SHEET.format(attrs=attrs, slots=slots))

    return render


class TestSheetDialog:
    def test_it_is_a_closed_modal_dialog_named_by_its_title(self, render_sheet):
        soup = render_sheet()

        dialog = soup.select_one("dialog#more")
        assert dialog is not None
        assert dialog.has_attr("open") is False
        assert {"modal", "modal-bottom", "sm:modal-middle"} <= set(dialog["class"])
        title = soup.select_one("#more-title")
        assert dialog["aria-labelledby"] == "more-title"
        assert title.name == "h2"
        assert title.get_text(strip=True) == "Orders"

    def test_the_title_is_drawn_once(self, render_sheet):
        soup = render_sheet()

        assert len(soup.select("dialog h2")) == 1

    def test_the_title_and_the_line_under_it_sit_in_a_div(self, render_sheet):
        soup = render_sheet(attrs='lead="Three open"')

        names = soup.select_one(".mvp-sheet-names")
        assert names.name == "div"
        assert names.select_one("h2") is not None

    def test_a_fixed_sheets_grab_bar_is_not_a_button(self, render_sheet):
        soup = render_sheet(attrs="fixed")

        grab = soup.select_one("[data-mvp-sheet-grab]")
        assert grab.name != "button"
        assert grab["aria-hidden"] == "true"
        assert not grab.has_attr("tabindex")

    def test_the_grab_bar_is_a_button_with_a_name(self, render_sheet):
        soup = render_sheet()

        grab = soup.select_one("[data-mvp-sheet-grab]")
        assert grab.name == "button"
        assert grab["type"] == "button"
        assert grab["aria-label"]

    def test_the_script_hooks_are_present(self, render_sheet):
        soup = render_sheet()

        dialog = soup.select_one("dialog#more")
        assert dialog.has_attr("data-mvp-sheet")
        assert dialog["x-data"] == "mvpSheet"
        assert soup.select_one("dialog [data-mvp-sheet-head]") is not None
        assert soup.select_one("dialog [data-mvp-sheet-body] #body") is not None

    def test_the_body_slot_is_in_the_scrolling_body(self, render_sheet):
        soup = render_sheet()

        assert soup.select_one("#body").find_parent(attrs={"data-mvp-sheet-body": True})


class TestSheetHead:
    def test_lead_and_icon_are_in_the_head(self, render_sheet):
        soup = render_sheet('lead="Order 14" icon="more"')

        head = soup.select_one("[data-mvp-sheet-head]")
        assert head.select_one("[data-mvp-sheet-lead]").get_text(strip=True) == (
            "Order 14"
        )
        assert head.select_one("h2 [aria-hidden=true], h2 ~ * [aria-hidden=true]")

    def test_the_art_slot_is_in_the_head_and_hidden_from_assistive_technology(
        self, render_sheet
    ):
        soup = render_sheet(slots='<c-slot name="art"><img id="cover" alt=""></c-slot>')

        art = soup.select_one("[data-mvp-sheet-head] #cover")
        assert art.find_parent(attrs={"aria-hidden": "true"}) is not None

    def test_no_art_draws_no_art_tile(self, render_sheet):
        soup = render_sheet()

        assert soup.select_one("[data-mvp-sheet-art]") is None

    def test_the_description_slot_describes_the_dialog(self, render_sheet):
        soup = render_sheet(
            slots='<c-slot name="description"><span id="why">Why</span></c-slot>'
        )

        dialog = soup.select_one("dialog#more")
        description = soup.select_one("#more-description")
        assert dialog["aria-describedby"] == "more-description"
        assert description.select_one("#why") is not None

    def test_without_a_description_nothing_describes_the_dialog(self, render_sheet):
        soup = render_sheet()

        assert not soup.select_one("dialog#more").get("aria-describedby")
        assert soup.select_one("#more-description") is None

    def test_without_a_description_the_attribute_is_left_off(self, render_sheet):
        soup = render_sheet()

        assert not soup.select_one("dialog#more").has_attr("aria-describedby")


class TestSheetFoot:
    def test_the_foot_is_empty_without_actions(self, render_sheet):
        soup = render_sheet()

        assert soup.select("[data-mvp-sheet-foot] button") == []

    def test_the_head_holds_an_icon_only_close_button_that_submits_nothing(
        self, render_sheet
    ):
        soup = render_sheet()

        buttons = soup.select("[data-mvp-sheet-head] .mvp-sheet-close")
        assert len(buttons) == 1
        assert buttons[0]["type"] == "button"
        assert buttons[0]["aria-label"] == "Close"
        assert buttons[0].get_text(strip=True) == ""

    def test_the_actions_slot_fills_the_foot(self, render_sheet):
        soup = render_sheet(
            slots='<c-slot name="actions"><button id="save" type="submit">'
            "Save</button></c-slot>"
        )

        foot = soup.select_one("[data-mvp-sheet-foot]")
        assert foot.select_one("#save") is not None
        assert len(foot.select("button")) == 1

    def test_no_closing_control_submits_a_form_around_the_sheet(
        self, cotton_render_string_soup
    ):
        soup = cotton_render_string_soup(
            '<form id="outer" method="post"><c-mvp.sheet id="s" title="T">'
            "x</c-mvp.sheet></form>"
        )

        dialog = soup.select_one("#outer dialog")
        assert dialog.find("form") is None
        for button in dialog.select("button"):
            assert button["type"] == "button"


class TestSheetOptions:
    def test_by_default_none_of_the_options_are_set(self, render_sheet):
        dialog = render_sheet().select_one("dialog#more")

        assert dialog.has_attr("data-mvp-sheet-full") is False
        assert dialog.has_attr("data-mvp-sheet-fixed") is False
        assert "mvp-sheet-wide" not in dialog["class"]

    def test_full_sets_its_data_attribute(self, render_sheet):
        dialog = render_sheet("full").select_one("dialog#more")

        assert dialog.has_attr("data-mvp-sheet-full")
        assert dialog.has_attr("data-mvp-sheet-fixed") is False

    def test_fixed_sets_its_data_attribute(self, render_sheet):
        dialog = render_sheet("fixed").select_one("dialog#more")

        assert dialog.has_attr("data-mvp-sheet-fixed")
        assert dialog.has_attr("data-mvp-sheet-full") is False

    def test_wide_adds_the_wide_size_class(self, render_sheet):
        dialog = render_sheet("wide").select_one("dialog#more")

        assert "mvp-sheet-wide" in dialog["class"]
        assert {"modal-bottom", "sm:modal-middle"} <= set(dialog["class"])


class TestSheetView:
    def test_a_view_is_shown_while_the_sheet_is_on_it(self, render_sheet):
        soup = render_sheet(
            slots='<c-mvp.sheet.view name="confirm"><p id="ask">Sure?</p>'
            "</c-mvp.sheet.view>"
        )

        view = soup.select_one("[data-mvp-sheet-view=confirm]")
        assert view.has_attr("x-show")
        assert "view" in view["x-show"]
        assert view.select_one("#ask") is not None


TRIGGER = (
    '<c-mvp.sheet.trigger for="more" label="Orders" {attrs}>'
    "{slot}</c-mvp.sheet.trigger>"
)


@pytest.fixture
def render_trigger(cotton_render_string_soup):
    """Render a trigger with extra attributes and a slot."""

    def render(attrs="", slot=""):
        return cotton_render_string_soup(TRIGGER.format(attrs=attrs, slot=slot))

    return render


class TestSheetTrigger:
    def test_with_an_address_it_is_a_link_that_announces_a_dialog(self, render_trigger):
        soup = render_trigger('href="/orders/1/"')

        link = soup.select_one("a")
        assert link["href"] == "/orders/1/"
        assert link["aria-haspopup"] == "dialog"
        assert soup.select_one("button") is None

    def test_without_an_address_it_is_a_button(self, render_trigger):
        soup = render_trigger()

        button = soup.select_one("button")
        assert button["type"] == "button"
        assert button["aria-haspopup"] == "dialog"
        assert soup.select_one("a") is None

    def test_the_icon_only_trigger_is_named_for_its_item(self, render_trigger):
        soup = render_trigger()

        button = soup.select_one("button")
        assert "Orders" in button["aria-label"]
        assert button.get_text(strip=True) == ""

    def test_a_worded_trigger_keeps_its_words_and_names_its_item(self, render_trigger):
        soup = render_trigger(slot="Rename")

        button = soup.select_one("button")
        assert "Rename" in button.get_text()
        assert "Orders" in button.get_text()

    def test_it_carries_what_the_script_reads(self, render_trigger):
        soup = render_trigger(
            'href="/x/" view="confirm" returns="back" id="opener"',
        )

        link = soup.select_one("a")
        assert link["data-for"] == "more"
        assert link["data-view"] == "confirm"
        assert link["data-returns"] == "back"
        assert link["id"] == "opener"
        assert link["x-data"] == "mvpSheetTrigger"

    def test_the_icon_is_hidden_from_assistive_technology(self, render_trigger):
        soup = render_trigger()

        assert soup.select_one("button [aria-hidden=true]") is not None


MENU = """
<c-mvp.sheet.menu>
  <c-mvp.sheet.menu.item text="Open" icon="more" href="/open/" />
  <c-mvp.sheet.menu.item text="Rename" icon="more" />
  <c-mvp.sheet.menu.item text="Delete" icon="more" danger />
</c-mvp.sheet.menu>
"""


class TestSheetMenu:
    @pytest.fixture
    def soup(self, cotton_render_string_soup):
        return cotton_render_string_soup(MENU)

    def test_rows_are_a_list(self, soup):
        assert len(soup.select("ul > li")) == 3

    def test_a_row_with_an_address_is_a_link(self, soup):
        link = soup.select_one("li a")

        assert link["href"] == "/open/"
        assert link.get_text(strip=True) == "Open"

    def test_a_row_without_an_address_is_a_button(self, soup):
        buttons = soup.select("li button")

        assert [b.get_text(strip=True) for b in buttons] == ["Rename", "Delete"]
        assert all(b["type"] == "button" for b in buttons)

    def test_each_icon_is_hidden_from_assistive_technology(self, soup):
        icons = soup.select("li [aria-hidden=true]")

        assert len(icons) == 3

    def test_only_the_danger_row_carries_the_destructive_mark(self, soup):
        marked = soup.select("li [data-mvp-sheet-danger]")

        assert [m.get_text(strip=True) for m in marked] == ["Delete"]
