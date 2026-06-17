"""E2E tests for mobile footer navigation visibility and sidebar toggle.

These tests use pytest-playwright and require a running development server.
They are marked with @pytest.mark.e2e and skipped if playwright is not installed.
"""

import pytest

playwright = pytest.importorskip("playwright")

pytestmark = pytest.mark.e2e


class TestMobileFooterNavVisibility:
    """Playwright E2E tests for mobile footer nav responsive visibility."""

    def test_footer_nav_visible_on_mobile(self, page):
        """Footer nav is visible at mobile viewport (375x812)."""
        page.set_viewport_size({"width": 375, "height": 812})
        page.goto("http://localhost:8001/")
        nav = page.locator("div[aria-label='Mobile navigation']")
        assert nav.is_visible()

    def test_footer_nav_hidden_on_desktop(self, page):
        """Footer nav is hidden at desktop viewport (1280x800)."""
        page.set_viewport_size({"width": 1280, "height": 800})
        page.goto("http://localhost:8001/")
        nav = page.locator("div[aria-label='Mobile navigation']")
        assert not nav.is_visible()

    def test_footer_nav_fixed_during_scroll(self, page):
        """Footer nav remains pinned at bottom after scrolling on mobile."""
        page.set_viewport_size({"width": 375, "height": 812})
        page.goto("http://localhost:8001/")
        page.evaluate("window.scrollBy(0, 500)")
        nav = page.locator("div.dock")
        bounding_box = nav.bounding_box()
        assert bounding_box is not None
        # Nav should still be near the bottom of the viewport
        viewport_height = 812
        assert abs((bounding_box["y"] + bounding_box["height"]) - viewport_height) < 10


class TestMobileFooterNavSidebarToggle:
    """Playwright E2E tests for mobile footer nav sidebar toggle interaction."""

    def test_sidebar_opens_when_toggle_tapped(self, page):
        """Tapping the sidebar toggle in the footer nav opens the sidebar."""
        page.set_viewport_size({"width": 375, "height": 812})
        page.goto("http://localhost:8001/")
        toggle = page.locator("div[aria-label='Mobile navigation'] button")
        toggle.click()
        sidebar = page.locator("aside.mvp-sidebar")
        assert sidebar.is_visible()

    def test_sidebar_closes_when_toggle_tapped_again(self, page):
        """Tapping the sidebar toggle twice closes the sidebar."""
        page.set_viewport_size({"width": 375, "height": 812})
        page.goto("http://localhost:8001/")
        toggle = page.locator("div[aria-label='Mobile navigation'] button")
        toggle.click()
        toggle.click()
        overlay = page.locator(".sidebar-overlay")
        assert not overlay.is_visible()

    def test_default_menu_has_exactly_one_item(self, page):
        """Default MobileFooterMenu has exactly one item (the sidebar toggle)."""
        page.set_viewport_size({"width": 375, "height": 812})
        page.goto("http://localhost:8001/")
        items = page.locator("div[aria-label='Mobile navigation'] nav button.nav-link")
        assert items.count() == 1
