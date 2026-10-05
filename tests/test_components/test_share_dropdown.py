"""Tests for ``<c-mvp.addons.share-dropdown>``.

Source: mvp/templates/cotton/mvp/addons/share_dropdown.html
"""

from mvp.config import MVP_CONFIG


class TestShareDropdownMenu:
    def test_the_menu_has_an_accessible_name(self, cotton_render_string_soup):
        soup = cotton_render_string_soup(
            '<c-mvp.addons.share-dropdown url="https://example.com/page/" />',
            context={"mvp_config": MVP_CONFIG},
        )

        assert soup.select_one("ul.menu")["aria-label"].strip()
