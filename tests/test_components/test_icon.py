"""``<c-icon>`` hands every attribute it is given to the icon it renders.

The component's whole body is ``{% icon name defaults=attrs.dict %}``, so a
caller's attributes travel in ``attrs``. It used to declare ``class`` as well,
which read as a promise that the component did something with it — it did not,
and the declaration is gone.

These tests hold the pass-through in place, since nothing else in the package
would notice if a future ``<c-vars>`` line started intercepting an attribute on
its way to the icon.
"""


class TestIconAttributePassThrough:
    def test_a_caller_class_joins_the_icon_classes(self, cotton_render_string_soup):
        soup = cotton_render_string_soup('<c-icon name="add" class="size-6" />')
        rendered = soup.find("i")

        assert "size-6" in rendered["class"]

    def test_any_other_attribute_reaches_the_icon(self, cotton_render_string_soup):
        soup = cotton_render_string_soup('<c-icon name="add" aria-hidden="true" />')

        assert soup.find("i")["aria-hidden"] == "true"


class TestIconAnswersDaisyCottonComponents:
    def test_an_alert_draws_its_icon_through_this_package(
        self, cotton_render_string_soup
    ):
        soup = cotton_render_string_soup("<c-alert variant='success' only>x</c-alert>")

        icon = soup.select_one("[role='alert'] i")
        assert icon is not None
        assert "bi" in icon["class"]
