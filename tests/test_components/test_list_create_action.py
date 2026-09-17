"""Tests for the <c-page.list.actions.create> component.

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
    """The context the modal branch needs: a create URL and an unbound form."""
    return {
        "directory": {"create_url": "/products/create/"},
        "create_form": ProductForm(),
    }


@pytest.fixture
def modal_soup(cotton_render_soup):
    """The modal branch: a create_url and an (unbound) create_form both
    present, which renders the trigger button and its modal's submit."""
    return cotton_render_soup(
        "page.list.actions.create",
        context={
            "directory": {"create_url": "/products/create/"},
            "create_form": ProductForm(),
        },
    )


class TestCreateActionButtonSize:
    """The row is small throughout: the ghost link, the modal trigger, and the
    modal's own submit button keep its authored `large` intent."""

    def test_the_ghost_link_button_is_small(self, cotton_render_soup):
        soup = cotton_render_soup(
            "page.list.actions.create",
            context={"directory": {"create_url": "/products/create/"}},
        )
        button = soup.find("a", class_="btn")
        assert button is not None
        assert "btn-sm" in button.get("class", [])
        assert not button.has_attr("small")

    def test_the_modal_trigger_button_is_small(self, modal_soup):
        trigger = modal_soup.find("button", attrs={"@click": "createModal.showModal()"})
        assert trigger is not None
        assert "btn-sm" in trigger.get("class", [])
        assert not trigger.has_attr("small")

    def test_the_modal_submit_button_is_large(self, modal_soup):
        submit = modal_soup.find("button", attrs={"form": "createForm"})
        assert submit is not None
        assert "btn-lg" in submit.get("class", [])
        assert not submit.has_attr("large")

    def test_no_element_carries_a_bare_small_or_large_attribute(self, modal_soup):
        for element in modal_soup.find_all():
            assert not element.has_attr("small"), element
            assert not element.has_attr("large"), element


class TestCreateActionIcon:
    """``icon`` picks the glyph the action draws, everywhere it draws one."""

    def test_it_defaults_to_the_add_glyph(
        self, cotton_render_string_soup, modal_context
    ):
        soup = cotton_render_string_soup(
            "<c-page.list.actions.create />", context=modal_context
        )

        assert soup.find("i", class_="bi-plus-circle") is not None

    def test_a_caller_chooses_the_glyph(
        self, cotton_render_string_soup, modal_context
    ):
        soup = cotton_render_string_soup(
            '<c-page.list.actions.create icon="upload" />', context=modal_context
        )

        assert soup.find("i", class_="bi-upload") is not None
        assert soup.find("i", class_="bi-plus-circle") is None

    def test_the_glyph_follows_on_the_plain_link_too(
        self, cotton_render_string_soup
    ):
        """The branch without a form draws one button and no modal."""
        soup = cotton_render_string_soup(
            '<c-page.list.actions.create icon="upload" />',
            context={"directory": {"create_url": "/products/create/"}},
        )

        assert soup.find("i", class_="bi-upload") is not None


class TestCreateModalTitle:
    """The modal is headed by the view's resolved title, not the button's."""

    def test_the_view_title_heads_the_modal(
        self, cotton_render_string_soup, modal_context
    ):
        soup = cotton_render_string_soup(
            "<c-page.list.actions.create />",
            context={**modal_context, "create_modal_title": "Add Product"},
        )

        assert "Add Product" in soup.get_text()

    def test_the_button_keeps_its_own_short_label(
        self, cotton_render_string_soup, modal_context
    ):
        """The trigger stays "Add" while the modal names the model."""
        soup = cotton_render_string_soup(
            "<c-page.list.actions.create />",
            context={**modal_context, "create_modal_title": "Add Product"},
        )
        trigger = soup.find("button", attrs={"@click": "createModal.showModal()"})

        assert trigger.get_text(strip=True) == "Add"

    def test_the_label_heads_the_modal_when_no_view_supplies_a_title(
        self, cotton_render_string_soup, modal_context
    ):
        """The component is usable outside ``MVPListViewMixin``, which is the
        only thing that resolves ``create_modal_title``."""
        soup = cotton_render_string_soup(
            '<c-page.list.actions.create label="New" />', context=modal_context
        )

        assert "New" in soup.get_text()
