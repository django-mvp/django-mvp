"""Tests for the <c-page.list.actions.sort> component's button size (issue #328).

The sort trigger rendered at the button's default size while its row neighbours
(filter, create) were meant to be small, leaving the action row visibly mixed.
"""


class TestSortActionButtonSize:
    def test_the_trigger_button_is_small(self, cotton_render_soup):
        soup = cotton_render_soup(
            "page.list.actions.sort",
            context={
                "order_by_choices": [("name", "Name", "-name")],
                "current_ordering": "",
            },
        )
        trigger = soup.find("button")
        assert trigger is not None
        assert "btn-sm" in trigger.get("class", [])

    def test_no_element_carries_a_bare_small_or_large_attribute(
        self, cotton_render_soup
    ):
        soup = cotton_render_soup(
            "page.list.actions.sort",
            context={
                "order_by_choices": [("name", "Name", "-name")],
                "current_ordering": "",
            },
        )
        for element in soup.find_all():
            assert not element.has_attr("small"), element
            assert not element.has_attr("large"), element
