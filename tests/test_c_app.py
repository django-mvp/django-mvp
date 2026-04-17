"""Tests for <c-app> component."""

import pytest


class TestCAppBasic:
    """Basic rendering tests for <c-app> component."""

    def test_c_app_renders_with_default_attributes(self, cotton_render_soup):
        """Test that <c-app> renders with correct default body classes."""
        soup = cotton_render_soup(
            'app',
            slot='<c-app.main>Test content</c-app.main>'
        )

        body = soup.find('body')
        assert body is not None
        assert 'bg-body-tertiary' in body.get('class', [])
        assert 'sidebar-expand-lg' in body.get('class', [])

    def test_c_app_fixed_sidebar_adds_layout_fixed_class(self, cotton_render_soup):
        """Test that fixed-sidebar attribute adds .layout-fixed to body."""
        soup = cotton_render_soup(
            'app',
            fixed_sidebar=True,
            slot='<c-app.main>Test</c-app.main>'
        )

        body = soup.find('body')
        assert 'layout-fixed' in body.get('class', [])

    def test_c_app_fixed_header_adds_fixed_header_class(self, cotton_render_soup):
        """Test that fixed-header attribute adds .fixed-header to body."""
        soup = cotton_render_soup(
            'app',
            fixed_header=True,
            slot='<c-app.main>Test</c-app.main>'
        )

        body = soup.find('body')
        assert 'fixed-header' in body.get('class', [])

    def test_c_app_fixed_footer_adds_fixed_footer_class(self, cotton_render_soup):
        """Test that fixed-footer attribute adds .fixed-footer to body."""
        soup = cotton_render_soup(
            'app',
            fixed_footer=True,
            slot='<c-app.main>Test</c-app.main>'
        )

        body = soup.find('body')
        assert 'fixed-footer' in body.get('class', [])

    def test_c_app_sidebar_collapsible_adds_sidebar_mini_class(self, cotton_render_soup):
        """Test that sidebar-collapsible attribute adds .sidebar-mini to body."""
        soup = cotton_render_soup(
            'app',
            sidebar_collapsible=True,
            slot='<c-app.main>Test</c-app.main>'
        )

        body = soup.find('body')
        assert 'sidebar-mini' in body.get('class', [])

    def test_c_app_collapsed_adds_sidebar_collapse_class(self, cotton_render_soup):
        """Test that collapsed attribute adds .sidebar-collapse when sidebar-collapsible is set."""
        soup = cotton_render_soup(
            'app',
            sidebar_collapsible=True,
            collapsed=True,
            slot='<c-app.main>Test</c-app.main>'
        )

        body = soup.find('body')
        assert 'sidebar-collapse' in body.get('class', [])

    def test_c_app_collapsed_without_collapsible_has_no_sidebar_collapse(self, cotton_render_soup):
        """Test that collapsed without sidebar-collapsible does NOT add .sidebar-collapse (guard invariant)."""
        soup = cotton_render_soup(
            'app',
            collapsed=True,
            slot='<c-app.main>Test</c-app.main>'
        )

        body = soup.find('body')
        classes = body.get('class', [])
        assert 'sidebar-collapse' not in classes

    def test_c_app_sidebar_expand_accepts_breakpoint_values(self, cotton_render_soup):
        """Test that sidebar-expand attribute maps to correct CSS class."""
        for breakpoint in ['sm', 'md', 'lg', 'xl', 'xxl']:
            soup = cotton_render_soup(
            'app',
                sidebar_expand=breakpoint,
                slot='<c-app.main>Test</c-app.main>'
            )

            body = soup.find('body')
            assert f'sidebar-expand-{breakpoint}' in body.get('class', [])

    def test_c_app_with_fill_attribute_adds_fill_class_to_wrapper(self, cotton_render_soup):
        """Test that fill attribute adds .fill to .app-wrapper."""
        soup = cotton_render_soup(
            'app',
            fill=True,
            slot='<c-app.main>Test</c-app.main>'
        )

        wrapper = soup.find('div', class_='app-wrapper')
        assert wrapper is not None
        assert 'fill' in wrapper.get('class', [])

    def test_c_app_with_custom_class_adds_to_body(self, cotton_render_soup):
        """Test that custom class attribute is added to body."""
        soup = cotton_render_soup(
            'app',
            **{'class': 'custom-class another-class'},
            slot='<c-app.main>Test</c-app.main>'
        )

        body = soup.find('body')
        assert 'custom-class' in body.get('class', [])
        assert 'another-class' in body.get('class', [])

    def test_c_app_combined_attributes(self, cotton_render_soup):
        """Test multiple attributes together."""
        soup = cotton_render_soup(
            'app',
            fixed_sidebar=True,
            fixed_header=True,
            sidebar_collapsible=True,
            sidebar_expand='xl',
            slot='<c-app.main>Test</c-app.main>'
        )

        body = soup.find('body')
        classes = body.get('class', [])
        assert 'bg-body-tertiary' in classes
        assert 'layout-fixed' in classes
        assert 'fixed-header' in classes
        assert 'sidebar-mini' in classes
        assert 'sidebar-expand-xl' in classes

    def test_c_app_renders_app_wrapper_div(self, cotton_render_soup):
        """Test that <c-app> renders a .app-wrapper div."""
        soup = cotton_render_soup(
            'app',
            slot='<c-app.main>Test content</c-app.main>'
        )

        wrapper = soup.find('div', class_='app-wrapper')
        assert wrapper is not None

    def test_c_app_renders_slot_content(self, cotton_render_soup):
        """Test that app-wrapper div is present and can contain slot content."""
        soup = cotton_render_soup(
            'app'
        )

        # Verify the app-wrapper is rendered even with empty slot
        wrapper = soup.find('div', class_='app-wrapper')
        assert wrapper is not None
