"""This package's own components render inside daisy-cotton's containers.

Source: mvp/templates/cotton/mvp/
"""


class TestKeptComponentsRenderInsideDaisyCotton:
    def test_an_avatar_renders_inside_the_avatar_group(self, cotton_render_string_soup):
        soup = cotton_render_string_soup(
            '<c-avatar.group><c-mvp.avatar src="/a.png" alt="Ada" /></c-avatar.group>'
        )

        assert soup.select_one(".avatar img[src='/a.png']") is not None
