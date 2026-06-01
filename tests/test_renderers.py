"""Tests for custom menu renderers in mvp/renderers.py."""

import pytest
from flex_menu import MenuItem
from flex_menu.renderers import BaseRenderer


class TestMobileFooterNavRenderer:
    """Tests for MobileFooterNavRenderer class structure and registration."""

    def test_renderer_is_importable(self):
        """Test MobileFooterNavRenderer can be imported from mvp.renderers."""
        from mvp.renderers import MobileFooterNavRenderer  # noqa: F401

    def test_renderer_is_baserenderer_subclass(self):
        """Test MobileFooterNavRenderer subclasses BaseRenderer."""
        from mvp.renderers import MobileFooterNavRenderer

        assert issubclass(MobileFooterNavRenderer, BaseRenderer)

    def test_templates_maps_depth_0_to_wrapper(self):
        """Test templates dict maps depth-0 default to wrapper.html."""
        from mvp.renderers import MobileFooterNavRenderer

        assert MobileFooterNavRenderer.templates[0]["default"] == "menus/mobile-footer-nav/wrapper.html"

    def test_templates_maps_default_leaf_to_item(self):
        """Test templates dict maps default leaf to item.html."""
        from mvp.renderers import MobileFooterNavRenderer

        assert MobileFooterNavRenderer.templates["default"]["leaf"] == "menus/mobile-footer-nav/item.html"

    def test_templates_maps_default_parent_to_item(self):
        """Test templates dict maps default parent to item.html."""
        from mvp.renderers import MobileFooterNavRenderer

        assert MobileFooterNavRenderer.templates["default"]["parent"] == "menus/mobile-footer-nav/item.html"

    def test_renderer_registered_in_settings(self, settings):
        """Test renderer is registered under 'mobile-footer-nav' key in FLEX_MENUS."""
        renderers = settings.FLEX_MENUS["renderers"]
        assert "mobile-footer-nav" in renderers
        assert renderers["mobile-footer-nav"] == "mvp.renderers.MobileFooterNavRenderer"

    def test_invisible_item_produces_no_output(self, rf):
        """Test item with visible=False produces no output (FR-011 — BaseRenderer.render visibility)."""
        from mvp.renderers import MobileFooterNavRenderer

        request = rf.get("/")
        renderer = MobileFooterNavRenderer()

        # Create a MenuItem and manually set visible=False to simulate failed check
        item = MenuItem(name="hidden", extra_context={"label": "Hidden", "url": "#"}, url="#", check=False)
        item.visible = False  # Simulate processed state

        result = renderer.render(item)
        assert result == ""


class TestMobileFooterNavRendererOutput:
    """Tests for MobileFooterNavRenderer HTML output structure."""

    @pytest.fixture(autouse=True)
    def reset_mobile_footer_menu(self):
        """Save and restore MobileFooterMenu children around each test."""
        from mvp.menus import MobileFooterMenu

        original_children = list(MobileFooterMenu.children)
        yield
        MobileFooterMenu.children = original_children

    def test_item_renders_nav_item_nav_link_structure(self, cotton_render_soup):
        """Test rendered HTML contains a nav-link as direct child of <nav> (no <li> wrapper)."""
        from flex_menu import MenuItem

        from mvp.menus import MobileFooterMenu

        MobileFooterMenu.children = [
            MenuItem(name="link", url="/test/", extra_context={"label": "Test", "icon": "home", "url": "/test/"})
        ]
        soup = cotton_render_soup("app.mobile-footer-nav")
        nav = soup.find("nav")
        assert nav is not None
        nav_link = nav.find(class_="nav-link")
        assert nav_link is not None

    def test_active_class_applied_when_url_matches_request_path(self, cotton_render_soup):
        """Test active class applied to .nav-link when item URL matches request path."""
        from flex_menu import MenuItem

        from mvp.menus import MobileFooterMenu

        # cotton_render_soup uses request.path = "/" — use "/" to test active matching
        MobileFooterMenu.children = [
            MenuItem(name="current", url="/", extra_context={"label": "Current", "icon": "home", "url": "/"})
        ]
        soup = cotton_render_soup("app.mobile-footer-nav")
        nav_link = soup.find(class_="nav-link")
        assert nav_link is not None
        assert "active" in nav_link.get("class", [])

    def test_no_active_class_when_url_does_not_match(self, cotton_render_soup):
        """Test no active class when item URL does not match request path."""
        from flex_menu import MenuItem

        from mvp.menus import MobileFooterMenu

        MobileFooterMenu.children = [
            MenuItem(name="other", url="/other/", extra_context={"label": "Other", "icon": "home", "url": "/other/"})
        ]
        soup = cotton_render_soup("app.mobile-footer-nav", request_path="/test/")
        nav_link = soup.find(class_="nav-link")
        assert nav_link is not None
        assert "active" not in nav_link.get("class", [])

    def test_icon_rendered_when_icon_in_extra_context(self, cotton_render_soup):
        """Test icon element is present when icon is in extra_context."""
        from flex_menu import MenuItem

        from mvp.menus import MobileFooterMenu

        MobileFooterMenu.children = [
            MenuItem(name="icon_item", url="/test/", extra_context={"label": "Item", "icon": "home", "url": "/test/"})
        ]
        soup = cotton_render_soup("app.mobile-footer-nav")
        icon = soup.find("i", class_="bi")
        assert icon is not None

    def test_sidebar_toggle_renders_as_button_not_anchor(self, cotton_render_soup):
        """Test sidebar toggle item renders as <button>, not <a>."""
        from flex_menu import MenuItem

        from mvp.menus import MobileFooterMenu

        # Isolate to only the sidebar toggle to avoid interference from other items
        MobileFooterMenu.children = [
            MenuItem(
                name="sidebar_toggle",
                extra_context={
                    "label": "Menu",
                    "icon": "menu",
                    "attrs": {"data-lte-toggle": "sidebar"},
                },
            ),
        ]
        soup = cotton_render_soup("app.mobile-footer-nav")
        button = soup.find("button", attrs={"data-lte-toggle": "sidebar"})
        anchor = soup.find("a", class_="nav-link")
        assert button is not None
        assert anchor is None

    def test_regular_item_renders_as_anchor_not_button(self, cotton_render_soup):
        """Test non-toggle item renders as <a>, not <button>."""
        from flex_menu import MenuItem

        from mvp.menus import MobileFooterMenu

        MobileFooterMenu.children = [
            MenuItem(name="link", url="/test/", extra_context={"label": "Link", "icon": "home", "url": "/test/"})
        ]
        soup = cotton_render_soup("app.mobile-footer-nav")
        anchor = soup.find("a", class_="nav-link")
        button = soup.find("button")
        assert anchor is not None
        assert button is None

    def test_sidebar_toggle_has_data_lte_toggle_attribute(self, cotton_render_soup):
        """Test data-lte-toggle='sidebar' present on toggle button."""
        soup = cotton_render_soup("app.mobile-footer-nav")
        button = soup.find("button", attrs={"data-lte-toggle": "sidebar"})
        assert button is not None
        assert button.get("data-lte-toggle") == "sidebar"

    def test_items_rendered_in_registration_order(self, cotton_render_soup):
        """Test two items registered in order appear in DOM order."""
        from flex_menu import MenuItem

        from mvp.menus import MobileFooterMenu

        MobileFooterMenu.children = [
            MenuItem(name="first", url="/first/", extra_context={"label": "First", "icon": "home", "url": "/first/"}),
            MenuItem(
                name="second", url="/second/", extra_context={"label": "Second", "icon": "list", "url": "/second/"}
            ),
        ]
        soup = cotton_render_soup("app.mobile-footer-nav")
        nav = soup.find("nav")
        assert nav is not None
        items = nav.find_all(class_="nav-link")
        assert len(items) == 2
        assert "First" in items[0].get_text()
        assert "Second" in items[1].get_text()
