"""Tests for <c-app.header> component."""

import pytest


class TestCAppHeader:
    """Tests for <c-app.header> component."""

    def test_c_app_header_renders_nav_with_default_class(self, cotton_render_soup):
        """Test that <c-app.header> renders <nav> with default bg-body class."""
        soup = cotton_render_soup('app.header')
        nav = soup.find('nav', class_='app-header')
        assert nav is not None
        assert 'navbar' in nav.get('class', [])
        assert 'bg-body' in nav.get('class', [])

    def test_c_app_header_renders_navbar_expand_class(self, cotton_render_soup):
        """Test that navbar has navbar-expand class."""
        soup = cotton_render_soup('app.header')
        nav = soup.find('nav', class_='app-header')
        assert 'navbar-expand' in nav.get('class', [])

    def test_c_app_header_with_custom_class(self, cotton_render_soup):
        """Test that custom class attribute is applied to nav."""
        soup = cotton_render_soup('app.header', **{'class': 'custom-nav-class'})
        nav = soup.find('nav', class_='app-header')
        assert 'custom-nav-class' in nav.get('class', [])

    def test_c_app_header_with_border_false(self, cotton_render_soup):
        """Test that border=False adds border-0 class to nav."""
        soup = cotton_render_soup('app.header', border=False)
        nav = soup.find('nav', class_='app-header')
        assert 'border-0' in nav.get('class', [])

    def test_c_app_header_with_border_true(self, cotton_render_soup):
        """Test that border=True (default) does not add border-0."""
        soup = cotton_render_soup('app.header', border=True)
        nav = soup.find('nav', class_='app-header')
        classes = nav.get('class', [])
        assert 'border-0' not in classes

    def test_c_app_header_renders_container_fluid_div(self, cotton_render_soup):
        """Test that header renders container-fluid div."""
        soup = cotton_render_soup('app.header')
        container = soup.find('div', class_='container-fluid')
        assert container is not None

    def test_c_app_header_renders_navbar_nav_list(self, cotton_render_soup):
        """Test that header renders navbar-nav ul."""
        soup = cotton_render_soup('app.header')
        nav_list = soup.find('ul', class_='navbar-nav')
        assert nav_list is not None

    def test_c_app_header_includes_sidebar_toggle(self, cotton_render_soup):
        """Test that header includes sidebar toggle button."""
        soup = cotton_render_soup('app.header')
        # The sidebar toggle should be within the navbar nav
        nav = soup.find('nav', class_='app-header')
        toggle = nav.find('a', **{'data-lte-toggle': 'sidebar'})
        assert toggle is not None

    def test_c_app_header_with_custom_container_class(self, cotton_render_soup):
        """Test that container-class attribute is applied."""
        soup = cotton_render_soup('app.header', container_class='container')
        container = soup.find('div', class_='container')
        assert container is not None
        # fluid container should not be present
        fluid_containers = soup.find_all('div', class_='container-fluid')
        assert len(fluid_containers) == 0

    def test_c_app_header_has_ms_auto_for_right_nav(self, cotton_render_soup):
        """Test that right nav has ms-auto class for right alignment."""
        soup = cotton_render_soup('app.header')
        nav_lists = soup.find_all('ul', class_='navbar-nav')
        assert len(nav_lists) >= 2
        # The second nav list should have ms-auto
        assert 'ms-auto' in nav_lists[1].get('class', [])
