"""Tests for ``<c-modal>``: a dialog on daisyUI's own modal box, built from parts.

The header, body and footer sit directly in the box, so the dialog holds no form of
its own and works inside one, such as the list page's filter form. How the parts stack
and scroll is django-mvp-layout's to test: these tests check that the markup carries
the layout's classes and the parts.

Source: mvp/templates/cotton/modal.html
"""

import pytest

MODAL = """
<form id="outer" method="get">
  <c-modal id="demo" {attrs}>
    <c-modal.header title="Pick one" {header}>{actions}</c-modal.header>
    <c-modal.body><p id="body">The body</p></c-modal.body>
    <c-modal.footer>
      <span id="start">Start</span>
      <c-slot name="end"><b id="end">End</b></c-slot>
    </c-modal.footer>
  </c-modal>
</form>
"""


@pytest.fixture
def render_modal(cotton_render_string_soup):
    """Render the modal inside a form, with extra attributes and header content."""

    def render(attrs="", header="", actions=""):
        return cotton_render_string_soup(
            MODAL.format(attrs=attrs, header=header, actions=actions)
        )

    return render


class TestModalInsideAForm:
    def test_the_modal_draws_no_form_of_its_own(self, render_modal):
        soup = render_modal(attrs="closable")

        assert soup.select_one("#outer dialog").find("form") is None

    def test_every_button_that_closes_it_does_not_submit(self, render_modal):
        soup = render_modal(attrs="closable")

        buttons = soup.select("#demo button")
        assert soup.select_one("#demo .mvp-modal-close") is not None
        assert all(button["type"] == "button" for button in buttons)


class TestModalParts:
    def test_the_box_is_stacked_by_the_layout(self, render_modal):
        soup = render_modal()

        assert "hbf" in soup.select_one(".modal-box")["class"]

    def test_each_part_carries_the_layouts_class(self, render_modal):
        soup = render_modal()

        box = soup.select_one(".modal-box")
        assert box.select_one(":scope > .mvpl-header") is not None
        assert box.select_one(":scope > .mvpl-body #body") is not None
        assert box.select_one(":scope > .mvpl-footer") is not None

    def test_the_title_and_icon_head_the_box(self, render_modal):
        soup = render_modal(header='icon="info"')

        heading = soup.select_one(".modal-box h2")
        assert "Pick one" in heading.get_text()
        assert heading.find("i") is not None

    def test_the_dialog_has_one_heading(self, render_modal):
        soup = render_modal()

        headings = soup.find("dialog").find_all(["h1", "h2", "h3"])
        assert len(headings) == 1

    def test_actions_sit_at_the_end_of_the_heading_row(self, render_modal):
        soup = render_modal(
            actions='<c-slot name="actions"><b id="slot">x</b></c-slot>'
        )

        assert soup.select_one(".mvpl-header .mvp-box-end #slot") is not None

    def test_the_footer_has_a_start_group_and_an_end_slot(self, render_modal):
        soup = render_modal()

        footer = soup.select_one(".mvpl-footer")
        assert footer.select_one("#start") is not None
        assert footer.select_one("#end") is not None

    def test_the_body_is_not_drawn_in_the_footer(self, render_modal):
        soup = render_modal()

        assert soup.select_one(".mvpl-footer #body") is None

    def test_a_dialog_with_no_parts_is_not_stacked(self, cotton_render_string_soup):
        soup = cotton_render_string_soup(
            "<c-modal id='bare'><p id='x'>Bare</p></c-modal>"
        )

        assert "hbf" not in soup.select_one(".modal-box")["class"]
        assert soup.select_one(".modal-box #x") is not None


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

    def test_an_empty_size_leaves_the_width_to_content_class(self, render_modal):
        soup = render_modal(attrs='size="" content_class="w-40"')

        classes = soup.select_one(".modal-box")["class"]
        assert "w-40" in classes
        assert not any(name.startswith("max-w-") for name in classes)

    def test_placement_places_the_dialog_and_spans_the_box(self, render_modal):
        soup = render_modal(attrs='placement="top"')

        assert "modal-top" in soup.find("dialog")["class"]
        assert "w-full" in soup.select_one(".modal-box")["class"]

    def test_closable_draws_a_close_button_in_the_box(self, render_modal):
        closable = render_modal(attrs="closable")
        plain = render_modal()

        assert closable.select_one(".modal-box > .mvp-modal-close") is not None
        assert plain.select_one(".modal-box > .mvp-modal-close") is None

    def test_open_renders_the_dialog_shown(self, render_modal):
        soup = render_modal(attrs="open")

        assert soup.find("dialog").has_attr("open")

    def test_content_class_reaches_the_box(self, render_modal):
        soup = render_modal(attrs='content_class="extra-box"')

        assert "extra-box" in soup.select_one(".modal-box")["class"]

    def test_class_reaches_the_dialog(self, render_modal):
        soup = render_modal(attrs='class="extra-dialog"')

        assert "extra-dialog" in soup.find("dialog")["class"]

    def test_the_box_is_the_only_surface(self, render_modal):
        soup = render_modal(attrs="closable")

        assert soup.select_one(".modal-box .card") is None


class TestModalLayout:
    def test_a_view_draws_a_layout_with_the_parts_as_its_header_and_footer(
        self, cotton_render_string_soup
    ):
        soup = cotton_render_string_soup(
            "<c-modal id='m' view='hHh LpR fFf'><c-modal.header title='Settings' />"
            "<c-layout.page>Page</c-layout.page><c-modal.footer>Foot</c-modal.footer>"
            "</c-modal>"
        )

        box = soup.select_one(".modal-box.mvp-box-layout")
        layout = box.select_one(".mvpl")
        assert layout.select_one(".mvpl-header") is not None
        assert layout.select_one(".mvpl-footer") is not None
        assert "Page" in layout.get_text()
