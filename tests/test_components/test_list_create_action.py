"""Tests for the <c-mvp.page.list.actions.create> component.

**Button sizes (issue #328).** ``mvp/templates/cotton/button.html`` declares
``size``, mapped to ``sm``/``md``/``lg``. It declares neither ``small`` nor
``large``, so a template that passes one of those gets it forwarded straight
through as a bare, invalid HTML attribute, and the button keeps its default
size. This template passed both, on all three of its buttons.

**Icon and modal title (issue #263).** The component declared an ``icon`` and
then wrote ``icon="add"`` at every point that needed one, so the attribute
could not change anything. The modal's heading, meanwhile, came from the
button's own ``label`` — always the bare word "Add" — while the view had been
resolving a title of "Add <verbose name>" into the context since 021 and
nothing read it.

Icon and title are attribute-driven, so these render through
``cotton_render_string_soup``: rendering the component's template file
directly, as the size tests above do, never triggers Cotton's ``<c-vars>``
handling and every attribute would keep its default.
"""

import pytest

from demo.forms import ProductForm


@pytest.fixture
def modal_context():
    return {
        "directory": {"create_url": "/products/create/"},
        "create_form": ProductForm(),
    }


class TestCreateActionIcon:
    def test_a_caller_chooses_the_glyph(self, cotton_render_string_soup, modal_context):
        soup = cotton_render_string_soup(
            '<c-mvp.page.list.actions.create icon="upload" />', context=modal_context
        )

        assert soup.find("i", class_="bi-upload") is not None
        assert soup.find("i", class_="bi-plus-circle") is None

    def test_the_glyph_follows_on_the_plain_link_too(self, cotton_render_string_soup):
        soup = cotton_render_string_soup(
            '<c-mvp.page.list.actions.create icon="upload" />',
            context={"directory": {"create_url": "/products/create/"}},
        )

        assert soup.find("i", class_="bi-upload") is not None


class TestCreateModalTitle:
    def test_the_view_title_heads_the_modal(
        self, cotton_render_string_soup, modal_context
    ):
        soup = cotton_render_string_soup(
            "<c-mvp.page.list.actions.create />",
            context={**modal_context, "create_modal_title": "Add Product"},
        )

        assert "Add Product" in soup.get_text()

    def test_the_button_keeps_its_own_short_label(
        self, cotton_render_string_soup, modal_context
    ):
        soup = cotton_render_string_soup(
            "<c-mvp.page.list.actions.create />",
            context={**modal_context, "create_modal_title": "Add Product"},
        )
        trigger = soup.find("button", attrs={"@click": "createModal.showModal()"})

        assert trigger.get_text(strip=True) == "Add"

    def test_the_label_heads_the_modal_when_no_view_supplies_a_title(
        self, cotton_render_string_soup, modal_context
    ):
        soup = cotton_render_string_soup(
            '<c-mvp.page.list.actions.create label="New" />', context=modal_context
        )

        assert "New" in soup.get_text()
