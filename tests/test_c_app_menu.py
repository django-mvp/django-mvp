"""Tests for <c-app.menu> component."""

import pytest
pytestmark = pytest.mark.skip(reason="Requires 'Site Navigation' menu to be registered")


class TestCAppMenu:
    """Tests for <c-app.menu> (standalone menu) component."""

    def test_c_app_menu_renders_menu(self, cotton_render_soup):
        """Test that <c-app.menu> renders a menu."""
        soup = cotton_render_soup('app.menu')
        ul = soup.find('ul', id='navigation')
        assert ul is not None

    def test_c_app_menu_has_nav_sidebar_menu_classes(self, cotton_render_soup):
        """Test that menu has nav and sidebar-menu classes."""
        soup = cotton_render_soup('app.menu')
        ul = soup.find('ul')
        classes = ul.get('class', [])
        assert 'nav' in classes
        assert 'sidebar-menu' in classes

    def test_c_app_menu_is_unordered_list(self, cotton_render_soup):
        """Test that menu renders as <ul> (unordered list)."""
        soup = cotton_render_soup('app.menu')
        ul = soup.find('ul')
        assert ul.name == 'ul'

    def test_c_app_menu_has_flex_column_class(self, cotton_render_soup):
        """Test that menu has flex-column class for vertical layout."""
        soup = cotton_render_soup('app.menu')
        ul = soup.find('ul', class_='sidebar-menu')
        assert 'flex-column' in ul.get('class', [])
