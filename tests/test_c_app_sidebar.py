"""Tests for <c-app.sidebar> component."""

import pytest


class TestCAppSidebar:
    """Tests for <c-app.sidebar> component."""

    def test_c_app_sidebar_renders_aside_tag(self, cotton_render_soup):
        """Test that <c-app.sidebar> renders <aside> with app-sidebar class."""
        soup = cotton_render_soup('app.sidebar')
        aside = soup.find('aside', class_='app-sidebar')
        assert aside is not None

    def test_c_app_sidebar_has_shadow_class(self, cotton_render_soup):
        """Test that sidebar has shadow class."""
        soup = cotton_render_soup('app.sidebar')
        aside = soup.find('aside', class_='app-sidebar')
        assert 'shadow' in aside.get('class', [])

    def test_c_app_sidebar_has_data_bs_theme_dark(self, cotton_render_soup):
        """Test that sidebar has data-bs-theme=dark attribute."""
        soup = cotton_render_soup('app.sidebar')
        aside = soup.find('aside', class_='app-sidebar')
        assert aside.get('data-bs-theme') == 'dark'

    def test_c_app_sidebar_renders_header(self, cotton_render_soup):
        """Test that sidebar renders the header component."""
        soup = cotton_render_soup('app.sidebar')
        aside = soup.find('aside', class_='app-sidebar')
        header = aside.find('div', class_='sidebar-brand')
        assert header is not None

    def test_c_app_sidebar_renders_wrapper_nav(self, cotton_render_soup):
        """Test that sidebar renders sidebar-wrapper with nav."""
        soup = cotton_render_soup('app.sidebar')
        wrapper = soup.find('div', class_='sidebar-wrapper')
        assert wrapper is not None
        nav = wrapper.find('nav')
        assert nav is not None

    def test_c_app_sidebar_renders_overlay_div(self, cotton_render_soup):
        """Test that sidebar renders overlay div."""
        soup = cotton_render_soup('app.sidebar')
        overlay = soup.find('div', class_='sidebar-overlay')
        assert overlay is not None
        assert overlay.get('data-lte-toggle') == 'sidebar'
        assert overlay.get('data-lte-dismiss') == 'sidebar-menu'

    def test_c_app_sidebar_renders_app_menu_by_default(self, cotton_render_soup):
        """Test that sidebar renders AppMenu by default."""
        soup = cotton_render_soup('app.sidebar')
        nav = soup.find('nav', class_='mt-2')
        assert nav is not None
        # The nav should contain menu items rendered by AppMenu
        # At minimum, it should have the navigation ID
        ul = nav.find('ul', id='navigation')
        assert ul is not None

    def test_c_app_sidebar_with_custom_brand_text(self, cotton_render_soup):
        """Test that custom brand-text attribute is used."""
        custom_text = "My App"
        soup = cotton_render_soup('app.sidebar', brand_text=custom_text)
        sidebar = soup.find('aside', class_='app-sidebar')
        # The brand text should appear in the header
        assert custom_text in sidebar.get_text()

    def test_c_app_sidebar_with_custom_class(self, cotton_render_soup):
        """Test that custom class attribute is applied to aside."""
        soup = cotton_render_soup('app.sidebar', **{'class': 'custom-sidebar-class'})
        aside = soup.find('aside', class_='app-sidebar')
        assert 'custom-sidebar-class' in aside.get('class', [])
