"""Tests for <c-app.sidebar.toggle> component."""

import pytest


class TestCAppSidebarToggle:
    """Tests for <c-app.sidebar.toggle> (hamburger button) component."""

    def test_c_app_sidebar_toggle_renders_nav_item(self, cotton_render_soup):
        """Test that toggle renders <li> with nav-item class."""
        soup = cotton_render_soup('app.sidebar.toggle')
        li = soup.find('li', class_='nav-item')
        assert li is not None

    def test_c_app_sidebar_toggle_renders_link(self, cotton_render_soup):
        """Test that toggle renders <a> with nav-link class."""
        soup = cotton_render_soup('app.sidebar.toggle')
        link = soup.find('a', class_='nav-link')
        assert link is not None

    def test_c_app_sidebar_toggle_has_data_lte_toggle(self, cotton_render_soup):
        """Test that toggle button has data-lte-toggle=sidebar."""
        soup = cotton_render_soup('app.sidebar.toggle')
        link = soup.find('a', class_='nav-link')
        assert link.get('data-lte-toggle') == 'sidebar'

    def test_c_app_sidebar_toggle_has_href_hash(self, cotton_render_soup):
        """Test that toggle button has href=#."""
        soup = cotton_render_soup('app.sidebar.toggle')
        link = soup.find('a', class_='nav-link')
        assert link.get('href') == '#'

    def test_c_app_sidebar_toggle_has_button_role(self, cotton_render_soup):
        """Test that toggle button has role=button."""
        soup = cotton_render_soup('app.sidebar.toggle')
        link = soup.find('a', class_='nav-link')
        assert link.get('role') == 'button'

    def test_c_app_sidebar_toggle_has_icon(self, cotton_render_soup):
        """Test that toggle button contains an icon element."""
        soup = cotton_render_soup('app.sidebar.toggle')
        icon = soup.find('i', class_='bi')
        assert icon is not None
        # Should be the Bootstrap Icons list icon
        assert 'bi-list' in icon.get('class', [])

    def test_c_app_sidebar_toggle_with_custom_class(self, cotton_render_soup):
        """Test that custom class attribute is applied to link."""
        soup = cotton_render_soup('app.sidebar.toggle', **{'class': 'custom-toggle-class'})
        link = soup.find('a', class_='nav-link')
        assert 'custom-toggle-class' in link.get('class', [])
