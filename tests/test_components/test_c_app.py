"""Consolidated tests for c-app component family.

This module intentionally groups all `c-app*` component tests together:
- app
- app.header
- app.sidebar
- app.main
- app.footer
- app.sidebar.toggle
- app.sidebar.header
- app.menu
"""

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
        nav = soup.find('nav', class_='app-header')
        toggle = nav.find('a', **{'data-lte-toggle': 'sidebar'})
        assert toggle is not None

    def test_c_app_header_with_custom_container_class(self, cotton_render_soup):
        """Test that container-class attribute is applied."""
        soup = cotton_render_soup('app.header', container_class='container')
        container = soup.find('div', class_='container')
        assert container is not None
        fluid_containers = soup.find_all('div', class_='container-fluid')
        assert len(fluid_containers) == 0

    def test_c_app_header_has_ms_auto_for_right_nav(self, cotton_render_soup):
        """Test that right nav has ms-auto class for right alignment."""
        soup = cotton_render_soup('app.header')
        nav_lists = soup.find_all('ul', class_='navbar-nav')
        assert len(nav_lists) >= 2
        assert 'ms-auto' in nav_lists[1].get('class', [])


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
        ul = nav.find('ul', id='navigation')
        assert ul is not None

    def test_c_app_sidebar_with_custom_brand_text(self, cotton_render_soup):
        """Test that custom brand-text attribute is used."""
        custom_text = "My App"
        soup = cotton_render_soup('app.sidebar', brand_text=custom_text)
        sidebar = soup.find('aside', class_='app-sidebar')
        assert custom_text in sidebar.get_text()

    def test_c_app_sidebar_with_custom_class(self, cotton_render_soup):
        """Test that custom class attribute is applied to aside."""
        soup = cotton_render_soup('app.sidebar', **{'class': 'custom-sidebar-class'})
        aside = soup.find('aside', class_='app-sidebar')
        assert 'custom-sidebar-class' in aside.get('class', [])


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
        _ = footer.get_text()
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
        assert 'bi-list' in icon.get('class', [])

    def test_c_app_sidebar_toggle_with_custom_class(self, cotton_render_soup):
        """Test that custom class attribute is applied to link."""
        soup = cotton_render_soup('app.sidebar.toggle', **{'class': 'custom-toggle-class'})
        link = soup.find('a', class_='nav-link')
        assert 'custom-toggle-class' in link.get('class', [])


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
            icon='/path/to/icon.png',
        )
        link = soup.find('a', class_='brand-link')
        assert 'logo-switch' in link.get('class', [])

    def test_c_app_sidebar_header_brand_text_hidden_with_both_logo_and_icon(self, cotton_render_soup):
        """Test that brand text is hidden (d-none) when both logo and icon provided."""
        soup = cotton_render_soup(
            'app.sidebar.header',
            text='Test App',
            logo='/path/to/logo.png',
            icon='/path/to/icon.png',
        )
        span = soup.find('span', class_='brand-text')
        assert 'd-none' in span.get('class', [])

    def test_c_app_sidebar_header_trademark_classes(self, cotton_render_soup):
        """Test that images have correct trademark span classes."""
        soup = cotton_render_soup('app.sidebar.header', logo='/logo.png', icon='/icon.png')
        icon_img = soup.find('img', class_='logo-xs')
        assert icon_img is not None
        logo_img = soup.find('img', class_='logo-xl')
        assert logo_img is not None


@pytest.mark.skip(reason="Requires 'Site Navigation' menu to be registered")
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
