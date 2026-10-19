"""Tests for ``<c-mvp.modal>``: a dialog laid out as a card.

The component draws its card inside daisy-cotton's ``<c-modal>``, so it holds
no form of its own and works inside one, such as the list page's filter form.

Source: mvp/templates/cotton/mvp/modal.html
"""

import pytest

MODAL = """
<form id="outer" method="get">
  <c-mvp.modal id="demo" title="Pick one" {attrs}>
    <p id="body">The body</p>
    {slots}
  </c-mvp.modal>
</form>
"""


@pytest.fixture
def render_modal(cotton_render_string_soup):
    """Render the modal inside a form, with extra attributes and slots."""

    def render(attrs="", slots=""):
        return cotton_render_string_soup(MODAL.format(attrs=attrs, slots=slots))

    return render


class TestModalInsideAForm:
    def test_the_modal_draws_no_form_of_its_own(self, render_modal):
        soup = render_modal(attrs="closable")

        assert soup.select_one("#outer dialog").find("form") is None

    def test_every_button_that_closes_it_does_not_submit(self, render_modal):
        soup = render_modal(attrs="closable")

        buttons = soup.select("#demo button")
        assert len(buttons) == 2
        assert all(button["type"] == "button" for button in buttons)


class TestModalName:
    def test_the_dialog_is_named_by_its_title(self, render_modal):
        soup = render_modal()

        assert soup.find("dialog")["aria-label"] == "Pick one"

    def test_the_dialog_has_one_heading(self, render_modal):
        soup = render_modal()

        headings = soup.find("dialog").find_all(["h1", "h2", "h3"])
        assert len(headings) == 1
        assert "Pick one" in headings[0].get_text()


class TestModalProps:
    def test_the_dialog_carries_its_id(self, render_modal):
        soup = render_modal()

        assert soup.find("dialog")["id"] == "demo"

    @pytest.mark.parametrize(
        ("size", "width"),
        [("sm", "max-w-md"), ("md", "max-w-2xl"), ("lg", "max-w-4xl")],
    )
    def test_size_sets_the_box_width(self, render_modal, size, width):
        soup = render_modal(attrs=f'size="{size}"')

        assert width in soup.select_one(".modal-box")["class"]

    def test_position_places_the_dialog_and_spans_the_box(self, render_modal):
        soup = render_modal(attrs='position="top"')

        assert "modal-top" in soup.find("dialog")["class"]
        assert "w-full" in soup.select_one(".modal-box")["class"]

    def test_closable_draws_a_close_button_in_the_box(self, render_modal):
        closable = render_modal(attrs="closable")
        plain = render_modal()

        assert closable.select_one(".modal-box button") is not None
        assert plain.select_one(".modal-box button") is None

    def test_class_reaches_the_card(self, render_modal):
        soup = render_modal(attrs='class="extra-card"')

        assert "extra-card" in soup.select_one(".modal-box .card")["class"]


class TestModalSlots:
    def test_the_body_is_drawn_in_the_card(self, render_modal):
        soup = render_modal()

        assert soup.select_one(".modal-box .card #body") is not None

    @pytest.mark.parametrize("slot", ["actions", "footer", "footer_end"])
    def test_each_named_slot_is_drawn_in_the_card(self, render_modal, slot):
        soup = render_modal(slots=f'<c-slot name="{slot}"><b id="slot">x</b></c-slot>')

        assert soup.select_one(".modal-box .card #slot") is not None
