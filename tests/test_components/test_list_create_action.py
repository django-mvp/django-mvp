"""Tests for the <c-page.list.actions.create> component's button sizes (issue #328).

``mvp/templates/cotton/button.html`` declares ``size``, mapped to ``sm``/``md``/``lg``.
It declares neither ``small`` nor ``large``, so a template that passes one of those
gets it forwarded straight through as a bare, invalid HTML attribute, and the button
keeps its default size. This template passed both, on all three of its buttons.
"""


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

    def test_the_modal_trigger_button_is_small(self, cotton_render_soup):
        from demo.forms import ProductForm

        soup = cotton_render_soup(
            "page.list.actions.create",
            context={
                "directory": {"create_url": "/products/create/"},
                "create_form": ProductForm(),
            },
        )
        trigger = soup.find("button", attrs={"@click": "createModal.showModal()"})
        assert trigger is not None
        assert "btn-sm" in trigger.get("class", [])
        assert not trigger.has_attr("small")

    def test_the_modal_submit_button_is_large(self, cotton_render_soup):
        from demo.forms import ProductForm

        soup = cotton_render_soup(
            "page.list.actions.create",
            context={
                "directory": {"create_url": "/products/create/"},
                "create_form": ProductForm(),
            },
        )
        submit = soup.find("button", attrs={"form": "createForm"})
        assert submit is not None
        assert "btn-lg" in submit.get("class", [])
        assert not submit.has_attr("large")

    def test_no_element_carries_a_bare_small_or_large_attribute(
        self, cotton_render_soup
    ):
        from demo.forms import ProductForm

        soup = cotton_render_soup(
            "page.list.actions.create",
            context={
                "directory": {"create_url": "/products/create/"},
                "create_form": ProductForm(),
            },
        )
        for element in soup.find_all():
            assert not element.has_attr("small"), element
            assert not element.has_attr("large"), element
