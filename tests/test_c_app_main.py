"""Tests for <c-app.main> component."""

import pytest


class TestCAppMain:
    """Tests for <c-app.main> component."""

    def test_c_app_main_renders_main_tag_with_correct_classes(self, cotton_render_soup):
        """Test that <c-app.main> renders <main> with app-main and pb-0 classes."""
        soup = cotton_render_soup('app.main')
        main = soup.find('main', class_='app-main')
        assert main is not None
        assert 'pb-0' in main.get('class', [])

    def test_c_app_main_is_main_element(self, cotton_render_soup):
        """Test that the root element is a <main> tag."""
        soup = cotton_render_soup('app.main')
        main = soup.find('main')
        assert main is not None
        assert main.name == 'main'
