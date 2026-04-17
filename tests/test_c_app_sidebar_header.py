"""Tests for <c-app.sidebar.header> component."""

import pytest


class TestCAppSidebarHeader:
    """Tests for <c-app.sidebar.header> (branding block) component."""

    def test_c_app_sidebar_header_renders_sidebar_brand_div(self, cotton_render_soup):
        """Test that header renders <div class=sidebar-brand>."""
        soup = cotton_render_soup('app.sidebar.header')
        brand_div = soup.find('div', class_='sidebar-brand')
        assert brand_div is not None

    def test_c_app_sidebar_header_renders_brand_link(self, cotton_render_soup):
        """Test that header renders <a> with brand-link class."""
        soup = cotton_render_soup('app.sidebar.header')
        link = soup.find('a', class_='brand-link')
        assert link is not None

    def test_c_app_sidebar_header_link_has_default_href(self, cotton_render_soup):
        """Test that brand link has default href=/."""
        soup = cotton_render_soup('app.sidebar.header')
        link = soup.find('a', class_='brand-link')
        assert link.get('href') == '/'

    def test_c_app_sidebar_header_link_with_custom_link(self, cotton_render_soup):
        """Test that custom link attribute overrides default href."""
        soup = cotton_render_soup('app.sidebar.header', link='/custom-home')
        link = soup.find('a', class_='brand-link')
        assert link.get('href') == '/custom-home'

    def test_c_app_sidebar_header_renders_brand_text(self, cotton_render_soup):
        """Test that header renders brand text in <span>."""
        soup = cotton_render_soup('app.sidebar.header', text='Test App')
        span = soup.find('span', class_='brand-text')
        assert span is not None
        assert 'Test App' in span.get_text()

    def test_c_app_sidebar_header_brand_text_has_fw_light_class(self, cotton_render_soup):
        """Test that brand text has fw-light class."""
        soup = cotton_render_soup('app.sidebar.header', text='Test App')
        span = soup.find('span', class_='brand-text')
        assert 'fw-light' in span.get('class', [])

    def test_c_app_sidebar_header_renders_logo_when_provided(self, cotton_render_soup):
        """Test that logo image is rendered when provided."""
        soup = cotton_render_soup('app.sidebar.header', logo='/path/to/logo.png')
        img = soup.find('img', class_='brand-image-xs')
        assert img is not None
        assert img.get('src') == '/path/to/logo.png'

    def test_c_app_sidebar_header_renders_icon_when_provided(self, cotton_render_soup):
        """Test that icon image is rendered when provided."""
        soup = cotton_render_soup('app.sidebar.header', icon='/path/to/icon.png')
        img = soup.find('img', class_='brand-image-xl')
        assert img is not None
        assert img.get('src') == '/path/to/icon.png'

    def test_c_app_sidebar_header_with_both_logo_and_icon_adds_logo_switch_class(self, cotton_render_soup):
        """Test that logo-switch class is added when both logo and icon provided."""
        soup = cotton_render_soup(
            'app.sidebar.header',
            logo='/path/to/logo.png',
            icon='/path/to/icon.png'
        )
        link = soup.find('a', class_='brand-link')
        assert 'logo-switch' in link.get('class', [])

    def test_c_app_sidebar_header_brand_text_hidden_with_both_logo_and_icon(self, cotton_render_soup):
        """Test that brand text is hidden (d-none) when both logo and icon provided."""
        soup = cotton_render_soup(
            'app.sidebar.header',
            text='Test App',
            logo='/path/to/logo.png',
            icon='/path/to/icon.png'
        )
        span = soup.find('span', class_='brand-text')
        assert 'd-none' in span.get('class', [])

    def test_c_app_sidebar_header_trademark_classes(self, cotton_render_soup):
        """Test that images have correct trademark span classes."""
        soup = cotton_render_soup(
            'app.sidebar.header',
            logo='/logo.png',
            icon='/icon.png'
        )
        # Icon image should have logo-xs
        icon_img = soup.find('img', class_='logo-xs')
        assert icon_img is not None
        # Logo image should have logo-xl
        logo_img = soup.find('img', class_='logo-xl')
        assert logo_img is not None
