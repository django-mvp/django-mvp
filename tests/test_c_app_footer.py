"""Tests for <c-app.footer> component."""

import pytest


class TestCAppFooter:
    """Tests for <c-app.footer> component."""

    def test_c_app_footer_renders_footer_tag(self, cotton_render_soup):
        """Test that <c-app.footer> renders <footer> tag with app-footer class."""
        soup = cotton_render_soup('app.footer')
        footer = soup.find('footer', class_='app-footer')
        assert footer is not None

    def test_c_app_footer_renders_default_text(self, cotton_render_soup):
        """Test that footer renders default text attribute."""
        soup = cotton_render_soup('app.footer')
        footer = soup.find('footer', class_='app-footer')
        # Default text should be in the footer
        text_content = footer.get_text()
        # The component uses a <strong> tag
        strong = footer.find('strong')
        assert strong is not None

    def test_c_app_footer_with_custom_text(self, cotton_render_soup):
        """Test that custom text attribute appears in footer."""
        custom_text = "Custom Footer Text"
        soup = cotton_render_soup('app.footer', text=custom_text)
        footer = soup.find('footer', class_='app-footer')
        assert custom_text in footer.get_text()

    def test_c_app_footer_with_custom_class(self, cotton_render_soup):
        """Test that custom class attribute is applied to footer."""
        soup = cotton_render_soup('app.footer', **{'class': 'custom-footer-class'})
        footer = soup.find('footer', class_='app-footer')
        assert 'custom-footer-class' in footer.get('class', [])

    def test_c_app_footer_renders_float_end_div_for_right_slot(self, cotton_render_soup):
        """Test that footer renders float-end div for right slot content."""
        soup = cotton_render_soup('app.footer')
        float_div = soup.find('div', class_='float-end')
        assert float_div is not None

    def test_c_app_footer_float_end_has_d_none_d_sm_inline(self, cotton_render_soup):
        """Test that float-end div has responsive classes."""
        soup = cotton_render_soup('app.footer')
        float_div = soup.find('div', class_='float-end')
        classes = float_div.get('class', [])
        assert 'd-none' in classes
        assert 'd-sm-inline' in classes
